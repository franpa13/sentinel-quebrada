"""Índice explicable de riesgo aluvional.

El índice no pronostica la lluvia. Parte de lo que la telemetría ya midió
(o de un escenario) y responde tres cosas: cuánto riesgo hay en este tramo,
qué término lo empujó, y cuántos minutos de concentración quedan según Kirpich.

Fast-trigger: una ráfaga corta en terreno susceptible pone un piso al índice
aunque el acumulado de 6–24 h todavía se vea inocente.

Memoria: el índice puede subir de una lectura a la otra, pero no se desploma
más de 12 puntos por paso. Un claro de diez minutos no apaga una alerta roja.

Confianza: un dato viejo no baja el índice. Si no alcanza para declarar calma,
el nivel operativo no se queda en verde.
"""

from __future__ import annotations

from dataclasses import dataclass

from sentinel.zones import Zone

LEVELS = ("verde", "amarillo", "naranja", "rojo")
MAX_DROP_PER_STEP = 12.0

# (mm o mm/h, aporte 0–1)
ACC_KNOTS = ((0.0, 0.0), (10.0, 0.15), (30.0, 0.45), (60.0, 0.78), (110.0, 1.0))
INTENSITY_KNOTS = ((0.0, 0.0), (5.0, 0.10), (15.0, 0.35), (30.0, 0.65), (60.0, 1.0))
BURST_KNOTS = ((0.0, 0.0), (5.0, 0.15), (15.0, 0.45), (25.0, 0.72), (40.0, 1.0))

W_ACC = 0.38
W_INTENSITY = 0.32
W_BURST = 0.30


@dataclass(frozen=True)
class Snapshot:
    rain_acc_mm: float
    intensity_mm_h: float
    burst_mm_30min: float
    soil_moisture: float
    data_age_min: float
    sensor_quality: float = 0.95

    def clamped(self) -> Snapshot:
        return Snapshot(
            rain_acc_mm=_clamp(self.rain_acc_mm, 0, 400),
            intensity_mm_h=_clamp(self.intensity_mm_h, 0, 300),
            burst_mm_30min=_clamp(self.burst_mm_30min, 0, 200),
            soil_moisture=_clamp(self.soil_moisture, 0, 1),
            data_age_min=_clamp(self.data_age_min, 0, 20000),
            sensor_quality=_clamp(self.sensor_quality, 0, 1),
        )

    def scaled(self, coupling: float) -> Snapshot:
        """Aproxima un pluviómetro aguas arriba leído desde un tramo de abajo."""
        coupling = _clamp(coupling, 0, 1)
        current = self.clamped()
        mix = 0.55 + 0.45 * coupling
        return Snapshot(
            rain_acc_mm=current.rain_acc_mm * (0.72 + 0.28 * coupling),
            intensity_mm_h=current.intensity_mm_h * mix,
            burst_mm_30min=current.burst_mm_30min * coupling,
            soil_moisture=current.soil_moisture,
            data_age_min=current.data_age_min,
            sensor_quality=current.sensor_quality,
        )

    def lerp(self, other: Snapshot, t: float) -> Snapshot:
        t = _clamp(t, 0, 1)
        return Snapshot(
            rain_acc_mm=_lerp(self.rain_acc_mm, other.rain_acc_mm, t),
            intensity_mm_h=_lerp(self.intensity_mm_h, other.intensity_mm_h, t),
            burst_mm_30min=_lerp(self.burst_mm_30min, other.burst_mm_30min, t),
            soil_moisture=_lerp(self.soil_moisture, other.soil_moisture, t),
            data_age_min=_lerp(self.data_age_min, other.data_age_min, t),
            sensor_quality=_lerp(self.sensor_quality, other.sensor_quality, t),
        )


@dataclass(frozen=True)
class Factor:
    id: str
    label: str
    points: float
    detail: str


@dataclass(frozen=True)
class Modifier:
    id: str
    label: str
    value: float
    factor: float
    detail: str


