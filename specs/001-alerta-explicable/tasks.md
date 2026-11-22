# Tareas 001 — Alerta explicable

Hechas cuando el test o la pantalla de la spec correspondiente pasan.

- [x] T1. Índice aditivo con suelo y terreno (RF-01). Test: suelo cargado supera al suelo seco.
- [x] T2. Niveles verde, amarillo, naranja y rojo (RF-02).
- [x] T3. Fast-trigger con factor visible (RF-03). Test: la ráfaga no espera al acumulado.
- [x] T4. Caída máxima de 12 puntos por paso (RF-04). Test de memoria.
- [x] T5. Silencio de sensores sube el operativo a amarillo sin bajar el índice (RF-05).
- [x] T6. Kirpich y margen por zona (RF-06). Test: el casco concentra más lento que la cabecera.
- [x] T7. Escenario de pico con la cuenca en rojo antes que el casco (RF-07).
- [x] T8. Cuatro escenarios servidos por la API, el lento sin fast-trigger (RF-08).
- [x] T9. Perillas contra `POST /evaluate` con acople aguas abajo (RF-09).
- [x] T10. Open-Meteo opcional con calidad 0.40 y aviso de grilla (RF-10).
- [x] T11. Seis zonas en SVG y en GeoJSON, con el aviso de esquema (RF-11, RF-13).
- [x] T12. Narrativa de cuenca, casco y RN 9 (RF-12).
- [ ] T13. Calibrar pisos y pesos con eventos observados. Requiere enmendar RF-01 y RF-03, no solo el código.
- [ ] T14. Visor de mapa sobre `GET /zones.geojson`. Es una spec nueva (`specs/002-...`), no un parche de esta.
- [ ] T15. Ingesta de un pluviómetro real al mismo `Snapshot`. También es spec nueva.
