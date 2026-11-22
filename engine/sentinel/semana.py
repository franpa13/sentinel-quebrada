"""Los próximos 7 días en cualquier coordenada.

La lluvia sale de la grilla de Open-Meteo. El suelo, si responde, es el último
día válido de NASA POWER. La pendiente es SRTM. El índice es el de siempre:
esta puerta no inventa ráfaga de 30 minutos, así que el fast-trigger no entra.
"""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlencode

from sentinel.lugar import fetch_bytes, fetch_power, fetch_slope, fetch_smn, source
from sentinel.model import LEVELS, Snapshot, ZoneScore, piecewise, score_zone
from sentinel.suelo import apply_reading, fetch_ign, fetch_inta, fetch_saocom
from sentinel.zones import Zone, zones_containing

FORECAST_QUALITY = 0.40
UNKNOWN_TERRAIN = 0.70
SLOPE_KNOTS = ((0.0, 0.25), (8.0, 0.45), (15.0, 0.65), (25.0, 0.85), (35.0, 1.0))
LEVEL_RANK = {name: index for index, name in enumerate(LEVELS)}


def terrain_from_slope(slope_deg: float | None) -> tuple[float, str]:
    if slope_deg is None:
        return UNKNOWN_TERRAIN, "Sin pendiente SRTM la susceptibilidad queda en 0.70 para no bajar el índice."
    value = round(piecewise(slope_deg, SLOPE_KNOTS), 2)
    return value, f"Pendiente local {slope_deg:.2f}° pasa a susceptibilidad {value:.2f}."


def point_zone(name: str, terrain: float) -> Zone:
    return Zone(
        id="punto",
        name=name,
        kind="punto",
        terrain=terrain,
        exposure=0.5,
        path_length_m=0,
        path_slope=0,
        coupling=1,
        svg="",
        label=(0, 0),
        ring=(),
    )


def parse_week(payload: dict) -> list[dict]:
    daily = payload.get("daily") or {}
    dates = daily.get("time") or []
    rains = daily.get("precipitation_sum") or []
    hourly = payload.get("hourly") or {}
    peaks = _hourly_peaks(hourly.get("time") or [], hourly.get("precipitation") or [])
    days = []
    for date, rain in zip(dates, rains):
        if rain is None:
            days.append({"date": date, "rain_mm": None, "intensity_mm_h": None, "missing": True})
            continue
        millimeters = float(rain)
        if date in peaks:
            intensity = peaks[date]
            note = "Máxima hora de la grilla, en mm/h."
        else:
            intensity = millimeters / 24
            note = "Sin horas para ese día: la intensidad es el milimetraje diario dividido 24."
        days.append(
            {
                "date": date,
                "rain_mm": round(millimeters, 2),
                "intensity_mm_h": round(intensity, 3),
                "missing": False,
                "intensity_note": note,
            }
        )
    if len(days) < 7:
        raise ValueError("La grilla no trajo 7 días.")
    return days[:7]


def _hourly_peaks(times: list, values: list) -> dict[str, float]:
    peaks: dict[str, float] = {}
    for stamp, value in zip(times, values):
        if value is None or not stamp:
            continue
        day = str(stamp)[:10]
        peaks[day] = max(peaks.get(day, 0.0), float(value))
    return peaks


