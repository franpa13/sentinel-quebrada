"""Escenarios precargados para la demo, sin red.

El pico en cuenca alta es el relato de un minuto: arriba el fast-trigger
ya está en rojo y el casco todavía no recibió el pulso.
"""

from __future__ import annotations

from dataclasses import dataclass

from sentinel.model import Snapshot, ZoneScore, narrative, score_zone
from sentinel.zones import ZONES, Zone

LAGS: dict[str, tuple[float, float, float]] = {
    # lag en fracción de la línea de tiempo, escala de ráfaga, escala de intensidad
    "cuenca_alta": (0.0, 1.0, 1.0),
    "cauce": (0.08, 0.90, 0.90),
    "cono": (0.18, 0.75, 0.82),
    "casco": (0.34, 0.70, 0.75),
    "accesos": (0.36, 0.60, 0.70),
    "rn9": (0.42, 0.55, 0.65),
}


@dataclass(frozen=True)
class Frame:
    label: str
    minute: int
    zones: tuple[ZoneScore, ...]

    @property
    def narrative(self) -> str:
        return narrative(list(self.zones))


@dataclass(frozen=True)
class Scenario:
    id: str
    title: str
    summary: str
    demo_hint: str
    step_minutes: int
    frames: tuple[Frame, ...]


def sample_keys(keys: list[tuple[float, Snapshot]], t: float) -> Snapshot:
    t = max(0.0, min(1.0, t))
    if t <= keys[0][0]:
        return keys[0][1]
    for (t0, left), (t1, right) in zip(keys, keys[1:]):
        if t <= t1:
            span = 0.0 if t1 == t0 else (t - t0) / (t1 - t0)
            return left.lerp(right, span)
    return keys[-1][1]


def pulse_snapshot(regional: Snapshot, pulse: Snapshot, burst_scale: float, intensity_scale: float) -> Snapshot:
    return Snapshot(
        rain_acc_mm=regional.rain_acc_mm * 0.75 + pulse.rain_acc_mm * 0.25,
        intensity_mm_h=pulse.intensity_mm_h * intensity_scale,
        burst_mm_30min=pulse.burst_mm_30min * burst_scale,
        soil_moisture=regional.soil_moisture,
        data_age_min=regional.data_age_min,
        sensor_quality=regional.sensor_quality,
    )


def play(zone_snaps: dict[str, list[Snapshot]]) -> tuple[Frame, ...]:
    """Recorre la línea de tiempo y aplica la memoria de alerta por zona."""
    count = len(next(iter(zone_snaps.values())))
    previous: dict[str, float | None] = {zone.id: None for zone in ZONES}
    frames: list[Frame] = []
    for index in range(count):
        scores: list[ZoneScore] = []
        for zone in ZONES:
            score = score_zone(zone_snaps[zone.id][index], zone, previous[zone.id])
            previous[zone.id] = score.index
            scores.append(score)
        frames.append(Frame(label=f"T+{index * 10} min", minute=index * 10, zones=tuple(scores)))
    return tuple(frames)


def _series_from_upper(keys: list[tuple[float, Snapshot]], steps: int = 9) -> dict[str, list[Snapshot]]:
    series: dict[str, list[Snapshot]] = {zone.id: [] for zone in ZONES}
    for step in range(steps):
        t = 0.0 if steps == 1 else step / (steps - 1)
        regional = sample_keys(keys, t)
        for zone in ZONES:
            lag, burst_scale, intensity_scale = LAGS[zone.id]
            pulse = sample_keys(keys, max(0.0, t - lag))
            series[zone.id].append(pulse_snapshot(regional, pulse, burst_scale, intensity_scale))
    return series


def _uniform(snapshot: Snapshot, steps: int = 1) -> dict[str, list[Snapshot]]:
    return {zone.id: [snapshot for _ in range(steps)] for zone in ZONES}


def _broadcast(keys: list[tuple[float, Snapshot]], steps: int = 9) -> dict[str, list[Snapshot]]:
    """Misma lluvia en todos los tramos: el terreno, no el retardo, hace la diferencia."""
    series = {zone.id: [] for zone in ZONES}
    for step in range(steps):
        t = 0.0 if steps == 1 else step / (steps - 1)
        snap = sample_keys(keys, t)
        for zone in ZONES:
            series[zone.id].append(snap)
    return series


PICO_KEYS: list[tuple[float, Snapshot]] = [
    (0.00, Snapshot(8, 3, 0, 0.38, 5, 0.96)),
    (0.25, Snapshot(14, 22, 16, 0.50, 5, 0.96)),
    (0.45, Snapshot(22, 62, 38, 0.62, 6, 0.94)),
    (0.70, Snapshot(36, 18, 10, 0.74, 8, 0.92)),
    (1.00, Snapshot(44, 6, 2, 0.80, 10, 0.90)),
]

ACUMULADO_KEYS: list[tuple[float, Snapshot]] = [
    (0.00, Snapshot(6, 3, 0, 0.28, 6, 0.95)),
    (0.50, Snapshot(48, 14, 3, 0.62, 8, 0.93)),
    (1.00, Snapshot(120, 28, 6, 0.95, 10, 0.92)),
]


def build_scenarios() -> tuple[Scenario, ...]:
    calma = _uniform(Snapshot(1.5, 0.2, 0, 0.22, 4, 0.98))
    silencio = _uniform(Snapshot(4, 1, 0, 0.30, 360, 0.40))
    return (
        Scenario(
            id="calma",
            title="Calma aparente",
            summary="Lluvia insignificante, suelo lejos de saturarse, telemetría fresca.",
            demo_hint="Arranque del pitch: el tablero en verde no es un adorno, es el contraste.",
            step_minutes=10,
            frames=play(calma),
        ),
        Scenario(
            id="acumulado_lento",
            title="Acumulado lento",
            summary="Horas de lluvia sin ráfaga extrema. El índice sube por suelo cargado y milímetros acumulados.",
            demo_hint="Mostrá que el motor también ve el peligro lento, sin disparar el fast-trigger.",
            step_minutes=10,
            frames=play(_broadcast(ACUMULADO_KEYS)),
        ),
        Scenario(
            id="pico_cuenca_alta",
            title="Pico en cuenca alta",
            summary="Ráfaga corta arriba. El casco y la RN 9 todavía no reciben el pulso.",
            demo_hint="Demo de un minuto: reproducí hasta que la cuenca alta cruce a rojo y frená. El margen del casco es el argumento.",
            step_minutes=10,
            frames=play(_series_from_upper(PICO_KEYS)),
        ),
        Scenario(
            id="silencio_sensores",
            title="Silencio de sensores",
            summary="Los últimos valores son bajos, pero el dato tiene horas. No se declara calma.",
            demo_hint="Cierre de rigor: ausencia de telemetría no es ausencia de alud.",
            step_minutes=10,
            frames=play(silencio),
        ),
    )


SCENARIOS: tuple[Scenario, ...] = build_scenarios()
SCENARIO_BY_ID: dict[str, Scenario] = {scenario.id: scenario for scenario in SCENARIOS}


def zone_for_tests(zone_id: str) -> Zone:
    for zone in ZONES:
        if zone.id == zone_id:
            return zone
    raise KeyError(zone_id)
