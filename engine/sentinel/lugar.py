"""Lectura real de un punto de la quebrada.

Cada fuente se pide por separado. Si una falla, las otras siguen.
El índice no cambia de fórmula: esta lectura solo arma el Snapshot que el
modelo ya sabe puntuar. La ráfaga de 30 minutos no sale de estas grillas,
así que el fast-trigger no se dispara con esta puerta.
"""

from __future__ import annotations

import json
import math
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from xml.etree import ElementTree

from sentinel.model import Snapshot

VOLCAN_LAT = -23.919
VOLCAN_LON = -65.463
VOLCAN_NAME = "Volcán, Jujuy"
USER_AGENT = "sentinel-quebrada/0.2 (alerta temprana; Volcan, Jujuy)"
POWER_QUALITY = 0.35
MISSING = -900


def fetch_bytes(url: str, timeout: float = 20, data: bytes | None = None, headers: dict | None = None) -> bytes:
    request = Request(
        url,
        data=data,
        headers={"User-Agent": USER_AGENT, "Accept": "application/json, application/xml, */*", **(headers or {})},
    )
    with urlopen(request, timeout=timeout) as response:
        return response.read()


def source(source_id: str, name: str, status: str, summary: str, detail: dict | None = None, error: str | None = None) -> dict:
    return {
        "id": source_id,
        "name": name,
        "status": status,
        "summary": summary,
        "detail": detail or {},
        "error": error,
    }


def _guard(source_id: str, name: str, function) -> dict:
    try:
        return function()
    except (URLError, HTTPError, TimeoutError, json.JSONDecodeError, ElementTree.ParseError, KeyError, ValueError, OSError) as error:
        return source(source_id, name, "error", "La fuente no respondió.", error=f"{type(error).__name__}: {error}")


def valid_series(values: dict) -> list[tuple[str, float]]:
    rows = []
    for day, value in values.items():
        number = float(value)
        if number > MISSING:
            rows.append((day, number))
    return rows


def parse_power(payload: dict) -> dict:
    parameters = payload["properties"]["parameter"]
    rain = valid_series(parameters["PRECTOTCORR"])
    soil = valid_series(parameters["GWETROOT"])
    if not rain:
        raise ValueError("NASA POWER no trae días válidos de precipitación.")
    day, millimeters = rain[-1]
    soil_day, wetness = soil[-1] if soil else (None, None)
    observed = datetime.strptime(day, "%Y%m%d").replace(tzinfo=timezone.utc)
    age_min = max(0.0, (datetime.now(timezone.utc) - observed).total_seconds() / 60)
    return {
        "day": day,
        "rain_mm": round(millimeters, 2),
        "intensity_mm_h": round(millimeters / 24, 3),
        "soil": None if wetness is None else round(max(0.0, min(1.0, wetness)), 3),
        "soil_day": soil_day,
        "age_min": round(age_min, 1),
        "days": [{"day": item[0], "rain_mm": round(item[1], 2)} for item in rain[-7:]],
    }


def snapshot_from_power(parsed: dict) -> Snapshot:
    return Snapshot(
        rain_acc_mm=parsed["rain_mm"],
        intensity_mm_h=parsed["intensity_mm_h"],
        burst_mm_30min=0,
        soil_moisture=0.45 if parsed["soil"] is None else parsed["soil"],
        data_age_min=parsed["age_min"],
        sensor_quality=POWER_QUALITY,
    )


def fetch_power(lat: float, lon: float) -> dict:
    end = datetime.now(timezone.utc).date() - timedelta(days=2)
    start = end - timedelta(days=14)

    def run() -> dict:
        query = urlencode(
            {
                "parameters": "PRECTOTCORR,GWETROOT",
                "community": "AG",
                "longitude": lon,
                "latitude": lat,
                "start": start.strftime("%Y%m%d"),
                "end": end.strftime("%Y%m%d"),
                "format": "JSON",
            }
        )
        payload = json.loads(fetch_bytes(f"https://power.larc.nasa.gov/api/temporal/daily/point?{query}", timeout=40))
        parsed = parse_power(payload)
        soil = "sin humedad" if parsed["soil"] is None else f"humedad de raíz {parsed['soil']}"
        return source(
            "nasa_power",
            "NASA POWER",
            "ok",
            f"Último día válido {parsed['day']}: {parsed['rain_mm']} mm y {soil}.",
            parsed,
        )

    return _guard("nasa_power", "NASA POWER", run)


def distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6_371_000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    chord = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * radius * math.asin(math.sqrt(chord))


def steepest_slope(samples: list[dict]) -> dict:
    marked = [item for item in samples if item.get("role") == "centro"]
    center = marked[0] if marked else samples[0]
    steepest = 0.0
    toward = None
    for sample in samples:
        if sample is center:
            continue
        run = distance_m(center["lat"], center["lon"], sample["lat"], sample["lon"])
        if run < 1:
            continue
        grade = abs(sample["elevation_m"] - center["elevation_m"]) / run
        if grade > steepest:
            steepest = grade
            toward = sample["role"]
    return {
        "elevation_m": center["elevation_m"],
        "slope_m_per_m": round(steepest, 4),
        "slope_deg": round(math.degrees(math.atan(steepest)), 2),
        "steepest_toward": toward,
    }


def fetch_slope(lat: float, lon: float) -> dict:
    def run() -> dict:
        step = 0.01
        points = [
            ("centro", lat, lon),
            ("norte", lat + step, lon),
            ("sur", lat - step, lon),
            ("este", lat, lon + step),
            ("oeste", lat, lon - step),
        ]
        locations = "|".join(f"{point[1]},{point[2]}" for point in points)
        payload = json.loads(fetch_bytes(f"https://api.opentopodata.org/v1/srtm30m?locations={locations}", timeout=25))
        samples = []
        for (role, point_lat, point_lon), result in zip(points, payload["results"]):
            if result.get("elevation") is None:
                continue
            samples.append(
                {"role": role, "lat": point_lat, "lon": point_lon, "elevation_m": float(result["elevation"])}
            )
        if len(samples) < 2:
            raise ValueError("SRTM no devolvió cotas suficientes.")
        parsed = steepest_slope(samples)
        parsed["dataset"] = "SRTM 30 m vía OpenTopoData"
        parsed["note"] = (
            "El IGN no publica una API de pendiente por punto. "
            "El MDE-Ar del IGN también se apoya en SRTM y ALOS, a 30 m."
        )
        return source(
            "srtm_pendiente",
            "Pendiente SRTM 30 m",
            "ok",
            f"Cota {parsed['elevation_m']} m, pendiente local {parsed['slope_deg']}°.",
            parsed,
        )

    return _guard("srtm_pendiente", "Pendiente SRTM 30 m", run)


def closest_station(rows: list[dict], lat: float, lon: float) -> dict | None:
    best = None
    best_distance = None
    for row in rows:
        geom = row.get("geom") or {}
        coordinates = geom.get("coordinates") or []
        if len(coordinates) < 2:
            continue
        station_lon, station_lat = float(coordinates[0]), float(coordinates[1])
        distance = distance_m(lat, lon, station_lat, station_lon)
        name = (row.get("nombre") or "").lower()
        if "volc" in name:
            distance -= 5000
        if best_distance is None or distance < best_distance:
            best = row
            best_distance = distance
    return best


def parse_observations(payload) -> list[dict]:
    rows = payload if isinstance(payload, list) else payload.get("data") or payload.get("rows") or []
    parsed = []
    for row in rows:
        if isinstance(row, dict):
            moment = row.get("timestart") or row.get("fecha") or row.get("date")
            value = row.get("valor") if "valor" in row else row.get("value")
        elif isinstance(row, (list, tuple)) and len(row) >= 2:
            moment, value = row[0], row[1]
        else:
            continue
        if value is None:
            continue
        parsed.append({"time": moment, "value": float(value)})
    return parsed


