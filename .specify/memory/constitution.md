# Constitución — Sentinel Quebrada

Principios que ninguna spec puede contradecir. Si una spec nueva choca con un DEBE de acá, se cambia la spec o se enmienda esta constitución a propósito, con el cambio escrito.

## Propósito

Ayudar a ver, minutos u horas antes, cuándo una quebrada de Volcán (Jujuy) cruza umbrales de lluvia, suelo y terreno. El sistema informa. No evacua y no pronostica el clima.

## DEBE

1. **Explicable.** Cada punto del índice 0–100 tiene un factor con nombre, puntos y una frase. Un piso o una memoria que mueva el índice también aparece como factor.
2. **Una sola verdad.** El puntaje se calcula en `engine/` (Python). El panel, otro cliente o un script futuro llaman a esa lógica. No se copia la fórmula a otro lenguaje.
3. **El dato malo no es calma.** Confianza baja no reduce el índice. Si la confianza no alcanza para declarar calma, el nivel operativo no se queda en verde.
4. **La ráfaga no espera al acumulado.** Existe un fast-trigger por milímetros en 30 minutos sobre terreno susceptible, independiente de la lluvia de 6–24 h.
5. **La alerta no se apaga de golpe.** Entre dos pasos de un escenario el índice puede subir libre, pero no cae más de 12 puntos.
6. **La demo corre sin red.** Los escenarios precargados alcanzan para el relato. Open-Meteo es contexto opcional y su calidad de dato queda por debajo de un pluviómetro de quebrada.
7. **Tests antes de dar por cerrado un cambio de riesgo.** Fast-trigger, suelo seco contra suelo cargado, silencio de sensores, memoria de la alerta y el orden cuenca-antes-que-casco tienen test en `engine/tests/`.
8. **Límites en voz alta.** La interfaz dice que el esquema no es cartografía oficial ni una orden de evacuación, y que Kirpich es un tiempo de concentración, no un modelo de colada.

## PUEDE

- Sumar sensores reales si entran por el mismo `Snapshot` (mm, mm/h, ráfaga de 30 min, suelo 0–1, edad del dato, calidad 0–1).
- Reemplazar el dibujo por un mapa cuando el GeoJSON deje de ser un esquema.

## Enmienda

Un cambio a esta constitución se escribe acá, en el mismo commit que la spec que lo necesita, y se menciona en el mensaje de commit.
