# Spec 002 — Lectura en vivo de un punto

Estado: implementada en el motor. El panel no la muestra todavía.

## Contexto

El índice ya existe, pero la demo lo alimenta con escenarios escritos a mano. Esta spec pide la última lectura pública de un punto de la quebrada, por defecto Volcán, y la pasa por el mismo índice. No agrega un modelo opaco.

## Requisitos

### RF-14 Lectura separada por fuente

`GET /context/lugar` DEBE consultar cada fuente por su cuenta. Si una falla, las demás DEBEN seguir y la respuesta DEBE decir cuál falló.

### RF-15 Lluvia y humedad que sí entran al índice

La precipitación diaria y la humedad de raíz de NASA POWER, último día con dato válido, DEBEN armar el Snapshot: acumulada = milímetros de ese día, intensidad = esos milímetros divididos 24, ráfaga = 0, calidad = 0.35.

Criterio: un día de 6 mm no dispara fast-trigger.

### RF-16 Lo que se muestra y no mueve el índice

Pendiente SRTM, estación hidrológica, cauces de OpenStreetMap, avisos CAP del SMN, NDVI MODIS y la última escena Sentinel-2 DEBEN volver en `sources`. NO DEBEN cambiar la fórmula del índice.

### RF-17 Lo que no está conectado se dice

IMERG de 30 minutos, la cobertura puntual del IGN y Google Earth Engine DEBEN figurar como `no_conectado`, con el motivo. No se simula su respuesta.

## Fuera de alcance

- Cambiar el panel. Lo toma quien trabaja `web/`.
- Calibrar el índice con NDVI o pendiente.
- Scrapear el sitio del SNIH o usar el token interno de la app del SMN.
