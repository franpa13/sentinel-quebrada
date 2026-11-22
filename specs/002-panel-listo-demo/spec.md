# Spec 002 — Panel listo para la demo

Estado: implementada.

El panel de la spec 001 funciona, pero en un proyector no se lee. Esta spec no cambia el índice ni la API: fija cómo tiene que verse y comportarse la pantalla para que el relato de un minuto se pueda contar sin scroll y sin explicar lo que no se ve.

## Contexto

La demo se presenta hoy, en la Cursor Hackathon Jujuy a bordo del Tren Solar, que sale de Volcán. La pantalla de presentación más probable es un proyector o una TV de 1280×720 o 1920×1080.

Medición del panel actual a 1280×720:

- El botón **Reproducir** queda en y=702 con una ventana de 720 de alto. El presentador tiene que hacer scroll en la columna izquierda para arrancar la demo.
- El mapa se dibuja a escala ×0.44. Los nombres de zona quedan en 7.9 px y el nivel en 6.2 px. Texto blanco sobre amarillo da 3.10:1 y sobre naranja 4.03:1.
- El aviso “no es cartografía oficial ni una orden de evacuación” queda cortado debajo del borde (707–747 px). Es un DEBE de la constitución (8) y de la spec 001 (RF-13).
- 7 textos fallan contraste WCAG AA (los detalles de cada factor en #6e8578 sobre #17211c dan 4.16:1). 59 de 88 textos están por debajo de 14 px; algunos en 10 px.

## Historias

### Historia 1 — Arrancar sin buscar

Como presentador, quiero ver el escenario, el paso actual y el botón de reproducir en la primera pantalla, para arrancar el relato sin scroll.

### Historia 2 — Leer el mapa desde el fondo de la sala

Como jurado, quiero leer el nombre y el nivel de cada zona desde lejos, para ver que la cuenca alta se enciende antes que el casco.

### Historia 3 — El límite siempre a la vista

Como quien defiende el proyecto, quiero que el aviso de límites se vea siempre, para que nadie confunda el esquema con una orden de evacuación.

### Historia 4 — Perillas que no mienten

Como presentador, quiero que al mover una perilla rápido el panel muestre la última lectura que pedí, no una respuesta vieja que llegó tarde.

### Historia 5 — Recuperarse si el motor no está

Como presentador, quiero reintentar la conexión con el motor desde la pantalla, sin recargar ni abrir una terminal delante del jurado.

## Requisitos

### RF-01 Una pantalla

A 1280×720 y a 1920×1080 la página NO DEBE tener scroll vertical del documento. En la primera pantalla DEBEN verse: el título, el escenario activo, el paso actual, los controles de reproducción, el mapa, la frase narrativa, el índice, el nivel y el margen de la zona elegida, y el aviso de límites.

El desglose de factores PUEDE desplazarse dentro de su tarjeta.

Criterio: con el escenario de pico en T+40 min, `document.documentElement.scrollHeight` es igual al alto de la ventana en los dos tamaños, y el botón de reproducir y el aviso quedan dentro de la ventana.

### RF-02 Mapa legible

A 1280×720 el nombre de cada zona DEBE medir al menos 14 px en pantalla y su nivel con índice al menos 12 px.

Todo texto del mapa DEBE tener un contraste de al menos 4.5:1 contra lo que tiene detrás, en los cuatro niveles.

Cada zona DEBE poder asociarse a su nombre, su nivel y su índice sin hacer clic. Los dos tramos de “Accesos” DEBEN mostrar su índice.

Criterio: medición en el navegador del tamaño renderizado de las etiquetas y cálculo de contraste contra el color pintado.

### RF-03 Leyenda de niveles

El mapa DEBE mostrar una leyenda con los cuatro niveles (verde, amarillo, naranja, rojo) y sus nombres.

La leyenda NO DEBE escribir los umbrales numéricos: viven en `engine/` y el panel no los copia (constitución, DEBE 2).

### RF-04 Paso y reproducción

El paso actual (`T+N min`) y el título del escenario DEBEN leerse como el estado principal de la pantalla, no como una nota al margen.

Cada casilla de la tira de pasos DEBE tener un nombre accesible con su minuto.

El panel PUEDE aceptar atajos de teclado: espacio para reproducir o pausar, flechas para cambiar de paso.

### RF-05 Contraste y tamaño de texto

Ningún texto de la página DEBE quedar por debajo de WCAG AA (4.5:1, o 3:1 si es grande).

Ningún texto DEBE medir menos de 12 px.

Criterio: el script de `kero-audit` no informa fallas `hard` a 1280×720, 1920×1080 ni 390×844.

### RF-06 Perillas en orden

Si se piden dos evaluaciones seguidas, la respuesta de la anterior NO DEBE reemplazar a la más nueva.

Mientras una evaluación está en curso, el panel DEBE seguir mostrando la última lectura válida.

### RF-07 Motor caído

Si el motor no responde al cargar, el panel DEBE decirlo y DEBE ofrecer un botón para reintentar sin recargar la página.

### RF-08 Límites a la vista

El aviso de límites de la spec 001 (RF-13) DEBE quedar visible en la primera pantalla a 1280×720 y a 1920×1080. El texto no cambia.

### RF-09 Fast-trigger en el mapa

Una zona con `fast_trigger` verdadero DEBE marcarse en el mapa, además de en la ficha.

### RF-10 Teclado y foco

Todo control DEBE tener foco visible. Toda zona DEBE poder elegirse con teclado.

### RF-11 Teléfono

A 390×844 NO DEBE haber scroll horizontal. El mapa y la frase narrativa PUEDEN ir antes que las perillas.

## Fuera de alcance

- Cambios al índice, a los escenarios o a la API. Si algo de esta spec necesita un dato que la API no da, se deja escrito y no se calcula en el panel.
- Mapa con teselas o MapLibre. Sigue siendo T14 de la spec 001.
- Memoria de alerta en el modo perillas. RF-04 de la spec 001 y la constitución (DEBE 5) la exigen entre pasos de un escenario; las perillas no son pasos. Ver Clarificaciones.
- Rediseño de identidad. Se mantienen la paleta, las tipografías (Geist y Fraunces) y la estructura de tres columnas.

## Clarificaciones

- Memoria en perillas: `POST /evaluate` acepta `previous_index`, pero el panel no lo manda. Con memoria, bajar la ráfaga no bajaría el índice de golpe y el presentador podría leerlo como un error. Esta spec no la activa. Si se quiere, es una decisión de producto que se escribe en una spec aparte.
