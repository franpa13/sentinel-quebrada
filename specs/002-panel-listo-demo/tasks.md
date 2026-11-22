# Tareas 002 — Panel listo para la demo

Hechas cuando su criterio de la spec se puede mostrar en el navegador.

- [x] T1. Página de una pantalla con encabezado, grilla y pie fijos (RF-01, RF-08). Criterio: sin scroll del documento a 1280×720 y 1920×1080; aviso visible.
- [x] T2. Barra de reproducción debajo del mapa y estado `T+N min` en el encabezado (RF-04). Criterio: el botón de reproducir queda dentro de la ventana a 1280×720.
- [x] T3. Mapa con columna de etiquetas, líneas guía e índice en tinta oscura (RF-02). Criterio: nombres ≥ 14 px y nivel ≥ 12 px a 1280×720; contraste ≥ 4.5:1. Medido: 15.1 px y 12.1 px.
- [x] T4. Leyenda de niveles sin umbrales (RF-03).
- [x] T5. Pastilla de fast-trigger en el mapa (RF-09). Criterio: visible en la cuenca alta en T+30 y T+40 del pico. En teléfono va en la píldora de la zona.
- [x] T6. Zonas del mapa con teclado y foco visible (RF-10). Medido: 29 paradas de Tab, todas con foco visible.
- [x] T7. Contraste y tamaño mínimo de texto (RF-05). Criterio: `kero-audit` sin fallas `hard` en los tres tamaños.
- [x] T8. Perillas sin respuestas viejas (RF-06). Probado demorando la primera respuesta de `/evaluate`.
- [x] T9. Botón “Reintentar” con el motor caído (RF-07).
- [x] T10. Teléfono sin scroll horizontal, mapa primero, píldoras de zona (RF-11).
- [x] T11. Atajos de teclado de reproducción (RF-04, PUEDE).
- [x] T12. `npm test`, lint y build en verde.

Excepción conocida: `kero-audit` marca el radio del botón “Reproducir” (píldora) dentro de la barra de 16 px. Se deja así: es un control en forma de píldora, no una tarjeta anidada.
