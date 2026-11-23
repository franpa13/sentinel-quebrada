import pytest

from sentinel.ruta9 import CORTES, catalogo, combinar_viaje, dias_de_corte, evaluar_corte, pueblos, tramo


def test_el_catalogo_cita_el_alud_de_volcan_y_no_se_dice_completo():
    data = catalogo()
    assert data["episode_count"] >= 10
    assert any(item["episode"] == "2017-01-10-volcan" for item in CORTES)
    assert "Vialidad" in data["note"]


def test_una_semana_seca_no_hereda_los_cortes_viejos():
    reading = evaluar_corte(-23.919, -65.463, month=1, peak_index=0, confidence=0.34, name="Volcán")
    assert reading["on_rn9"] is True
    assert reading["chance"] == 0
    assert reading["band"] == "baja"
    assert reading["operational"] == "atencion"
    assert all(factor["points"] == 0 for factor in reading["factors"])


def test_lluvia_fuerte_en_enero_sobre_volcan_sube_la_chance():
    dry = evaluar_corte(-23.919, -65.463, month=1, peak_index=0, confidence=0.9, name="Volcán")
    wet = evaluar_corte(-23.919, -65.463, month=1, peak_index=80, confidence=0.9, name="Volcán")
    july = evaluar_corte(-23.919, -65.463, month=7, peak_index=80, confidence=0.9, name="Volcán")
    assert wet["chance"] > dry["chance"]
    assert wet["band"] in ("alta", "muy_alta")
    assert wet["chance"] > july["chance"]
    assert {factor["id"] for factor in wet["factors"]} == {"lluvia_semana", "historia_local", "temporada"}


def test_lejos_de_la_ruta_no_hay_chance():
    reading = evaluar_corte(-34.60, -58.38, month=1, peak_index=90, confidence=0.9, name="Buenos Aires")
    assert reading["on_rn9"] is False
    assert reading["chance"] is None


def test_sin_lluvia_de_la_semana_no_se_declara_abierta():
    reading = evaluar_corte(-23.577, -65.393, month=None, peak_index=None, confidence=0, name="Tilcara")
    assert reading["on_rn9"] is True
    assert reading["operational"] == "atencion"
    assert reading["chance"] is None


def _week(*days):
    return {"days": [{"date": d, "index": i, "rain_mm": r, "confidence": c} for d, i, r, c in days]}


def test_cada_dia_tiene_su_chance_y_sus_factores():
    week = _week(("2027-01-10", 0, 0.0, 0.9), ("2027-01-11", 80, 40.0, 0.9), ("2027-01-12", None, None, 0))
    days = dias_de_corte(-23.919, -65.463, "Volcán", week)
    assert days[0]["chance"] == 0
    assert days[1]["chance"] > 40
    assert {f["id"] for f in days[1]["factors"]} == {"lluvia_dia", "historia_local", "temporada"}
    assert sum(f["points"] for f in days[1]["factors"]) == pytest.approx(days[1]["chance"], abs=0.2)
    assert days[2]["chance"] is None and days[2]["operational"] == "atencion"


def test_los_pueblos_van_de_sur_a_norte_y_cuentan_su_historia():
    data = pueblos()["pueblos"]
    assert data[0]["name"] == "Volcán" and data[-1]["name"] == "Humahuaca"
    assert [p["lat"] for p in data] == sorted(p["lat"] for p in data)
    assert data[0]["episodes_near"] >= 3


def test_el_tramo_incluye_los_extremos_en_orden_de_viaje():
    assert [p["name"] for p in tramo("Volcán", "Purmamarca")] == ["Volcán", "Tumbaya", "Purmamarca"]
    assert [p["name"] for p in tramo("Purmamarca", "Volcán")] == ["Purmamarca", "Tumbaya", "Volcán"]
    assert [p["name"] for p in tramo("Tilcara", "Tilcara")] == ["Tilcara"]
    with pytest.raises(ValueError):
        tramo("Volcán", "Salta")


def _town(name, days):
    return {"place": {"name": name}, "days": [
        {"date": d, "chance": c, "operational": o, "rain_mm": r} for d, c, o, r in days
    ]}


def test_el_viaje_lo_manda_el_pueblo_mas_comprometido_y_marca_el_mejor_dia():
    trip = combinar_viaje("Volcán", "Tumbaya", [
        _town("Volcán", [("d1", 10, "baja", 2), ("d2", 60, "alta", 30)]),
        _town("Tumbaya", [("d1", 30, "media", 8), ("d2", 20, "baja", 5)]),
    ])
    d1, d2 = trip["days"]
    assert (d1["chance"], d1["driver"], d1["operational"]) == (30, "Tumbaya", "media")
    assert (d2["chance"], d2["driver"], d2["operational"]) == (60, "Volcán", "alta")
    assert trip["best_day"] == "d1" and trip["worst_day"] == "d2"
    assert "Vialidad" in trip["headline"]
    assert any("no es una suma" in limit.lower() for limit in trip["limits"])


def test_un_pueblo_sin_dato_no_deja_el_viaje_en_baja_ni_es_mejor_dia():
    trip = combinar_viaje("Volcán", "Tumbaya", [
        _town("Volcán", [("d1", 5, "baja", 0), ("d2", 8, "baja", 1)]),
        _town("Tumbaya", [("d1", None, "atencion", None), ("d2", 9, "baja", 1)]),
    ])
    d1, d2 = trip["days"]
    assert d1["operational"] == "atencion" and d1["complete"] is False
    assert trip["best_day"] == "d2"


def test_sin_grilla_no_hay_mejor_dia_ni_ruta_libre():
    trip = combinar_viaje("Volcán", "Tilcara", [_town("Volcán", []), _town("Tilcara", [])])
    assert trip["days"] == [] and trip["best_day"] is None
    assert trip["operational"] == "atencion"


def test_los_cortes_del_tramo_quedan_cerca_de_sus_pueblos():
    trip = combinar_viaje("Volcán", "Volcán", [_town("Volcán", [("d1", 0, "baja", 0)])])
    places = {item["place"] for item in trip["cortes"]}
    assert "Volcán" in places
    assert not any("Uquía" in place for place in places)
