# Plan 002 — Panel listo para la demo

Todo el cambio vive en `web/`. `engine/` no se toca: ni el índice, ni los escenarios, ni la geometría de `zones.py`.

## Decisiones

| Decisión | Cumple | Por qué |
| --- | --- | --- |
| La página ocupa `100dvh` desde `lg` en una columna flex: encabezado, grilla y pie de altura fija. La grilla toma el resto con `min-h-0`. | RF-01, RF-08 | El pie con el aviso deja de caerse debajo del borde. Cada columna desplaza su propio contenido si no entra. |
| La reproducción baja a una barra debajo del mapa, en la columna central. La columna izquierda queda para escenarios y perillas. | RF-01, RF-04 | El botón que arranca la demo queda a la vista. La tira de pasos queda al lado del dibujo que cambia. |
| El encabezado muestra el escenario y `T+N min · paso X de Y` en tamaño grande, a la derecha. El nombre del producto es el `h1`; se va la etiqueta en mayúsculas de arriba. | RF-04 | El estado de la demo se lee desde el fondo de la sala. |
| El mapa usa un `viewBox` más ancho (`40 0 1060 790`). Los polígonos quedan a la izquierda y los nombres van en una columna a la derecha, en orden aguas arriba → aguas abajo, unidos a su zona con una línea guía. | RF-02 | Hoy el SVG está limitado por el alto y tira el ancho. Con la columna de etiquetas, el nombre queda en ~14.5 px a 1280×720 en lugar de 7.9 px. |
| Los polígonos se pintan opacos y llevan el índice adentro en tinta oscura `#0a0f0c`. | RF-02 | La tinta oscura da al menos 4.76:1 contra los cuatro colores. El blanco sobre amarillo daba 3.10:1. |
| Etiquetas de la columna en `#f6f1e7` sobre el fondo del mapa, con una muestra de color al lado del nivel. | RF-02 | 16.7:1. El nivel no depende solo del color. |
| La leyenda de cuatro niveles va dentro del SVG, al pie, sin números. | RF-03 | Escala con el mapa y no le roba alto. Los umbrales siguen en `engine/`. |
| Una zona con `fast_trigger` lleva una pastilla “Fast-trigger” en su fila de la columna. | RF-09 | El argumento del pitch se ve en el mapa, no solo en la ficha. |
| Cada zona del SVG es un `<g role="button" tabIndex={0}>` con `aria-label` que dice nombre, nivel e índice, y responde a Enter y espacio. El foco se dibuja como borde de la fila. Los textos internos llevan `aria-hidden`. | RF-10 | Las píldoras de zona que duplicaban el mapa se van en escritorio; el teclado entra por el mapa. |
| En pantallas chicas el SVG usa solo la zona de polígonos (`40 0 640 790`) y debajo aparecen las píldoras de zona. | RF-11 | A 390 px la columna de etiquetas quedaría en 9 px. |
| Detalles de factores y notas pasan de `#6e8578` a `#8aa094`, y de 10–11 px a 12 px. La tinta sobre colores de nivel pasa de `#102017` a `#0a0f0c`. | RF-05 | `#6e8578` sobre `#17211c` daba 4.16:1. `#8aa094` da 5.93:1. `#102017` sobre rojo daba 4.17:1. |
| Las perillas numeran cada pedido con un `useRef`. Solo la respuesta del último pedido escribe el estado. Open-Meteo usa el mismo contador. | RF-06 | Una respuesta vieja que llega tarde ya no pisa la lectura nueva. |
| La carga inicial es una función `connect()` que usan el efecto y el botón “Reintentar”. | RF-07 | Se recupera sin recargar. |
| Atajos: espacio reproduce o pausa, flechas cambian de paso. Se ignoran si el foco está en un control. | RF-04 (PUEDE) | El presentador maneja la demo sin apuntar con el mouse. |
| La tira de pasos usa `scenario.step_minutes` para el texto, en lugar de un 10 fijo. | RF-04 | El panel no repite un número que da la API. |
| Radios de tarjeta en 16 px y fichas internas en 12 px. Los títulos llevan `text-wrap: balance`. | RF-05 | Ajustes que pide la auditoría; no cambian la identidad. |

## Mapa

| Requisito | Dónde vive |
| --- | --- |
| RF-01, RF-08 | `web/src/components/Dashboard.tsx` (estructura de página) |
| RF-02, RF-03, RF-09, RF-10 | `BasinMap` en `web/src/components/Dashboard.tsx` |
| RF-04 | `Transport` y encabezado en `web/src/components/Dashboard.tsx` |
| RF-05 | `Dashboard.tsx`, `web/src/lib/types.ts` (`LEVEL_INK`), `web/src/app/globals.css` |
| RF-06, RF-07 | `Dashboard` (estado y efectos) |
| RF-11 | `Dashboard.tsx` (orden de columnas, píldoras solo en pantalla chica) |

## Verificación

1. `npm test` en la raíz: el motor no cambió y los 9 tests siguen en verde.
2. `npm run lint --prefix web` y `npm run build --prefix web`.
3. En el navegador, a 1280×720, 1920×1080 y 390×844, con el escenario de pico en T+40 min:
   - el script de `kero-audit` sin fallas `hard`;
   - `scrollHeight` igual al alto de la ventana en los dos tamaños de escritorio;
   - tamaño renderizado de las etiquetas del mapa (RF-02);
   - botón de reproducir y aviso dentro de la ventana.
4. Recorrido con teclado: Tab llega a escenarios, reproducción, zonas del mapa y perillas con foco visible.
5. Con el motor apagado, el aviso aparece y “Reintentar” conecta cuando el motor vuelve.

## Riesgos

- Las posiciones de la columna de etiquetas y de las líneas guía viven en el panel, por `zone_id`. Si `zones.py` cambia la geometría o suma una zona, hay que mover esa tabla. Una zona sin entrada en la tabla se sigue dibujando, sin etiqueta lateral.
- Con la ventana más baja que 720 px el mapa se achica y las etiquetas bajan de 14 px. El requisito se fija en 1280×720.
- Next 16 trae cambios de API (ver `web/AGENTS.md`). Este plan no usa APIs nuevas de Next: el cambio queda dentro de un componente cliente.
