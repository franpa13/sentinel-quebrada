# Spec 004 — Suelos del Estado y satélite

Estado: implementada en el motor. El panel no la muestra.

## Contexto

La humedad que entraba al índice era solo NASA POWER, una grilla de unos 50 km. El INTA publica la carta de suelos, el IGN la cobertura hecha con imágenes satelitales y la CONAE la humedad SAOCOM. Esta spec las consulta en el punto. No cambia la fórmula: solo pueden subir la susceptibilidad o la humedad que el índice ya usa.

## Requisitos

### RF-22 Carta de suelos

`GET /context/lugar` y `GET /consulta/semana` DEBEN pedir la asociación de Salta y Jujuy y la unidad nacional 1:500.000 del INTA en `geo-backend.inta.gob.ar`. Si el punto no cae en una unidad, la fuente queda `vacio`.

### RF-23 Cobertura satelital

La clase del mapa de cobertura del IGN DEBE volver con su código y su nombre. Afloramiento rocoso y médano pueden subir la susceptibilidad. El resto, incluido un humedal, no la baja.

### RF-24 Humedad SAOCOM

Si el píxel de CONAE trae un porcentaje, la humedad del Snapshot DEBE ser el máximo entre ese valor y la de POWER. Si no hay píxel, no se guarda un cero.

### RF-25 No se declara un suelo más inocente

Una pendiente alta no baja porque la carta diga que la unidad es plana. Un fallo de estas fuentes no baja el índice ni pinta verde.

## Fuera de alcance

- Cambiar `web/`.
- Bajar el índice con un NDVI alto o con un suelo profundo.
- Descargar bandas de Sentinel-2: el catálogo no entrega el píxel sin cuenta. La escena sigue en las fuentes.
