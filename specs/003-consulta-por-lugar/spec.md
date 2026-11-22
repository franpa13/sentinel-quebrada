# Spec 003 — Consulta de cualquier punto, esta semana

Estado: implementada en el motor. El panel no la muestra.

## Contexto

`/context/lugar` leía un punto, pero el puntaje devolvía las seis zonas del esquema de Volcán. Quien entra a la web tiene que poder preguntar por su coordenada, u otra, si los próximos 7 días merecen atención. La fórmula del índice no cambia. El esquema de Volcán solo aparece si el punto cae dentro de esos anillos.

## Requisitos

### RF-18 Cualquier coordenada

`GET /consulta/semana` DEBE exigir `lat` y `lon`. Sin esas dos, no asume Volcán. `nombre` es opcional.

### RF-19 Siete días, un índice por día

Cada día DEBE entrar al índice ya existente: acumulada = milímetros del día en la grilla, intensidad = máxima hora de ese día (o el día dividido 24 si no hay horas), ráfaga = 0, calidad = 0.40. Un día sin milímetros NO DEBE guardarse como 0 ni como verde.

La semana DEBE resumirse por el día de mayor índice. El nivel operativo de la semana es el peor de los días. Confianza baja no deja el operativo en verde.

### RF-20 El terreno es del punto

La susceptibilidad sale de la pendiente SRTM de esa coordenada. Si la cota no responde, la susceptibilidad queda en 0.70 para no bajar el índice. El margen de Kirpich y las zonas del pueblo NO DEBEN aparecer si el punto está fuera del esquema.

### RF-21 Lo que no es

La respuesta DEBE decir que esto no pronostica el alud, no es orden de evacuación y que la grilla no ve la quebrada. El fast-trigger queda apagado porque no hay ráfaga de 30 minutos.

## Fuera de alcance

- Cambiar `web/`.
- Cambiar la forma de `GET /context/open-meteo`, que el panel ya consume con las zonas de Volcán.
- Inventar un modelo nuevo.
