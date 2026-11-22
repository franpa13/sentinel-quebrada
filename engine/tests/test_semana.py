from sentinel.semana import evaluar_semana, parse_week, terrain_from_slope
from sentinel.zones import zones_containing


def _payload(rains):
    times = []
    values = []
    for index, rain in enumerate(rains):
        day = f"2026-11-{22 + index:02d}"
        if rain is None:
            continue
        times.append(f"{day}T15:00")
        values.append(0.4)
    return {
        "daily": {"time": [f"2026-11-{22 + index:02d}" for index in range(len(rains))], "precipitation_sum": rains},
        "hourly": {"time": times, "precipitation": values},
    }


def test_un_dia_sin_milimetros_no_es_cero_ni_verde():
    days = parse_week(_payload([1, None, 4, 0, 0, 0, 2]))
    week = evaluar_semana(days, soil=0.3, terrain=0.7, name="Casa")
    missing = week["days"][1]
    assert missing["rain_mm"] is None
    assert missing["index"] is None
    assert missing["operational_level"] == "amarillo"
    assert week["peak_day"] == "2026-11-24"


def test_la_semana_no_dispara_fast_trigger_y_no_declara_calma():
    days = parse_week(_payload([80, 0, 0, 0, 0, 0, 0]))
    steep = evaluar_semana(days, soil=0.5, terrain=1.0, name="Quebrada")
    flat = evaluar_semana(days, soil=0.5, terrain=0.25, name="Llano")
    assert steep["days"][0]["fast_trigger"] is False
    assert steep["days"][0]["index"] > flat["days"][0]["index"]
    assert steep["operational_level"] != "verde"
    assert flat["days"][0]["level"] == "verde"
    assert flat["operational_level"] == "amarillo"


def test_sin_pendiente_no_se_baja_el_terreno():
    terrain, note = terrain_from_slope(None)
    assert terrain == 0.70
    assert "0.70" in note
    assert terrain_from_slope(35)[0] == 1.0


def test_el_esquema_de_volcan_no_cubre_otra_ciudad():
    assert [zone.id for zone in zones_containing(-23.919, -65.463)] == ["cauce"]
    assert zones_containing(-34.60, -58.38) == ()