def evaluar_semana(days: list[dict], *, soil: float, terrain: float, name: str) -> dict:
    scored = [_score_day(day, soil, terrain, name) for day in days]
    present = [day for day in scored if day["index"] is not None]
    rain_values = [day["rain_mm"] for day in scored if day["rain_mm"] is not None]
    if not present:
        return {
            "from": scored[0]["date"] if scored else None,
            "to": scored[-1]["date"] if scored else None,
            "rain_sum_mm": None,
            "peak_index": None,
            "peak_day": None,
            "level": None,
            "operational_level": "amarillo",
            "headline": "La grilla no trajo milímetros. Sin ese dato no se declara calma.",
            "days": scored,
        }
    peak = max(present, key=lambda day: (day["index"], LEVEL_RANK[day["operational_level"]]))
    worst = max(scored, key=lambda day: LEVEL_RANK[day["operational_level"]])
    return {
        "from": scored[0]["date"],
        "to": scored[-1]["date"],
        "rain_sum_mm": round(sum(rain_values), 2),
        "peak_index": peak["index"],
        "peak_day": peak["date"],
        "level": peak["level"],
        "operational_level": worst["operational_level"],
        "headline": _headline(peak, worst["operational_level"]),
        "days": scored,
    }


def _score_day(day: dict, soil: float, terrain: float, name: str) -> dict:
    base = {
        "date": day["date"],
        "rain_mm": day["rain_mm"],
        "intensity_mm_h": day["intensity_mm_h"],
        "burst_mm_30min": 0,
        "missing": day["missing"],
    }
    if day["missing"] or day["rain_mm"] is None:
        return {
            **base,
            "index": None,
            "level": None,
            "operational_level": "amarillo",
            "confidence": 0.0,
            "confidence_note": "Día sin milímetros en la grilla. No se lee como cero ni como calma.",
            "fast_trigger": False,
            "factors": [],
        }
    snapshot = Snapshot(
        rain_acc_mm=day["rain_mm"],
        intensity_mm_h=day["intensity_mm_h"] or 0,
        burst_mm_30min=0,
        soil_moisture=soil,
        data_age_min=20,
        sensor_quality=FORECAST_QUALITY,
    )
    score = score_zone(snapshot, point_zone(name, terrain), None)
    return {
        **base,
        "index": score.index,
        "level": score.level,
        "operational_level": score.operational_level,
        "confidence": score.confidence,
        "confidence_note": score.confidence_note,
        "fast_trigger": score.fast_trigger,
        "factors": [
            {"id": factor.id, "label": factor.label, "points": factor.points, "detail": factor.detail}
            for factor in score.factors
        ],
    }


def _headline(peak: dict, operational: str) -> str:
    if peak["level"] in ("naranja", "rojo"):
        return (
            f"El {peak['date']} la grilla lleva el índice a {peak['index']:.1f} ({peak['level']}). "
            "No es un pronóstico de alud ni una orden de evacuación."
        )
    if operational == "amarillo" and peak["level"] == "verde":
        return (
            f"El día más alto queda en {peak['index']:.1f}, verde físico, el {peak['date']}. "
            "El operativo es amarillo: una grilla de unos 10 km, sin ráfaga de 30 minutos, no alcanza para declarar calma."
        )
    return (
        f"El {peak['date']} el índice llega a {peak['index']:.1f} ({operational}). "
        "Sale de la lluvia diaria de la grilla y del mismo índice. No es una orden de evacuación."
    )


def fetch_forecast(lat: float, lon: float) -> dict:
    query = urlencode(
        {
            "latitude": lat,
            "longitude": lon,
            "daily": "precipitation_sum",
            "hourly": "precipitation",
            "forecast_days": 7,
            "timezone": "America/Argentina/Jujuy",
        }
    )

    def run() -> dict:
        payload = json.loads(fetch_bytes(f"https://api.open-meteo.com/v1/forecast?{query}", timeout=20))
        days = parse_week(payload)
        return source(
            "open_meteo_semana",
            "Open-Meteo, 7 días",
            "ok",
            f"Grilla diaria del {days[0]['date']} al {days[-1]['date']}.",
            {"days": days},
        )

    try:
        return run()
    except (OSError, TimeoutError, json.JSONDecodeError, KeyError, ValueError, TypeError) as error:
        return source(
            "open_meteo_semana",
            "Open-Meteo, 7 días",
            "error",
            "La grilla de 7 días no respondió.",
            error=f"{type(error).__name__}: {error}",
        )


