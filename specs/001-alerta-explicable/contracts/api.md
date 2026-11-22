# Contrato HTTP 001

Base local: `http://127.0.0.1:8000`. CORS abierto para `http://localhost:3000` y `http://127.0.0.1:3000`.

## GET /health

`{ "ok": true, "name": "sentinel-quebrada", "version": "..." }`

## GET /scenarios

Lista `id`, `title`, `summary`, `demo_hint`, `step_minutes`, `frame_count`.

Ids que DEBEN existir: `calma`, `acumulado_lento`, `pico_cuenca_alta`, `silencio_sensores`.

## GET /scenarios/{id}

`404` si el id no existe. Si existe: metadatos y `frames[]`. Cada frame tiene `index`, `label`, `minute`, `narrative`, `zones[]` con la forma de `ZoneScore` en `data-model.md`.

## POST /evaluate

Cuerpo:

```json
{
  "snapshot": {
    "rain_acc_mm": 8,
    "intensity_mm_h": 3,
    "burst_mm_30min": 0,
    "soil_moisture": 0.38,
    "data_age_min": 5,
    "sensor_quality": 0.95
  }
}
```

Respuesta: `mode` = `pluviometro_cuenca_alta`, una `note` que explica la atenuación aguas abajo, `narrative` y `zones[]`.

## GET /context/open-meteo

Query opcional `lat` y `lon`. Por defecto Volcán. Incluye `disclaimer`, `snapshot` con `sensor_quality` 0.40, `narrative` y `zones[]`.

`502` si la grilla no responde. Ese error no bloquea los escenarios.

## GET /zones.geojson

`FeatureCollection`. Cada feature repite id y nombre de la zona y una nota de que es un esquema de demo.
