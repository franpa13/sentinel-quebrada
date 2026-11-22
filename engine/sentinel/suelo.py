"""Suelos del INTA, cobertura satelital del IGN y humedad SAOCOM.

Estas capas no reemplazan el índice. Pueden subir la susceptibilidad del
punto o la humedad que ya entra al índice. No la bajan: un mapa viejo o un
píxel seco no se usa para declarar un suelo más inocente.
"""

from __future__ import annotations

import json
from urllib.parse import urlencode

INTA_WFS = "https://geo-backend.inta.gob.ar/geoserver/wfs"
IGN_WMS = "https://imagenes.ign.gob.ar/geoserver/coberturas_del_suelo/ows"
CONAE_WMS = "https://geoservicios3.conae.gov.ar/geoserver/wms"

COVER_CLASSES = {
    1: "Cuerpos de agua",
    2: "Nieve",
    3: "Bosque, selva",
    4: "Estepa arbustiva",
    5: "Tierra para cultivo",
    6: "Afloramiento rocoso",
    7: "Humedal",
    8: "Salina",
    9: "Médano, duna",
    10: "Pastizal",
    11: "Monte",
    12: "Planta urbana",
    13: "Glaciar",
}
# Solo el suelo desnudo suelto o la roca suben la susceptibilidad.
COVER_RAISE = {6: 0.72, 9: 0.78}


def _features(payload: dict) -> list[dict]:
    if not isinstance(payload, dict):
        return []
    return payload.get("features") or []


def parse_inta_national(payload: dict) -> dict | None:
    features = _features(payload)
    if not features:
        return None
    props = features[0].get("properties") or {}
    if not props:
        return None
    return {
        "province": props.get("provincia"),
        "order": props.get("orden_sue1"),
        "subgroup": props.get("sgrup_sue1"),
        "limitation": props.get("limit_ppal"),
        "limitation_2": props.get("limit_secu"),
        "texture": props.get("text_sups1"),
        "drainage": props.get("drenaje_s1"),
        "depth_cm": props.get("profund_s1"),
        "slope_pct": props.get("porc_pens1"),
        "water_erosion": props.get("erhidr_s1"),
        "rock": props.get("rocos_s1"),
        "susceptibility": national_floor(props),
    }


def parse_inta_local(payload: dict) -> dict | None:
    features = _features(payload)
    if not features:
        return None
    props = features[0].get("properties") or {}
    if not props:
        return None
    return {
        "name": props.get("Nombre_Aso"),
        "code": props.get("Nomencla"),
        "landform": props.get("Fisiografi"),
        "relief": props.get("Relieve"),
        "vegetation": props.get("Vegetac"),
        "group": props.get("grupo_tier"),
        "soils": props.get("Suelos_Aso"),
        "susceptibility": local_floor(props),
    }


def national_floor(props: dict) -> float | None:
    floor = None
    limit = str(props.get("limit_ppal") or "").lower()
    erosion = str(props.get("water_erosion") or props.get("erhidr_s1") or "").lower()
    rock = str(props.get("rock") or props.get("rocos_s1") or "").strip().lower()
    if any(token in limit for token in ("pedreg", "rocos", "pendiente", "erosion")):
        floor = _lift(floor, 0.75)
    if any(token in erosion for token in ("moder", "sever", "grave", "fuerte")):
        floor = _lift(floor, 0.80)
    if rock and rock not in {"-", "no", "nula", "ninguna", "none"}:
        floor = _lift(floor, 0.70)
    slope_pct = _number(props.get("slope_pct", props.get("porc_pens1")))
    if slope_pct is not None and slope_pct >= 15:
        floor = _lift(floor, 0.85)
    return floor


def local_floor(props: dict) -> float | None:
    blob = " ".join(
        str(props.get(key) or "")
        for key in ("landform", "Fisiografi", "soils", "Suelos_Aso", "relief", "Relieve", "name", "Nombre_Aso")
    ).lower()
    if any(token in blob for token in ("coluv", "aluvion", "cono de", "abanico", "pedreg")):
        return 0.80
    return None


