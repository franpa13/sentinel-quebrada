from sentinel.model import Snapshot, apply_hysteresis, concentration_minutes, score_zone
from sentinel.scenarios import SCENARIO_BY_ID
from sentinel.zones import ZONE_BY_ID


def _score(**kwargs):
    zone = ZONE_BY_ID[kwargs.pop("zone")]
    previous = kwargs.pop("previous", None)
    return score_zone(Snapshot(**kwargs), zone, previous)


def test_calma_se_queda_en_verde():
    score = _score(
        zone="casco",
        rain_acc_mm=1.5,
        intensity_mm_h=0.2,
        burst_mm_30min=0,
        soil_moisture=0.22,
        data_age_min=4,
        sensor_quality=0.98,
    )
    assert score.operational_level == "verde"
    assert score.index < 25
    assert score.fast_trigger is False
    assert score.confidence > 0.9


def test_fast_trigger_no_espera_al_acumulado():
    triggered = _score(
        zone="cuenca_alta",
        rain_acc_mm=8,
        intensity_mm_h=10,
        burst_mm_30min=32,
        soil_moisture=0.35,
        data_age_min=5,
        sensor_quality=0.95,
    )
    quiet = _score(
        zone="cuenca_alta",
        rain_acc_mm=8,
        intensity_mm_h=10,
        burst_mm_30min=0,
        soil_moisture=0.35,
        data_age_min=5,
        sensor_quality=0.95,
    )
    assert triggered.fast_trigger is True
    assert triggered.index >= 76
    assert triggered.operational_level == "rojo"
    assert quiet.fast_trigger is False
    assert quiet.index < 40
    assert any(factor.id == "fast_trigger" for factor in triggered.factors)


def test_suelo_cargado_supera_al_suelo_seco():
    shared = dict(
        zone="cono",
        rain_acc_mm=45,
        intensity_mm_h=18,
        burst_mm_30min=4,
        data_age_min=8,
        sensor_quality=0.95,
    )
    dry = _score(soil_moisture=0.15, **shared)
    wet = _score(soil_moisture=0.95, **shared)
    assert wet.index >= dry.index + 10


def test_dato_viejo_no_declara_calma():
    score = _score(
        zone="casco",
        rain_acc_mm=4,
        intensity_mm_h=1,
        burst_mm_30min=0,
        soil_moisture=0.3,
        data_age_min=360,
        sensor_quality=0.4,
    )
    assert score.level == "verde"
    assert score.operational_level == "amarillo"
    assert score.confidence < 0.45
    assert score.confidence_note


def test_la_alerta_no_se_apaga_de_golpe():
    held, memory = apply_hysteresis(80, 40)
    assert held == 68
    assert memory == 28
    score = _score(
        zone="cuenca_alta",
        rain_acc_mm=8,
        intensity_mm_h=3,
        burst_mm_30min=0,
        soil_moisture=0.3,
        data_age_min=5,
        sensor_quality=0.95,
        previous=80,
    )
    assert score.index >= 68
    assert any(factor.id == "memoria" for factor in score.factors)


def test_el_pico_enciende_la_cuenca_antes_que_el_casco():
    frames = SCENARIO_BY_ID["pico_cuenca_alta"].frames
    assert len(frames) >= 8
    early = frames[0].zones
    early_by_id = {score.zone_id: score for score in early}
    assert early_by_id["cuenca_alta"].operational_level == "verde"
    assert early_by_id["casco"].operational_level == "verde"

    crossed = None
    for frame in frames:
        by_id = {score.zone_id: score for score in frame.zones}
        if by_id["cuenca_alta"].operational_level == "rojo" and by_id["cuenca_alta"].fast_trigger:
            crossed = by_id
            break
    assert crossed is not None
    assert crossed["casco"].index < crossed["cuenca_alta"].index
    assert crossed["casco"].operational_level in {"verde", "amarillo"}
    assert crossed["casco"].reaction_margin_min > crossed["cuenca_alta"].reaction_margin_min


def test_escenario_lento_no_dispara_fast_trigger():
    for frame in SCENARIO_BY_ID["acumulado_lento"].frames:
        assert all(score.fast_trigger is False for score in frame.zones)
    last = {score.zone_id: score for score in SCENARIO_BY_ID["acumulado_lento"].frames[-1].zones}
    assert last["cuenca_alta"].index > last["casco"].index
    assert last["cuenca_alta"].operational_level in {"naranja", "rojo"}


def test_kirpich_da_mas_margen_al_casco_que_a_la_cabecera():
    head = concentration_minutes(900, 0.20)
    town = concentration_minutes(4300, 0.045)
    assert town > head + 15


def test_silencio_de_sensores_sube_a_amarillo():
    frame = SCENARIO_BY_ID["silencio_sensores"].frames[0]
    assert all(score.operational_level == "amarillo" for score in frame.zones)
    assert "no es ausencia de riesgo" in frame.narrative
