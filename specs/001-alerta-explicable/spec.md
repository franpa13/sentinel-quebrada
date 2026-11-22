# Spec 001 — Alerta explicable

Estado: implementada.

El sistema informa el cruce de umbrales en la cuenca de Volcán. No pronostica la tormenta y no ordena una evacuación.

## Contexto

Volcán está sobre un cono de deyección. Una ráfaga corta en la quebrada alta puede llegar al casco y a la RN 9 antes de que el acumulado de varias horas “parezca grave”. Quien mira el tablero tiene que ver el nivel, qué término lo armó y cuántos minutos de concentración quedan.

## Historias

### Historia 1 — Pico arriba, pueblo todavía en calma

Como operador de la demo, quiero reproducir un escenario en el que la cuenca alta ya está en rojo y el casco sigue por debajo, para mostrar que el aviso nace aguas arriba.

### Historia 2 — La ráfaga no espera

Como quien defiende el modelo, quiero que una ráfaga de 30 minutos en terreno susceptible suba el índice aunque el acumulado de 6–24 h sea bajo, y quiero ver esos puntos aparte.

### Historia 3 — El silencio no es calma

Como operador, quiero que un dato viejo o de mala calidad no pinte verde aunque los últimos milímetros sean bajos.

### Historia 4 — Perillas sin red

Como presentador, quiero mover lluvia, intensidad, ráfaga, suelo y edad del dato y ver el mapa cambiar, sin depender de un servicio externo.

## Requisitos

### RF-01 Índice

El sistema DEBE calcular un índice de 0 a 100 por zona a partir de lluvia acumulada (6–24 h), intensidad horaria y ráfaga de 30 minutos.

Esos tres aportes DEBEN multiplicarse por la humedad del suelo (de ×0.45 en seco a ×1.00 en saturado) y por la susceptibilidad del tramo (de ×0.50 a ×1.00).

Los pesos de partida DEBEN ser 0.38 acumulada, 0.32 intensidad y 0.30 ráfaga.

Criterio: con la misma lluvia, un suelo más húmedo puntúa más alto. El desglose en puntos suma la base del índice.

### RF-02 Niveles

El nivel físico DEBE ser verde por debajo de 25, amarillo por debajo de 50, naranja por debajo de 75 y rojo desde 75.

Criterio: los cuatro colores se distinguen en el mapa y en la ficha de la zona.

### RF-03 Fast-trigger

El sistema DEBE aplicar un piso, independientemente del acumulado:

- ráfaga ≥ 15 mm y terreno ≥ 0.55 → piso 58
- ráfaga ≥ 25 mm y terreno ≥ 0.60 → piso 76
- ráfaga ≥ 40 mm y terreno ≥ 0.45 → piso 88

Si el piso supera la base, DEBE aparecer un factor “Fast-trigger” con los puntos de diferencia y el motivo.

Criterio: 32 mm en 30 min sobre la cuenca alta, con acumulada baja, deja el índice en al menos 76 y en rojo. La misma lectura sin ráfaga no dispara el piso.

### RF-04 Memoria

Si hay un índice previo, el nuevo DEBE poder subir libremente y NO DEBE caer más de 12 puntos en un paso.

Criterio: un índice previo de 80 y una lectura cruda baja quedan en 68, con un factor de memoria.

### RF-05 Confianza

La confianza DEBE ser frescura por calidad del sensor, entre 0 y 1. La frescura DEBE bajar con la edad del dato (fresca hasta 15 min; muy degradada después de 240 min).

Una confianza bajo 0.45 NO DEBE reducir el índice. Si además el nivel físico es verde, el nivel operativo DEBE subir a amarillo y la ficha DEBE decir que no hay evidencia de calma.

Criterio: el escenario de silencio de sensores queda en amarillo operativo en todas las zonas.

### RF-06 Margen

El sistema DEBE estimar el tiempo de concentración de Kirpich, en minutos: `0.0195 · L^0.77 · S^-0.385`, con L en metros y S en m/m, con un piso de 5 minutos.

El margen de reacción DEBE achicarse cuando el índice de esa zona sube, sin bajar de 3 minutos.

La interfaz DEBE decir que es un tiempo de concentración, no un modelo de flujo de detritos.

Criterio: el tramo hasta el casco tiene más tiempo de concentración que la cuenca alta.

### RF-07 Cascada

En el escenario de pico, la intensidad y la ráfaga DEBEN llegar primero a la cuenca alta y después, atenuadas, al cauce, al cono, al casco, a los accesos y a la RN 9.

Criterio: existe un paso en el que la cuenca alta está en rojo por fast-trigger y el casco todavía está en verde o amarillo, con un margen mayor que el de la cuenca.

### RF-08 Escenarios sin red

El sistema DEBE servir, sin llamar a internet, al menos: calma, acumulado lento, pico en cuenca alta y silencio de sensores.

El acumulado lento NO DEBE disparar fast-trigger.

Criterio: `GET /scenarios` los lista y `GET /scenarios/{id}` trae los cuadros ya puntuados.

### RF-09 Perillas

`POST /evaluate` DEBE interpretar el cuerpo como un pluviómetro en la cuenca alta y atenuar intensidad y ráfaga aguas abajo según el acople de cada zona.

Criterio: la misma ráfaga alta deja la cuenca por encima del casco.

### RF-10 Contexto meteorológico

`GET /context/open-meteo` PUEDE traer precipitación de grilla para Volcán (aprox. -23.919, -65.463).

La calidad de ese dato DEBE quedar en 0.40. La respuesta DEBE decir que la grilla no ve la quebrada.

Si el servicio no responde, la demo DEBE seguir usable con los escenarios.

### RF-11 Zonas

El sistema DEBE distinguir cuenca alta, cauce principal, cono de deyección, casco urbano, accesos y RN 9.

El mapa de la demo PUEDE ser un esquema SVG. `GET /zones.geojson` DEBE publicar el mismo esquema y DEBE aclarar que no es cartografía oficial.

### RF-12 Narrativa

Cada cuadro DEBE incluir una frase que nombre el nivel de la cuenca alta, el del casco, el de la RN 9 y los márgenes de casco y ruta.

Si alguna zona tiene confianza bajo 0.5, la frase DEBE decir que el silencio o el atraso no es ausencia de riesgo.

### RF-13 Límites visibles

La interfaz DEBE mostrar que el esquema no es una orden de evacuación.

## Fuera de alcance

- Orden de evacuación, sirenas o mensaje a la población.
- Modelo hidráulico 2D o de colada de barro y piedra.
- Calibración con la serie histórica de Volcán. Los umbrales de esta spec son los de partida.
- Mapa con teselas. El GeoJSON queda listo; el visor real es otra spec.
- Pluviómetro físico. El contrato del dato ya es el de esta spec.

## Clarificaciones

Ninguna abierta. Los números de RF-01 a RF-06 son los de partida del hackathon, no una calibración hidrológica cerrada.