def fetch_hydro(lat: float, lon: float) -> dict:
    def run() -> dict:
        west, south, east, north = lon - 0.25, lat - 0.35, lon + 0.25, lat + 0.35
        stations = json.loads(
            fetch_bytes(
                "https://alerta.ina.gob.ar/a5/obs/puntual/estaciones?"
                + urlencode({"geom": f"{west},{south},{east},{north}", "limit": 30}),
                timeout=25,
            )
        )
        station = closest_station(stations, lat, lon)
        if station is None:
            return source(
                "ina_hidro",
                "Red hidrológica INA / RHN",
                "vacio",
                "No hay estación pública en la caja de la quebrada.",
            )
        series_payload = json.loads(
            fetch_bytes(
                "https://alerta.ina.gob.ar/a5/obs/puntual/series?" + urlencode({"estacion_id": station["id"]}),
                timeout=25,
            )
        )
        series = series_payload.get("rows") or []
        rain_series = next((item for item in series if (item.get("var") or {}).get("var") == "Pacum"), None)
        observations: list[dict] = []
        if rain_series is not None:
            end = datetime.now(timezone.utc)
            start = end - timedelta(days=21)
            observations = parse_observations(
                json.loads(
                    fetch_bytes(
                        "https://alerta.ina.gob.ar/a5/obs/puntual/series/"
                        f"{rain_series['id']}/observaciones?"
                        + urlencode(
                            {
                                "timestart": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
                                "timeend": end.strftime("%Y-%m-%dT%H:%M:%SZ"),
                            }
                        ),
                        timeout=25,
                    )
                )
            )
        coordinates = station["geom"]["coordinates"]
        detail = {
            "station_id": station["id"],
            "name": station.get("nombre"),
            "network": (station.get("red") or {}).get("nombre"),
            "lon": coordinates[0],
            "lat": coordinates[1],
            "series_id": None if rain_series is None else rain_series["id"],
            "observations": observations[-12:],
            "note": (
                "La red nacional es estadística, no una red de alerta. "
                "La estación provincial en tiempo real no tiene API pública: el nodo de la DPRH Jujuy declara que hoy scrapea el SNIH."
            ),
        }
        if observations:
            last = observations[-1]
            summary = f"{detail['name']}: última acumulada {last['value']} a las {last['time']}."
            status = "ok"
        else:
            summary = f"Estación {detail['name']} encontrada, sin observaciones en los últimos 21 días."
            status = "vacio"
        return source("ina_hidro", "Red hidrológica INA / RHN", status, summary, detail)

    return _guard("ina_hidro", "Red hidrológica INA / RHN", run)


def parse_waterways(payload: dict) -> list[dict]:
    found = []
    for element in payload.get("elements") or []:
        tags = element.get("tags") or {}
        if "waterway" not in tags:
            continue
        found.append({"kind": tags.get("waterway"), "name": tags.get("name")})
    return found


def fetch_osm(lat: float, lon: float) -> dict:
    query = (
        f"[out:json][timeout:12];way[\"waterway\"](around:2500,{lat},{lon});out tags 20;"
    )
    mirrors = (
        "https://overpass-api.de/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter",
    )

    def run() -> dict:
        last_error = "sin intento"
        for mirror in mirrors:
            try:
                payload = json.loads(
                    fetch_bytes(mirror, timeout=18, data=urlencode({"data": query}).encode())
                )
                ways = parse_waterways(payload)
                names = [way["name"] for way in ways if way["name"]]
                summary = f"{len(ways)} cauces en 2,5 km."
                if names:
                    summary += " Con nombre: " + ", ".join(names[:4]) + "."
                return source("openstreetmap", "OpenStreetMap / Overpass", "ok", summary, {"waterways": ways[:20]})
            except (URLError, HTTPError, TimeoutError, json.JSONDecodeError, OSError) as error:
                last_error = f"{type(error).__name__}: {error}"
        raise TimeoutError(last_error)

    return _guard("openstreetmap", "OpenStreetMap / Overpass", run)


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def parse_smn_cap(xml_bytes: bytes, lat: float, lon: float) -> list[dict]:
    root = ElementTree.fromstring(xml_bytes)
    alerts = []
    for info in root.iter():
        if _local(info.tag) != "info":
            continue
        area = ""
        description = ""
        event = ""
        for child in info:
            name = _local(child.tag)
            if name == "area":
                for part in child:
                    if _local(part.tag) == "areaDesc" and part.text:
                        area = part.text
            elif name == "description" and child.text:
                description = child.text
            elif name == "event" and child.text:
                event = child.text
        blob = f"{area} {description} {event}".lower()
        near_quebrada = distance_m(lat, lon, VOLCAN_LAT, VOLCAN_LON) <= 40_000 and any(
            token in blob for token in ("jujuy", "volcán", "volcan", "tumbaya", "humahuaca", "quebrada")
        )
        if near_quebrada or _polygon_contains(info, lat, lon):
            alerts.append({"event": event, "area": area, "description": description[:400]})
    return alerts


