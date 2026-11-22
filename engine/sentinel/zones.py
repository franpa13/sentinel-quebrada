"""Zonas esquemáticas de Volcán.

No es cartografía oficial ni un catastro. Las geometrías alcanzan para la demo:
microcuenca, cauce, cono, casco, accesos y RN 9. `coupling` solo se usa en el
modo perillas, cuando hay un único pluviómetro imaginado en la cuenca alta.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Zone:
    id: str
    name: str
    kind: str
    terrain: float
    exposure: float
    path_length_m: float
    path_slope: float
    coupling: float
    svg: str
    label: tuple[float, float]
    # Anillos [lon, lat]. Esquema alrededor de Volcán, no un relevamiento.
    ring: tuple[tuple[float, float], ...]


ZONES: tuple[Zone, ...] = (
    Zone(
        id="cuenca_alta",
        name="Cuenca alta",
        kind="microcuenca",
        terrain=0.92,
        exposure=0.35,
        path_length_m=900,
        path_slope=0.20,
        coupling=1.0,
        svg="M250 46 L368 24 L488 58 L512 156 L430 214 L286 218 L206 150 Z",
        label=(360, 128),
        ring=(
            (-65.482, -23.893),
            (-65.452, -23.886),
            (-65.428, -23.896),
            (-65.436, -23.910),
            (-65.474, -23.912),
            (-65.482, -23.893),
        ),
    ),
    Zone(
        id="cauce",
        name="Cauce principal",
        kind="cauce",
        terrain=0.80,
        exposure=0.30,
        path_length_m=1900,
        path_slope=0.12,
        coupling=0.82,
        svg="M312 208 L408 206 L430 356 L292 360 Z",
        label=(360, 286),
        ring=(
            (-65.470, -23.912),
            (-65.448, -23.911),
            (-65.446, -23.928),
            (-65.468, -23.930),
            (-65.470, -23.912),
        ),
    ),
    Zone(
        id="cono",
        name="Cono de deyección",
        kind="cono",
        terrain=0.86,
        exposure=0.78,
        path_length_m=3200,
        path_slope=0.07,
        coupling=0.62,
        svg="M236 348 L486 342 L552 498 L168 508 Z",
        label=(360, 430),
        ring=(
            (-65.478, -23.926),
            (-65.440, -23.924),
            (-65.424, -23.942),
            (-65.486, -23.946),
            (-65.478, -23.926),
        ),
    ),
    Zone(
        id="casco",
        name="Casco urbano",
        kind="urbano",
        terrain=0.68,
        exposure=0.96,
        path_length_m=4300,
        path_slope=0.045,
        coupling=0.42,
        svg="M214 516 L512 506 L526 642 L200 652 Z",
        label=(360, 582),
        ring=(
            (-65.476, -23.944),
            (-65.442, -23.942),
            (-65.438, -23.958),
            (-65.478, -23.960),
            (-65.476, -23.944),
        ),
    ),
    Zone(
        id="accesos",
        name="Accesos",
        kind="acceso",
        terrain=0.58,
        exposure=0.72,
        path_length_m=4500,
        path_slope=0.04,
        coupling=0.40,
        svg="M132 524 L206 516 L194 654 L118 646 Z M524 506 L612 522 L598 648 L512 640 Z",
        label=(168, 590),
        ring=(
            (-65.492, -23.946),
            (-65.478, -23.944),
            (-65.480, -23.960),
            (-65.496, -23.958),
            (-65.492, -23.946),
        ),
    ),
    Zone(
        id="rn9",
        name="RN 9",
        kind="ruta",
        terrain=0.50,
        exposure=0.90,
        path_length_m=5100,
        path_slope=0.035,
        coupling=0.34,
        svg="M64 674 L656 656 L664 728 L56 744 Z",
        label=(360, 702),
        ring=(
            (-65.510, -23.962),
            (-65.420, -23.958),
            (-65.418, -23.970),
            (-65.512, -23.974),
            (-65.510, -23.962),
        ),
    ),
)

ZONE_BY_ID: dict[str, Zone] = {zone.id: zone for zone in ZONES}


def zones_geojson() -> dict:
    features = []
    for zone in ZONES:
        features.append(
            {
                "type": "Feature",
                "properties": {
                    "id": zone.id,
                    "name": zone.name,
                    "kind": zone.kind,
                    "terrain": zone.terrain,
                    "exposure": zone.exposure,
                    "note": "Esquema de demo. No usar para cartografía ni para una orden de evacuación.",
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [list(point) for point in zone.ring],
                },
            }
        )
    return {"type": "FeatureCollection", "features": features}
