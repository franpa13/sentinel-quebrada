# Modelo de datos 001

## Snapshot

Entrada única del puntaje.

| Campo | Rango | Sentido |
| --- | --- | --- |
| `rain_acc_mm` | 0–400 | Lluvia acumulada 6–24 h |
| `intensity_mm_h` | 0–300 | Intensidad de la última hora |
| `burst_mm_30min` | 0–200 | Milímetros en 30 minutos |
| `soil_moisture` | 0–1 | 0 seco, 1 saturado |
| `data_age_min` | 0–20000 | Edad del dato |
| `sensor_quality` | 0–1 | 1 instrumento confiable. Open-Meteo entra en 0.40 |

## Zona

Atributos fijos, no los manda el sensor.

| Campo | Sentido |
| --- | --- |
| `id` | `cuenca_alta`, `cauce`, `cono`, `casco`, `accesos`, `rn9` |
| `terrain` | Susceptibilidad del tramo, 0–1. Entra al índice. |
| `exposure` | Personas o vía crítica, 0–1. No infla el índice. Marca exposición alta desde 0.75. |
| `path_length_m`, `path_slope` | Camino desde la cabecera. Solo alimentan Kirpich. |
| `coupling` | Cuánto de la ráfaga del pluviómetro de arriba se siente en esta zona. Solo en `POST /evaluate`. |
| `svg`, `ring` | Dibujo de la demo y anillo GeoJSON. Esquema, no relevamiento. |

## ZoneScore

Salida por zona: `index`, `level` (físico), `operational_level`, `confidence`, `confidence_note`, `reaction_margin_min`, `concentration_min`, `fast_trigger`, `fast_trigger_reason`, `factors[]`, `modifiers[]`.

`factors[]` tiene `id`, `label`, `points`, `detail`. Los id posibles son `lluvia_acumulada`, `intensidad`, `rafaga`, `fast_trigger`, `memoria`.