def _polygon_contains(info, lat: float, lon: float) -> bool:
    for polygon in info.iter():
        if _local(polygon.tag) != "polygon" or not polygon.text:
            continue
        points = []
        for pair in polygon.text.split():
            bits = pair.split(",")
            if len(bits) != 2:
                continue
            points.append((float(bits[0]), float(bits[1])))
        if len(points) >= 3 and _point_in_ring(lat, lon, points):
            return True
    return False


def _point_in_ring(lat: float, lon: float, ring: list[tuple[float, float]]) -> bool:
    inside = False
    j = len(ring) - 1
    for i, (plat, plon) in enumerate(ring):
        qlat, qlon = ring[j]
        if (plon > lon) != (qlon > lon):
            edge = (qlat - plat) * (lon - plon) / ((qlon - plon) or 1e-12) + plat
            if lat < edge:
                inside = not inside
        j = i
    return inside


def fetch_smn(lat: float, lon: float) -> dict:
    def run() -> dict:
        raw = fetch_bytes("https://ssl.smn.gob.ar/CAP/AR.php", timeout=25)
        alerts = parse_smn_cap(raw, lat, lon)
        if not alerts:
            return source(
                "smn_cap",
                "SMN alertas CAP",
                "vacio",
                "No hay aviso CAP vigente que nombre la quebrada o cubra el punto.",
                {"feed": "https://ssl.smn.gob.ar/CAP/AR.php"},
            )
        return source(
            "smn_cap",
            "SMN alertas CAP",
            "ok",
            f"{len(alerts)} aviso(s) tocan la zona. No cambian el índice: no son un pluviómetro.",
            {"alerts": alerts[:5]},
        )

    return _guard("smn_cap", "SMN alertas CAP", run)


def fetch_modis(lat: float, lon: float) -> dict:
    def run() -> dict:
        dates_payload = json.loads(
            fetch_bytes(
                "https://modis.ornl.gov/rst/api/v1/MOD13Q1/dates?"
                + urlencode({"latitude": lat, "longitude": lon}),
                timeout=30,
            )
        )
        dates = dates_payload.get("dates") or []
        if not dates:
            raise ValueError("MODIS no lista fechas para el punto.")
        last = dates[-1]
        calendar = last.get("calendar_date") or last.get("modis_date")
        modis_date = last.get("modis_date")
        subset = json.loads(
            fetch_bytes(
                "https://modis.ornl.gov/rst/api/v1/MOD13Q1/subset?"
                + urlencode(
                    {
                        "latitude": lat,
                        "longitude": lon,
                        "startDate": modis_date,
                        "endDate": modis_date,
                        "band": "250m_16_days_NDVI",
                        "kmAboveBelow": 0,
                        "kmLeftRight": 0,
                    }
                ),
                timeout=30,
            )
        )
        ndvi = _mean_ndvi(subset)
        return source(
            "modis_ndvi",
            "MODIS NDVI (ORNL)",
            "ok",
            f"NDVI 16 días {calendar}: {ndvi}.",
            {"date": calendar, "modis_date": modis_date, "ndvi": ndvi, "product": "MOD13Q1"},
        )

    return _guard("modis_ndvi", "MODIS NDVI (ORNL)", run)


def _mean_ndvi(payload: dict) -> float | None:
    subsets = payload.get("subset") or payload.get("data") or []
    values = []
    for item in subsets:
        raw = item.get("data") if isinstance(item, dict) else None
        if not raw:
            continue
        for piece in raw:
            number = float(piece)
            if number > -9000:
                values.append(number / 10000 if abs(number) > 2 else number)
    if not values:
        return None
    return round(sum(values) / len(values), 3)