def parse_cover(payload: dict) -> dict | None:
    features = _features(payload)
    if not features:
        return None
    code = _number((features[0].get("properties") or {}).get("GRAY_INDEX"))
    if code is None:
        return None
    clase = COVER_CLASSES.get(int(code))
    return {
        "code": int(code),
        "clase": clase or f"Código {int(code)} sin nombre en la leyenda del IGN",
        "susceptibility": COVER_RAISE.get(int(code)),
    }


def parse_saocom(payload: dict) -> float | None:
    features = _features(payload)
    if not features:
        return None
    percent = _number((features[0].get("properties") or {}).get("HUMEDAD_DE_SUELO"))
    if percent is None or percent < 0 or percent > 100:
        return None
    return percent


def raise_terrain(slope_terrain: float, national: dict | None, local: dict | None, cover: dict | None) -> tuple[float, str]:
    value = slope_terrain
    reasons = []
    for label, item in (
        ("carta de suelos del INTA", national),
        ("asociación de suelos de Salta y Jujuy", local),
        ("cobertura satelital del IGN", cover),
    ):
        if not item:
            continue
        floor = item.get("susceptibility")
        if floor is None or floor <= value:
            continue
        value = floor
        reasons.append(f"{label} la deja en {floor:.2f}")
    if not reasons:
        return round(slope_terrain, 2), "La carta de suelos y la cobertura no bajan la susceptibilidad que sale de la pendiente."
    return round(value, 2), "Sube la susceptibilidad, no la baja: " + "; ".join(reasons) + "."


def raise_moisture(power: float | None, percent: float | None) -> tuple[float, str]:
    base = 0.45 if power is None else power
    if percent is None:
        if power is None:
            return base, "Sin humedad de POWER ni píxel SAOCOM. Queda 0.45 para no tratar el suelo como seco."
        return base, "Sin píxel SAOCOM en el punto. La humedad queda en la de NASA POWER."
    satellite = round(percent / 100, 3)
    if power is None:
        return satellite, f"Humedad SAOCOM {percent:.0f}%. POWER no tenía un día válido."
    if satellite > power:
        return satellite, (
            f"SAOCOM marca {percent:.0f}% y sube la humedad de {power:.2f} a {satellite:.2f}. "
            "Un píxel más seco no la baja."
        )
    return power, f"SAOCOM marca {percent:.0f}%. No baja la humedad de POWER ({power:.2f})."


def _lift(current: float | None, value: float) -> float:
    if current is None:
        return value
    return max(current, value)


def _number(value) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _wfs(lat: float, lon: float, type_name: str, properties: str) -> dict:
    from sentinel.lugar import fetch_bytes

    params = {
        "service": "WFS",
        "version": "1.0.0",
        "request": "GetFeature",
        "typeName": type_name,
        "outputFormat": "application/json",
        "maxFeatures": "1",
        "propertyName": properties,
        "CQL_FILTER": f"INTERSECTS(the_geom,POINT({lon} {lat}))",
    }
    return json.loads(fetch_bytes(INTA_WFS + "?" + urlencode(params), timeout=25))


def _feature_info(base: str, layer: str, lat: float, lon: float, span: float = 0.02) -> dict:
    from sentinel.lugar import fetch_bytes

    params = {
        "service": "WMS",
        "version": "1.1.1",
        "request": "GetFeatureInfo",
        "layers": layer,
        "query_layers": layer,
        "bbox": f"{lon - span},{lat - span},{lon + span},{lat + span}",
        "width": "101",
        "height": "101",
        "x": "50",
        "y": "50",
        "srs": "EPSG:4326",
        "info_format": "application/json",
        "feature_count": "1",
    }
    return json.loads(fetch_bytes(base + "?" + urlencode(params), timeout=25))