@dataclass(frozen=True)
class ZoneScore:
    zone_id: str
    name: str
    kind: str
    index: float
    level: str
    operational_level: str
    confidence: float
    confidence_note: str | None
    reaction_margin_min: float
    concentration_min: float
    fast_trigger: bool
    fast_trigger_reason: str | None
    exposure: float
    attention: float
    factors: tuple[Factor, ...]
    modifiers: tuple[Modifier, ...]
    svg: str
    label: tuple[float, float]
    snapshot: Snapshot


def piecewise(x: float, knots: tuple[tuple[float, float], ...]) -> float:
    if x <= knots[0][0]:
        return knots[0][1]
    for (x0, y0), (x1, y1) in zip(knots, knots[1:]):
        if x <= x1:
            if x1 == x0:
                return y1
            span = (x - x0) / (x1 - x0)
            return y0 + span * (y1 - y0)
    return knots[-1][1]


def concentration_minutes(length_m: float, slope: float) -> float:
    """Tiempo de concentración de Kirpich (1940), en minutos.

    L en metros, S en m/m. Tc = 0.0195 * L^0.77 * S^-0.385.
    Es una orientación del margen, no un modelo de flujo de detritos.
    """
    length_m = max(length_m, 50.0)
    slope = max(slope, 0.005)
    tc = 0.0195 * (length_m**0.77) * (slope**-0.385)
    return max(5.0, tc)


def reaction_margin_minutes(length_m: float, slope: float, index: float) -> float:
    tc = concentration_minutes(length_m, slope)
    remaining = max(0.12, 1.0 - 0.88 * (_clamp(index, 0, 100) / 100.0))
    return round(max(3.0, tc * remaining), 1)


def freshness(age_min: float) -> float:
    if age_min <= 15:
        return 0.97
    if age_min <= 45:
        return 0.85
    if age_min <= 120:
        return 0.62
    if age_min <= 240:
        return 0.40
    return 0.28


def level_for(index: float) -> str:
    if index < 25:
        return "verde"
    if index < 50:
        return "amarillo"
    if index < 75:
        return "naranja"
    return "rojo"


def apply_hysteresis(previous: float | None, raw: float, max_drop: float = MAX_DROP_PER_STEP) -> tuple[float, float]:
    """Devuelve (índice, puntos de memoria que evitaron la caída)."""
    raw = _clamp(raw, 0, 100)
    if previous is None or raw >= previous:
        return raw, 0.0
    held = min(100.0, max(raw, previous - max_drop))
    return held, round(held - raw, 1)


def fast_floor(burst_mm_30min: float, terrain: float) -> tuple[float, str | None]:
    if burst_mm_30min >= 40 and terrain >= 0.45:
        return 88.0, "Ráfaga extrema en terreno susceptible. Esperar el acumulado de 24 h llegaría tarde."
    if burst_mm_30min >= 25 and terrain >= 0.60:
        return 76.0, "Pico intenso de corta duración. El fast-trigger no espera el acumulado."
    if burst_mm_30min >= 15 and terrain >= 0.55:
        return 58.0, "Ráfaga corta sobre quebrada sensible."
    return 0.0, None