def fetch_sentinel(lat: float, lon: float) -> dict:
    def run() -> dict:
        end = datetime.now(timezone.utc)
        start = end - timedelta(days=40)
        body = json.dumps(
            {
                "collections": ["sentinel-2-l2a"],
                "intersects": {"type": "Point", "coordinates": [lon, lat]},
                "datetime": f"{start.strftime('%Y-%m-%dT%H:%M:%SZ')}/{end.strftime('%Y-%m-%dT%H:%M:%SZ')}",
                "limit": 1,
                "sortby": [{"field": "properties.datetime", "direction": "desc"}],
            }
        ).encode()
        payload = json.loads(
            fetch_bytes(
                "https://planetarycomputer.microsoft.com/api/stac/v1/search",
                timeout=25,
                data=body,
                headers={"Content-Type": "application/json"},
            )
        )
        features = payload.get("features") or []
        if not features:
            return source(
                "sentinel2",
                "Sentinel-2 (Planetary Computer)",
                "vacio",
                "No hay escena L2A en los últimos 40 días.",
            )
        properties = features[0].get("properties") or {}
        when = properties.get("datetime")
        cloud = properties.get("eo:cloud_cover")
        return source(
            "sentinel2",
            "Sentinel-2 (Planetary Computer)",
            "ok",
            f"Última escena {when}, nubes {cloud}%. No se calculó NDVI píxel a píxel.",
            {"datetime": when, "cloud_cover": cloud, "id": features[0].get("id")},
        )

    return _guard("sentinel2", "Sentinel-2 (Planetary Computer)", run)


def unavailable_sources() -> list[dict]:
    return [
        source(
            "gpm_imerg",
            "NASA GPM/IMERG",
            "no_conectado",
            "El granulo de IMERG cada 30 minutos pide cuenta Earthdata. La lluvia de esta lectura es PRECTOTCORR de NASA POWER, el producto abierto corregido con satélite y pluviómetros.",
        ),
        source(
            "google_earth_engine",
            "Google Earth Engine",
            "no_conectado",
            "Pedir NDVI por Earth Engine exige una cuenta y un proyecto. La cobertura satelital de esta lectura sale del mapa del IGN y, si responde, del NDVI MODIS de ORNL.",
        ),
    ]


def leer_lugar(lat: float = VOLCAN_LAT, lon: float = VOLCAN_LON, name: str = VOLCAN_NAME) -> dict:
    from sentinel.semana import terrain_from_slope
    from sentinel.suelo import apply_reading, fetch_ign, fetch_inta, fetch_saocom

    jobs = (
        lambda: fetch_power(lat, lon),
        lambda: fetch_slope(lat, lon),
        lambda: fetch_hydro(lat, lon),
        lambda: fetch_osm(lat, lon),
        lambda: fetch_smn(lat, lon),
        lambda: fetch_modis(lat, lon),
        lambda: fetch_sentinel(lat, lon),
        lambda: fetch_inta(lat, lon),
        lambda: fetch_ign(lat, lon),
        lambda: fetch_saocom(lat, lon),
    )
    sources: list[dict] = []
    with ThreadPoolExecutor(max_workers=len(jobs)) as pool:
        for item in pool.map(lambda job: job(), jobs):
            sources.append(item)
    sources.extend(unavailable_sources())
    power = next(item for item in sources if item["id"] == "nasa_power")
    slope = next(item for item in sources if item["id"] == "srtm_pendiente")
    snapshot = snapshot_from_power(power["detail"]) if power["status"] == "ok" else None
    slope_deg = slope["detail"].get("slope_deg") if slope["status"] == "ok" else None
    slope_terrain, _slope_note = terrain_from_slope(slope_deg)
    context = apply_reading(slope_terrain, None if snapshot is None else snapshot.soil_moisture, sources)
    if snapshot is not None:
        snapshot = Snapshot(
            rain_acc_mm=snapshot.rain_acc_mm,
            intensity_mm_h=snapshot.intensity_mm_h,
            burst_mm_30min=snapshot.burst_mm_30min,
            soil_moisture=context["moisture"],
            data_age_min=snapshot.data_age_min,
            sensor_quality=snapshot.sensor_quality,
        )
    return {
        "place": {"name": name, "latitude": lat, "longitude": lon},
        "snapshot": snapshot,
        "context": context,
        "sources": sources,
        "limits": [
            "Esto no pronostica el alud. Cruza la última lluvia y humedad con el índice que ya existe.",
            "Sin ráfaga de 30 minutos el fast-trigger queda apagado, aunque el día haya llovido.",
            "La carta de suelos del INTA y la cobertura del IGN pueden subir la susceptibilidad. No la bajan.",
            "SAOCOM puede subir la humedad. Un píxel ausente o más seco no se lee como suelo seco.",
            "El puntaje es de esta coordenada. Las zonas del esquema de Volcán solo entran si el punto cae dentro.",
        ],
    }