def consultar_semana(lat: float, lon: float, name: str) -> dict:
    with ThreadPoolExecutor(max_workers=7) as pool:
        forecast, power, slope, smn, inta, ign, saocom = pool.map(
            lambda job: job(),
            (
                lambda: fetch_forecast(lat, lon),
                lambda: fetch_power(lat, lon),
                lambda: fetch_slope(lat, lon),
                lambda: fetch_smn(lat, lon),
                lambda: fetch_inta(lat, lon),
                lambda: fetch_ign(lat, lon),
                lambda: fetch_saocom(lat, lon),
            ),
        )
    power_soil = power["detail"].get("soil") if power["status"] == "ok" else None
    _ignored, soil_detail = _soil_from(power)
    if power_soil is None and power["status"] == "ok":
        power_soil = _ignored
    slope_deg = slope["detail"].get("slope_deg") if slope["status"] == "ok" else None
    slope_terrain, slope_note = terrain_from_slope(slope_deg)
    context = apply_reading(slope_terrain, power_soil, [inta, ign, saocom])
    days = forecast["detail"].get("days") if forecast["status"] == "ok" else []
    week = evaluar_semana(days, soil=context["moisture"], terrain=context["terrain"], name=name) if days else {
        "from": None,
        "to": None,
        "rain_sum_mm": None,
        "peak_index": None,
        "peak_day": None,
        "level": None,
        "operational_level": "amarillo",
        "headline": "Sin la grilla de 7 días no se declara calma.",
        "days": [],
    }
    covered = zones_containing(lat, lon)
    soil_detail["value"] = context["moisture"]
    soil_detail["note"] = context["moisture_note"]
    return {
        "place": {"name": name, "latitude": lat, "longitude": lon},
        "limits": [
            "Esto no pronostica el alud y no es una orden de evacuación.",
            "La lluvia es una grilla de unos 10 km para los próximos 7 días, no un pluviómetro en la quebrada.",
            "La carta de suelos del INTA y la cobertura satelital del IGN pueden subir la susceptibilidad. No la bajan.",
            "SAOCOM puede subir la humedad. Si el píxel no está, no se declara un suelo seco.",
            "La ráfaga de 30 minutos no está en esta grilla: el fast-trigger queda apagado.",
            "El margen en minutos y el dibujo del pueblo solo aplican dentro del esquema de Volcán.",
        ],
        "terrain": {
            "slope_deg": slope_deg,
            "elevation_m": slope["detail"].get("elevation_m") if slope["status"] == "ok" else None,
            "susceptibility": context["terrain"],
            "slope_note": slope_note,
            "note": context["terrain_note"],
        },
        "soil": soil_detail,
        "gis": {
            "inta": context["inta"],
            "cobertura": context["cobertura"],
            "saocom_percent": context["saocom_percent"],
        },
        "week": week,
        "schematic_zones": [zone.id for zone in covered],
        "schematic_note": (
            "El punto cae en el esquema de demo de Volcán. Esos anillos no son cartografía oficial."
            if covered
            else "El esquema de Volcán no cubre este punto. El índice es del punto, no del casco ni de la RN 9."
        ),
        "sources": [forecast, power, slope, smn, inta, ign, saocom],
    }


def _soil_from(power: dict) -> tuple[float, dict]:
    if power["status"] != "ok":
        return 0.45, {
            "value": 0.45,
            "day": None,
            "note": "Sin humedad de POWER se usa 0.45, el piso ya previsto cuando el suelo no llega. No es un suelo medido.",
        }
    detail = power["detail"]
    value = 0.45 if detail.get("soil") is None else float(detail["soil"])
    return value, {"value": value, "day": detail.get("soil_day"), "note": "Humedad de raíz del último día válido de NASA POWER."}


def puntaje_de_punto(snapshot: Snapshot, terrain: float, name: str) -> ZoneScore:
    return score_zone(snapshot, point_zone(name, terrain), None)