def score_zone(snapshot: Snapshot, zone: Zone, previous_index: float | None = None) -> ZoneScore:
    snap = snapshot.clamped()
    n_acc = piecewise(snap.rain_acc_mm, ACC_KNOTS)
    n_int = piecewise(snap.intensity_mm_h, INTENSITY_KNOTS)
    n_burst = piecewise(snap.burst_mm_30min, BURST_KNOTS)

    soil_factor = 0.45 + 0.55 * snap.soil_moisture
    terrain_factor = 0.50 + 0.50 * zone.terrain
    shared = 100.0 * soil_factor * terrain_factor

    c_acc = shared * W_ACC * n_acc
    c_int = shared * W_INTENSITY * n_int
    c_burst = shared * W_BURST * n_burst
    base = c_acc + c_int + c_burst

    floor, trigger_reason = fast_floor(snap.burst_mm_30min, zone.terrain)
    raw = min(100.0, max(base, floor))
    index, memory_points = apply_hysteresis(previous_index, raw)
    index = round(min(100.0, index), 1)

    factors: list[Factor] = [
        Factor(
            "lluvia_acumulada",
            "Lluvia acumulada 6–24 h",
            round(c_acc, 1),
            f"{snap.rain_acc_mm:.0f} mm aportan {c_acc:.0f} pts después de suelo y terreno.",
        ),
        Factor(
            "intensidad",
            "Intensidad horaria",
            round(c_int, 1),
            f"{snap.intensity_mm_h:.0f} mm/h aportan {c_int:.0f} pts.",
        ),
        Factor(
            "rafaga",
            "Ráfaga de 30 min",
            round(c_burst, 1),
            f"{snap.burst_mm_30min:.0f} mm en 30 min aportan {c_burst:.0f} pts.",
        ),
    ]
    trigger_points = max(0.0, floor - base) if floor > base else 0.0
    if trigger_points > 0:
        factors.append(
            Factor(
                "fast_trigger",
                "Fast-trigger",
                round(trigger_points, 1),
                trigger_reason or "Piso por ráfaga intensa.",
            )
        )
    if memory_points > 0.05:
        factors.append(
            Factor(
                "memoria",
                "Memoria de la alerta",
                round(memory_points, 1),
                "El índice no cae más de 12 puntos por paso: un claro breve no apaga la alerta.",
            )
        )

    confidence = round(freshness(snap.data_age_min) * snap.sensor_quality, 2)
    physical = level_for(index)
    operational = physical
    confidence_note = None
    if confidence < 0.45 and LEVELS.index(physical) < LEVELS.index("amarillo"):
        operational = "amarillo"
        confidence_note = (
            "Telemetría vieja o incompleta. No hay evidencia de calma: el nivel operativo sube a amarillo."
        )
    elif confidence < 0.60:
        confidence_note = "Dato degradado. Se mantiene el riesgo y baja la confianza."

    tc = round(concentration_minutes(zone.path_length_m, zone.path_slope), 1)
    margin = reaction_margin_minutes(zone.path_length_m, zone.path_slope, index)
    attention = round(index * (0.65 + 0.35 * zone.exposure), 1)

    return ZoneScore(
        zone_id=zone.id,
        name=zone.name,
        kind=zone.kind,
        index=index,
        level=physical,
        operational_level=operational,
        confidence=confidence,
        confidence_note=confidence_note,
        reaction_margin_min=margin,
        concentration_min=tc,
        fast_trigger=trigger_reason is not None and floor >= raw - 0.01 and floor > 0 and floor >= base,
        fast_trigger_reason=trigger_reason if floor > base else None,
        exposure=zone.exposure,
        attention=attention,
        factors=tuple(factors),
        modifiers=(
            Modifier(
                "suelo",
                "Humedad del suelo",
                round(snap.soil_moisture, 2),
                round(soil_factor, 2),
                "Suelo seco amortigua el aporte de la lluvia (×0.45). Suelo cargado llega a ×1.00.",
            ),
            Modifier(
                "terreno",
                "Susceptibilidad del tramo",
                round(zone.terrain, 2),
                round(terrain_factor, 2),
                "Pendiente, cauce y material del tramo. No es lo mismo la cuenca alta que la banquina.",
            ),
        ),
        svg=zone.svg,
        label=zone.label,
        snapshot=snap,
    )


def narrative(scores: list[ZoneScore]) -> str:
    by_id = {score.zone_id: score for score in scores}
    cuenca = by_id["cuenca_alta"]
    casco = by_id["casco"]
    ruta = by_id["rn9"]

    if cuenca.fast_trigger and cuenca.fast_trigger_reason:
        opening = (
            f"Fast-trigger en la cuenca alta: índice {cuenca.index:.0f}, nivel {cuenca.operational_level}. "
            f"{cuenca.fast_trigger_reason}"
        )
    else:
        opening = f"Cuenca alta en {cuenca.operational_level} (índice {cuenca.index:.0f})."

    body = (
        f" Casco urbano en {casco.operational_level} ({casco.index:.0f}), "
        f"margen estimado {casco.reaction_margin_min:.0f} min hasta organizar el pico. "
        f"RN 9 en {ruta.operational_level}, margen {ruta.reaction_margin_min:.0f} min."
    )
    stale = [score.name for score in scores if score.confidence < 0.5]
    tail = ""
    if stale:
        tail = " Confianza baja: silencio o atraso de sensores no es ausencia de riesgo."
    return opening + body + tail


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t
