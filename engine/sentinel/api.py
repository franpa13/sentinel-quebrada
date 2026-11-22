"""API del motor. El panel de Next.js consume estos endpoints."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from sentinel import __version__
from sentinel.model import Snapshot, ZoneScore, narrative, score_zone
from sentinel.open_meteo import OpenMeteoError, fetch_open_meteo, snapshot_from_hourly
from sentinel.scenarios import SCENARIO_BY_ID, SCENARIOS
from sentinel.zones import ZONES, zones_geojson

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
