"""Contexto meteorológico de grilla. No reemplaza un pluviómetro en la quebrada."""

from __future__ import annotations

import json
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import urlopen

from sentinel.model import Snapshot

VOLCAN_LAT = -23.919
VOLCAN_LON = -65.463
OPEN_METEO = "https://api.open-meteo.com/v1/forecast"


class OpenMeteoError(RuntimeError):
    pass


def fetch_open_meteo(lat: float = VOLCAN_LAT, lon: float = VOLCAN_LON, timeout: float = 8.0) -> dict:
    query = urlencode(
        {
            "latitude": lat,
            "longitude": lon,
            "hourly": "precipitation",
            "past_days": 1,
            "forecast_days": 1,
            "timezone": "America/Argentina/Jujuy",
        }
    )
    try:
        with urlopen(f"{OPEN_METEO}?{query}", timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (URLError, TimeoutError, json.JSONDecodeError) as error:
        raise OpenMeteoError("Open-Meteo no respondió. La demo no lo necesita: usá los escenarios.") from error
    return payload


def snapshot_from_hourly(payload: dict) -> Snapshot:
    hourly = payload.get("hourly") or {}
    precip = hourly.get("precipitation") or []
    if len(precip) < 6:
        raise OpenMeteoError("Open-Meteo no trajo suficientes horas de precipitación.")
    # La serie mezcla pasado y pronóstico. Tomamos las últimas 12 horas ya emitidas
    # antes del tramo futuro: Open-Meteo ordena desde past_days, así que el bloque
    # central (índice 24, fin del día pasado) es el ancla si existe.
    anchor = 24 if len(precip) > 30 else len(precip) - 1
    window = [float(value or 0) for value in precip[max(0, anchor - 11) : anchor + 1]]
    accumulated = sum(window)
    intensity = window[-1] if window else 0.0
    # Una grilla de ~10 km no ve la quebrada. La calidad queda baja a propósito.
    return Snapshot(
        rain_acc_mm=round(accumulated, 1),
        intensity_mm_h=round(intensity, 1),
        burst_mm_30min=round(intensity / 2.0, 1),
        soil_moisture=0.45,
        data_age_min=30,
        sensor_quality=0.40,
    )
