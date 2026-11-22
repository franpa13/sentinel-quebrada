"""API del motor. El panel de Next.js consume estos endpoints."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from sentinel import __version__
from sentinel.lugar import VOLCAN_LAT, VOLCAN_LON, VOLCAN_NAME, leer_lugar
from sentinel.model import Snapshot, ZoneScore, narrative, score_zone
from sentinel.open_meteo import OpenMeteoError, fetch_open_meteo, snapshot_from_hourly
from sentinel.scenarios import SCENARIO_BY_ID, SCENARIOS
from sentinel.semana import consultar_semana, puntaje_de_punto
from sentinel.ruta9 import catalogo, lectura_de_semana
from sentinel.zones import ZONES, zones_containing, zones_geojson

app = FastAPI(
    title="Sentinel Quebrada",
    version=__version__,
    summary="Motor de alerta temprana aluvional para Volcán, Jujuy.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)


class SnapshotIn(BaseModel):
    rain_acc_mm: float = Field(ge=0, le=400, description="Lluvia acumulada 6–24 h, en mm.")
    intensity_mm_h: float = Field(ge=0, le=300)
    burst_mm_30min: float = Field(ge=0, le=200)
    soil_moisture: float = Field(ge=0, le=1)
    data_age_min: float = Field(ge=0, le=20000)
    sensor_quality: float = Field(default=0.95, ge=0, le=1)


class EvaluateIn(BaseModel):
    snapshot: SnapshotIn
    previous_index: dict[str, float] | None = None


def _dump_score(score: ZoneScore) -> dict:
    return {
        "zone_id": score.zone_id,
        "name": score.name,
        "kind": score.kind,
        "index": score.index,
        "level": score.level,
        "operational_level": score.operational_level,
        "confidence": score.confidence,
        "confidence_note": score.confidence_note,
        "reaction_margin_min": score.reaction_margin_min,
        "concentration_min": score.concentration_min,
        "fast_trigger": score.fast_trigger,
        "fast_trigger_reason": score.fast_trigger_reason,
        "exposure": score.exposure,
        "attention": score.attention,
        "svg": score.svg,
        "label": list(score.label),
        "snapshot": {
            "rain_acc_mm": score.snapshot.rain_acc_mm,
            "intensity_mm_h": score.snapshot.intensity_mm_h,
            "burst_mm_30min": score.snapshot.burst_mm_30min,
            "soil_moisture": score.snapshot.soil_moisture,
            "data_age_min": score.snapshot.data_age_min,
            "sensor_quality": score.snapshot.sensor_quality,
        },
        "factors": [
            {"id": factor.id, "label": factor.label, "points": factor.points, "detail": factor.detail}
            for factor in score.factors
        ],
        "modifiers": [
            {
                "id": modifier.id,
                "label": modifier.label,
                "value": modifier.value,
                "factor": modifier.factor,
                "detail": modifier.detail,
            }
            for modifier in score.modifiers
        ],
    }


def _dump_frame(frame, index: int) -> dict:
    return {
        "index": index,
        "label": frame.label,
        "minute": frame.minute,
        "narrative": frame.narrative,
        "zones": [_dump_score(score) for score in frame.zones],
    }


@app.get("/health")
def health() -> dict:
    return {"ok": True, "name": "sentinel-quebrada", "version": __version__}


@app.get("/zones")
def zones() -> dict:
    return {
        "disclaimer": "Esquema de demo para Volcán. No es cartografía oficial ni una orden operativa.",
        "viewBox": "0 0 720 780",
        "zones": [
            {
                "id": zone.id,
                "name": zone.name,
                "kind": zone.kind,
                "terrain": zone.terrain,
                "exposure": zone.exposure,
                "coupling": zone.coupling,
                "svg": zone.svg,
                "label": list(zone.label),
            }
            for zone in ZONES
        ],
    }


@app.get("/zones.geojson")
def geojson() -> dict:
    return zones_geojson()


@app.get("/scenarios")
def list_scenarios() -> dict:
    return {
        "scenarios": [
            {
                "id": scenario.id,
                "title": scenario.title,
                "summary": scenario.summary,
                "demo_hint": scenario.demo_hint,
                "step_minutes": scenario.step_minutes,
                "frame_count": len(scenario.frames),
            }
            for scenario in SCENARIOS
        ]
    }


@app.get("/scenarios/{scenario_id}")
def get_scenario(scenario_id: str) -> dict:
    scenario = SCENARIO_BY_ID.get(scenario_id)
    if scenario is None:
        raise HTTPException(status_code=404, detail="Escenario desconocido.")
    return {
        "id": scenario.id,
        "title": scenario.title,
        "summary": scenario.summary,
        "demo_hint": scenario.demo_hint,
        "step_minutes": scenario.step_minutes,
        "frames": [_dump_frame(frame, index) for index, frame in enumerate(scenario.frames)],
    }


@app.post("/evaluate")
def evaluate(body: EvaluateIn) -> dict:
    snapshot = Snapshot(
        rain_acc_mm=body.snapshot.rain_acc_mm,
        intensity_mm_h=body.snapshot.intensity_mm_h,
        burst_mm_30min=body.snapshot.burst_mm_30min,
        soil_moisture=body.snapshot.soil_moisture,
        data_age_min=body.snapshot.data_age_min,
        sensor_quality=body.snapshot.sensor_quality,
    )
    previous = body.previous_index or {}
    scores = [
        score_zone(snapshot.scaled(zone.coupling), zone, previous.get(zone.id))
        for zone in ZONES
    ]
    return {
        "mode": "pluviometro_cuenca_alta",
        "note": "Las perillas simulan un pluviómetro en la cuenca alta. Aguas abajo el pulso llega atenuado.",
        "narrative": narrative(scores),
        "zones": [_dump_score(score) for score in scores],
    }


def _dump_point(score: ZoneScore) -> dict:
    dumped = _dump_score(score)
    dumped["reaction_margin_min"] = None
    dumped["concentration_min"] = None
    dumped["margin_note"] = "Sin cuenca delineada no hay tiempo de Kirpich. Ese número no se inventa."
    return dumped


@app.get("/consulta")
def consulta_catalog() -> dict:
    return {
        "endpoints": [
            {
                "method": "GET",
                "path": "/consulta/semana",
                "query": {"lat": "obligatorio, grados", "lon": "obligatorio, grados", "nombre": "opcional"},
                "hace": (
                    "Dice si esa coordenada merece atención en los próximos 7 días. "
                    "Cada día pasa por el índice. No asume Volcán."
                ),
            },
            {
                "method": "GET",
                "path": "/context/lugar",
                "query": {"lat": "default Volcán", "lon": "default Volcán", "name": "opcional"},
                "hace": (
                    "Última lectura pública de esa coordenada y su puntaje. "
                    "Las zonas del esquema solo vuelven si el punto cae dentro."
                ),
            },
        ]
    }


@app.get("/consulta/semana")
def consulta_semana(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    nombre: str = "",
) -> dict:
    return consultar_semana(lat, lon, nombre.strip() or "Punto consultado")


@app.get("/ruta9")
def ruta9_home() -> dict:
    return {
        "route": "RN9",
        "focus": "Turismo y excursiones de la Quebrada, y la logística que depende de que la ruta siga abierta.",
        "endpoints": [
            {
                "method": "GET",
                "path": "/ruta9/cortes",
                "hace": "Lista los cortes por lluvia, alud o barro publicados sobre la RN9 de la Quebrada, con fuente.",
            },
            {
                "method": "GET",
                "path": "/ruta9/semana",
                "query": {"lat": "obligatorio", "lon": "obligatorio", "nombre": "opcional"},
                "hace": (
                    "Chance de que esta semana la lluvia corte la RN9 en ese punto. "
                    "Sirve para decidir una excursión o un traslado. No cancela la salida."
                ),
            },
        ],
    }


@app.get("/ruta9/cortes")
def ruta9_cortes() -> dict:
    return catalogo()


@app.get("/ruta9/semana")
def ruta9_semana(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    nombre: str = "",
) -> dict:
    name = nombre.strip() or "Punto de la Quebrada"
    week = consultar_semana(lat, lon, name)
    reading = lectura_de_semana(lat, lon, name, week["week"])
    reading["aluvional"] = {
        "headline": week["week"]["headline"],
        "terrain": week["terrain"],
        "soil": week["soil"],
    }
    return reading


@app.get("/context/lugar")
def lugar_context(
    lat: float = Query(default=VOLCAN_LAT, ge=-90, le=90),
    lon: float = Query(default=VOLCAN_LON, ge=-180, le=180),
    name: str = VOLCAN_NAME,
) -> dict:
    reading = leer_lugar(lat, lon, name)
    snapshot = reading["snapshot"]
    covered = zones_containing(lat, lon)
    if snapshot is None:
        scored = {
            "narrative": "Sin lluvia válida de la grilla no se declara calma.",
            "point": None,
            "zones": [],
            "operational_level": "amarillo",
            "schematic_note": _schematic_note(covered),
        }
    else:
        context = reading["context"]
        point = puntaje_de_punto(snapshot, context["terrain"], name)
        zone_scores = [score_zone(snapshot, zone, None) for zone in covered]
        scored = {
            "narrative": _lugar_narrative(point, covered),
            "point": _dump_point(point),
            "zones": [_dump_score(score) for score in zone_scores],
            "operational_level": point.operational_level,
            "terrain_note": context["terrain_note"],
            "moisture_note": context["moisture_note"],
            "schematic_note": _schematic_note(covered),
        }
    return {
        "place": reading["place"],
        "limits": reading["limits"],
        "snapshot": None
        if snapshot is None
        else {
            "rain_acc_mm": snapshot.rain_acc_mm,
            "intensity_mm_h": snapshot.intensity_mm_h,
            "burst_mm_30min": snapshot.burst_mm_30min,
            "soil_moisture": snapshot.soil_moisture,
            "data_age_min": snapshot.data_age_min,
            "sensor_quality": snapshot.sensor_quality,
        },
        "score": scored,
        "gis": {
            "inta": reading["context"]["inta"],
            "cobertura": reading["context"]["cobertura"],
            "saocom_percent": reading["context"]["saocom_percent"],
        },
        "sources": reading["sources"],
    }


def _schematic_note(covered) -> str:
    if covered:
        return "El punto cae en el esquema de demo de Volcán. Esos anillos no son cartografía oficial."
    return "El esquema de Volcán no cubre este punto. El índice es del punto, no del casco ni de la RN 9."


def _lugar_narrative(point: ZoneScore, covered) -> str:
    opening = f"Punto en {point.operational_level} (índice {point.index:.0f})."
    if not covered:
        return opening + " Fuera del esquema de Volcán: no hay casco ni RN 9 para este lugar."
    names = ", ".join(zone.name for zone in covered)
    return opening + f" Cae en el esquema de demo: {names}."


@app.get("/context/open-meteo")
def open_meteo_context(lat: float = -23.919, lon: float = -65.463) -> dict:
    try:
        payload = fetch_open_meteo(lat, lon)
        snapshot = snapshot_from_hourly(payload)
    except OpenMeteoError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error
    scores = [score_zone(snapshot.scaled(zone.coupling), zone, None) for zone in ZONES]
    return {
        "source": "open-meteo",
        "disclaimer": (
            "Grilla meteorológica de unos 10 km. No ve la quebrada. "
            "La calidad del dato queda en 0.40 para que no se pinte una calma falsa."
        ),
        "latitude": lat,
        "longitude": lon,
        "snapshot": {
            "rain_acc_mm": snapshot.rain_acc_mm,
            "intensity_mm_h": snapshot.intensity_mm_h,
            "burst_mm_30min": snapshot.burst_mm_30min,
            "soil_moisture": snapshot.soil_moisture,
            "data_age_min": snapshot.data_age_min,
            "sensor_quality": snapshot.sensor_quality,
        },
        "narrative": narrative(scores),
        "zones": [_dump_score(score) for score in scores],
    }
