# Plan 001 — Alerta explicable

La spec ya está implementada. Este plan es el mapa para no rehacerla en otro lenguaje ni en otro archivo.

## Decisiones

| Decisión | Cumple | Por qué |
| --- | --- | --- |
| Puntaje en Python, en `engine/sentinel/model.py` | RF-01 a RF-06 | Una sola fórmula, testeable sin el navegador. |
| FastAPI en `engine/sentinel/api.py` | RF-08 a RF-12 | El panel y un sensor futuro hablan el mismo JSON. |
| Escenarios en `engine/sentinel/scenarios.py` | RF-07, RF-08 | El relato del pico no depende de la red. |
| Zonas en `engine/sentinel/zones.py` | RF-11 | SVG para la demo y anillo GeoJSON salen del mismo lugar. |
| Open-Meteo en `engine/sentinel/open_meteo.py` con calidad 0.40 | RF-10 | La grilla no se disfraza de pluviómetro. |
| Panel Next.js que solo dibuja la respuesta | RF-02, RF-09, RF-13 | Si el panel calculara el índice, habría dos verdades. |

## Mapa

| Requisito | Dónde vive |
| --- | --- |
| RF-01, RF-02, RF-03, RF-04, RF-05, RF-06 | `engine/sentinel/model.py` |
| RF-07, RF-08 | `engine/sentinel/scenarios.py` |
| RF-09, RF-10, RF-12 | `engine/sentinel/api.py` |
| RF-11 | `engine/sentinel/zones.py` y `web/src/components/Dashboard.tsx` |
| RF-13 | `web/src/components/Dashboard.tsx` |
| Compuerta | `engine/tests/test_model.py` |

## Contrato de lectura

Un `Snapshot` es la única entrada del modelo: `rain_acc_mm`, `intensity_mm_h`, `burst_mm_30min`, `soil_moisture`, `data_age_min`, `sensor_quality`. Quien agregue un sensor lo traduce a esos campos. No se agregan columnas al índice sin una spec nueva.

## Riesgos

- Los umbrales no están calibrados con eventos de Volcán. Mover un piso sin actualizar RF-03 y su test deja la spec y el código divorciados.
- Kirpich se lee fácil como “faltan N minutos para el alud”. La interfaz tiene que seguir diciendo que es tiempo de concentración.
