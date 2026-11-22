from sentinel.ruta9 import CORTES, catalogo, evaluar_corte


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