def fetch_inta(lat: float, lon: float) -> dict:
    from sentinel.lugar import _guard, source

    def run() -> dict:
        local = parse_inta_local(
            _wfs(
                lat,
                lon,
                "geonode:asociaciones_suelos_salta_jujuy",
                "Nomencla,Nombre_Aso,Fisiografi,Relieve,Vegetac,grupo_tier,Suelos_Aso",
            )
        )
        national = parse_inta_national(
            _wfs(
                lat,
                lon,
                "geonode:suelos_argentina_1_500",
                "provincia,limit_ppal,limit_secu,orden_sue1,sgrup_sue1,text_sups1,drenaje_s1,profund_s1,porc_pens1,erhidr_s1,rocos_s1",
            )
        )
        if local is None and national is None:
            return source(
                "inta_suelos",
                "INTA GeoINTA, carta de suelos",
                "vacio",
                "El punto no cae en una unidad de la carta de suelos publicada.",
            )
        name = (local or {}).get("name") or (national or {}).get("order") or "unidad de suelos"
        return source(
            "inta_suelos",
            "INTA GeoINTA, carta de suelos",
            "ok",
            f"Unidad {name}. Es el inventario de suelos, no la humedad de hoy.",
            {"local": local, "national": national},
        )

    return _guard("inta_suelos", "INTA GeoINTA, carta de suelos", run)


def fetch_ign(lat: float, lon: float) -> dict:
    from sentinel.lugar import _guard, source

    def run() -> dict:
        cover = parse_cover(_feature_info(IGN_WMS, "cobertura", lat, lon))
        if cover is None:
            return source(
                "ign_cobertura",
                "IGN cobertura del suelo",
                "vacio",
                "El mapa satelital de cobertura no devolvió una clase en el punto.",
            )
        return source(
            "ign_cobertura",
            "IGN cobertura del suelo",
            "ok",
            f"Clase {cover['code']}: {cover['clase']}. Sale de clasificación satelital, no de un relevamiento de la quebrada.",
            cover,
        )

    return _guard("ign_cobertura", "IGN cobertura del suelo", run)


def fetch_saocom(lat: float, lon: float) -> dict:
    from sentinel.lugar import _guard, source

    def run() -> dict:
        for day in (1, 2, 3):
            layer = f"HumedadDeSuelos:DSS_MSMKR_{day}"
            percent = parse_saocom(_feature_info(CONAE_WMS, layer, lat, lon, span=0.08))
            if percent is None:
                continue
            return source(
                "saocom",
                "CONAE SAOCOM, humedad de suelo",
                "ok",
                f"Humedad volumétrica {percent:.0f}% en el perfil hasta 50 cm, mapa del día {day}.",
                {"percent": percent, "layer": layer, "depth": "hasta 50 cm"},
            )
        return source(
            "saocom",
            "CONAE SAOCOM, humedad de suelo",
            "vacio",
            "Los mapas de los últimos días no tienen píxel en este punto. No se inventa un suelo seco.",
        )

    return _guard("saocom", "CONAE SAOCOM, humedad de suelo", run)


def apply_reading(slope_terrain: float, power_soil: float | None, sources: list[dict]) -> dict:
    inta = _detail(sources, "inta_suelos")
    cover = _detail(sources, "ign_cobertura") if _status(sources, "ign_cobertura") == "ok" else None
    percent = None
    if _status(sources, "saocom") == "ok":
        percent = _number((_detail(sources, "saocom") or {}).get("percent"))
    terrain, terrain_note = raise_terrain(
        slope_terrain,
        (inta or {}).get("national"),
        (inta or {}).get("local"),
        cover,
    )
    moisture, moisture_note = raise_moisture(power_soil, percent)
    return {
        "terrain": terrain,
        "terrain_note": terrain_note,
        "moisture": moisture,
        "moisture_note": moisture_note,
        "inta": inta,
        "cobertura": cover,
        "saocom_percent": percent,
    }


def _detail(sources: list[dict], source_id: str) -> dict | None:
    for item in sources:
        if item["id"] == source_id and item["status"] == "ok":
            return item.get("detail") or None
    return None


def _status(sources: list[dict], source_id: str) -> str | None:
    for item in sources:
        if item["id"] == source_id:
            return item["status"]
    return None
