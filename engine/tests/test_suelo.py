from sentinel.suelo import (
    parse_cover,
    parse_inta_local,
    parse_inta_national,
    parse_saocom,
    raise_moisture,
    raise_terrain,
)


NATIONAL = {
    "provincia": "JUJUY",
    "orden_sue1": "Entisoles",
    "limit_ppal": "Pedregosidad",
    "erhidr_s1": "Ligera",
    "rocos_s1": "Interfiere labra",
    "porc_pens1": 5,
}
LOCAL = {
    "Nombre_Aso": "Río Grande",
    "Fisiografi": "Terrazas bajas y depósitos de coluvios aluvionales.",
    "Relieve": "Plano.",
}


def _feature(props):
    return {"features": [{"properties": props}]}


def test_la_carta_de_suelos_no_baja_una_pendiente_alta():
    national = parse_inta_national(_feature(NATIONAL))
    local = parse_inta_local(_feature(LOCAL))
    terrain, note = raise_terrain(0.92, national, local, None)
    assert terrain == 0.92
    assert "no bajan" in note


def test_el_coluvio_y_la_pedregosidad_suben_un_terreno_suave():
    national = parse_inta_national(_feature(NATIONAL))
    local = parse_inta_local(_feature(LOCAL))
    cover = parse_cover(_feature({"GRAY_INDEX": 7}))
    terrain, note = raise_terrain(0.48, national, local, cover)
    assert national["susceptibility"] == 0.75
    assert local["susceptibility"] == 0.80
    assert cover["clase"] == "Humedal"
    assert cover["susceptibility"] is None
    assert terrain == 0.80
    assert "INTA" in note or "asociación" in note


def test_la_roca_del_ign_si_sube_y_un_codigo_raro_no_se_inventa():
    rock = parse_cover(_feature({"GRAY_INDEX": 6}))
    assert rock["clase"] == "Afloramiento rocoso"
    terrain, _note = raise_terrain(0.40, None, None, rock)
    assert terrain == 0.72
    unknown = parse_cover(_feature({"GRAY_INDEX": 40}))
    assert unknown["clase"].startswith("Código 40")
    assert raise_terrain(0.50, None, None, unknown)[0] == 0.50


def test_saocom_no_seca_el_suelo_y_un_pixel_vacio_no_es_cero():
    assert parse_saocom({"features": []}) is None
    assert parse_saocom(_feature({"HUMEDAD_DE_SUELO": 22})) == 22
    assert raise_moisture(0.40, 22)[0] == 0.40
    assert raise_moisture(0.20, 55)[0] == 0.55
    assert raise_moisture(0.27, None)[0] == 0.27
    assert raise_moisture(None, None)[0] == 0.45
