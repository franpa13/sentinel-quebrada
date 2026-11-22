from datetime import datetime, timezone

from sentinel.lugar import (
    closest_station,
    parse_observations,
    parse_power,
    parse_smn_cap,
    parse_waterways,
    snapshot_from_power,
    steepest_slope,
)


def test_power_ignora_el_faltante_y_no_inventa_rafaga():
    payload = {
        "properties": {
            "parameter": {
                "PRECTOTCORR": {"20261118": 12.0, "20261119": 6.0, "20261120": -999},
                "GWETROOT": {"20261118": 0.4, "20261119": 0.55, "20261120": -999},
            }
        }
    }
    parsed = parse_power(payload)
    assert parsed["day"] == "20261119"
    assert parsed["rain_mm"] == 6.0
    assert parsed["soil"] == 0.55
    snapshot = snapshot_from_power(parsed)
    assert snapshot.burst_mm_30min == 0
    assert snapshot.intensity_mm_h == 0.25
    assert snapshot.sensor_quality == 0.35
    assert snapshot.data_age_min > 0


def test_la_pendiente_sale_de_la_cota_mas_empinada():
    slope = steepest_slope(
        [
            {"role": "centro", "lat": 0, "lon": 0, "elevation_m": 100},
            {"role": "norte", "lat": 0.01, "lon": 0, "elevation_m": 100},
            {"role": "sur", "lat": -0.01, "lon": 0, "elevation_m": 320},
        ]
    )
    assert slope["steepest_toward"] == "sur"
    assert slope["slope_m_per_m"] > 0.15


def test_elige_la_estacion_volcan_aunque_haya_otra_mas_cerca():
    rows = [
        {"nombre": "Puesto cercano", "geom": {"coordinates": [-65.463, -23.930]}},
        {"nombre": "Volcán - Dpto. Tumbaya", "geom": {"coordinates": [-65.463, -23.970]}},
    ]
    chosen = closest_station(rows, -23.919, -65.463)
    assert "Volc" in chosen["nombre"]


def test_observaciones_vacias_no_inventan_milimetros():
    assert parse_observations([]) == []
    assert parse_observations([{"timestart": "2026-11-01T00:00:00Z", "valor": 4.5}])[0]["value"] == 4.5


def test_overpass_se_queda_con_los_cauces():
    ways = parse_waterways(
        {"elements": [{"tags": {"waterway": "stream", "name": "Quebrada del Volcán"}}, {"tags": {"highway": "primary"}}]}
    )
    assert ways == [{"kind": "stream", "name": "Quebrada del Volcán"}]


def test_el_aviso_del_smn_tiene_que_nombrar_la_quebrada():
    xml = """
    <alert xmlns="urn:oasis:names:tc:emergency:cap:1.2">
      <info>
        <event>Tormentas</event>
        <description>Lluvias intensas.</description>
        <area><areaDesc>Buenos Aires</areaDesc></area>
      </info>
      <info>
        <event>Tormentas</event>
        <description>Precipitación en cortos períodos.</description>
        <area><areaDesc>Jujuy: Tumbaya y Volcán</areaDesc></area>
      </info>
    </alert>
    """.encode()
    alerts = parse_smn_cap(xml, -23.919, -65.463)
    assert len(alerts) == 1
    assert "Volcán" in alerts[0]["area"]
    assert parse_smn_cap(xml, -34.60, -58.38) == []


def test_la_edad_del_dato_de_power_es_positiva():
    parsed = parse_power(
        {"properties": {"parameter": {"PRECTOTCORR": {"20200101": 1}, "GWETROOT": {"20200101": 0.2}}}}
    )
    assert parsed["age_min"] > 1000
    assert datetime.now(timezone.utc).year >= 2026
