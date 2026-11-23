# Sentinel Quebrada

Motor de alerta temprana aluvional para Volcán (Jujuy). No pronostica el clima: con telemetría —o con un escenario precargado— dice cuándo se cruzan umbrales, qué término armó el índice y cuántos minutos de margen quedan antes de que el pulso se organice aguas abajo.

El 10 de enero de 2017 un aluvión cortó la RN 9 y afectó Volcán, Bárcena y Tumbaya. Este MVP no reconstruye ese evento. Usa la geografía del cono de deyección para ensayar una alerta que llegue antes del pico de escurrimiento.

## Qué hay en la demo

1. **Escenarios sin red.** Calma, acumulado lento, pico en cuenca alta y silencio de sensores. El pico es el relato de un minuto: arriba ya hay fast-trigger y el casco todavía no recibió el pulso.
2. **Esquema de zonas.** Cuenca alta, cauce, cono de deyección, casco, accesos y RN 9, pintados verde / amarillo / naranja / rojo. Hay un GeoJSON del mismo esquema en `GET /zones.geojson` para el día que se suba a un mapa.
3. **Alerta explicable.** Índice 0–100, factores en puntos, confianza del dato y margen de reacción.

## Specs para cualquier asistente

El comportamiento está fijado en `specs/`, no en el chat. `AGENTS.md` es el punto de entrada: lo leen Cursor, Copilot, Claude, Codex, Gemini u otro. La constitución está en `.specify/memory/constitution.md`. La spec activa está en `.specify/feature.json`.

Una feature nueva se escribe antes de codear: se copia `.specify/templates/` a `specs/NNN-nombre/` y se completa spec, plan y tareas.

## Stack

| Pieza | Tecnología | Por qué |
| --- | --- | --- |
| Ciencia y reglas | Python 3.15 | Ahí viven el índice, los escenarios y los tests. Es lo que se calibra cuando haya eventos etiquetados. |
| API | FastAPI | Contrato único para el panel, para Open-Meteo y para un pluviómetro futuro. |
| Panel | Next.js + React + Tailwind | Una pantalla de demo, perillas y reproducción. |
| Mapa de la demo | SVG | No depende de teselas ni de red. El fallo de conectividad no mata el pitch. |
| Contrato geográfico | GeoJSON | Mismo esquema, listo para MapLibre cuando haga falta una base real. |

No hay un modelo de caja negra. Sin una serie etiquetada de aludes, un random forest sería indefendible delante del jurado. Los pesos son el contrato: cuando existan casos, se calibran sin cambiar lo que el panel explica.

## Innovaciones que ya corren

- **Fast-trigger.** Una ráfaga de 30 minutos en terreno susceptible pone un piso al índice (58 / 76 / 88) aunque el acumulado de 6–24 h siga bajo.
- **Índice aditivo.** Lluvia acumulada, intensidad y ráfaga se multiplican por humedad del suelo (×0.45 a ×1) y por susceptibilidad del tramo (×0.50 a ×1). Cada punto tiene dueño.
- **Cascada.** En el pico, intensidad y ráfaga bajan con retardo de la cuenca alta hacia el cono, el casco y la RN 9. El mapa se enciende arriba primero.
- **Memoria de la alerta.** De un paso al siguiente el índice puede subir libremente, pero no cae más de 12 puntos. Un claro de diez minutos no la apaga.
- **Silencio de sensores.** Un dato viejo no baja el riesgo. Si no alcanza para declarar calma, el nivel operativo no se queda en verde.
- **Margen de Kirpich.** `Tc (min) = 0.0195 · L^0.77 · S^-0.385`. Es tiempo de concentración del tramo, no un modelo de flujo de detritos.
- **Open-Meteo con techo de confianza.** La grilla (~10 km) puede entrar como contexto. La calidad queda fija en 0.40 para que un pronóstico lindo no pinte calma en la quebrada.
- **Perillas de un solo pluviómetro.** Mover la ráfaga simula el instrumento de cuenca alta; aguas abajo el pulso llega atenuado (`coupling`).

## Cómo correrlo

Hace falta Node 22 y Python 3.15. La primera vez:

```powershell
.\scripts\setup.ps1
```

La demo, API en el puerto 8000 y panel en el 3000:

```powershell
npm run dev
```

Tests del motor:

```powershell
npm test
```

Si preferís dos terminales:

```powershell
engine\.venv\Scripts\python.exe -m uvicorn sentinel.api:app --app-dir engine --reload --port 8000
npm run dev --prefix web
```

Abrí http://localhost:3000. El escenario de arranque es **Pico en cuenca alta**, en el primer paso (todavía en verde). Reproducí hasta que la cuenca cruce a rojo y hacé clic en el casco: el margen es el argumento.

## Datos

Conectado ahora:

- Escenarios locales en `engine/sentinel/scenarios.py`.
- `GET /context/open-meteo` (Volcán, aprox. -23.919, -65.463), como contexto de grilla.
- `GET /context/lugar?lat=&lon=` arma la última lectura pública de esa coordenada y la puntúa. Si no se pasan coordenadas, sigue siendo Volcán. Las zonas del esquema solo entran cuando el punto cae dentro. El panel todavía no la dibuja.
- `GET /consulta/semana?lat=&lon=` puntúa los próximos 7 días de cualquier lugar. La carta del INTA, la cobertura del IGN y SAOCOM pueden subir la susceptibilidad o la humedad; no las bajan.
- `GET /ruta9/cortes` lista cortes de la RN9 por lluvia o alud, con la nota de prensa. `GET /ruta9/semana?lat=&lon=` dice la chance de que esa semana el barro corte la ruta en ese punto de la Quebrada. Es para excursiones y para la logística que no tiene otra salida. No es un parte de Vialidad ni una orden de cancelar.
- `GET /ruta9/pueblos` lista los pueblos de la traza de sur a norte, con la geometría real de la RN9 (OpenStreetMap, en `engine/sentinel/traza_rn9.py`) y el kilómetro de cada pueblo. `GET /ruta9/viaje?desde=&hasta=` arma el viaje día por día: cada día manda el pueblo más comprometido del tramo y se marca el día más tranquilo para salir. Es la vista **¿Se corta la ruta?** del panel (spec 006); la simulación de la cuenca quedó en la pestaña **Cuenca de Volcán**.

Para después, sin prometerlo en la demo:

- Pluviómetros y humedad en el mismo `Snapshot` (mm, mm/h, ráfaga de 30 min, suelo 0–1, edad del dato).
- Alertas del Servicio Meteorológico Nacional como otra capa de contexto, con el mismo techo de confianza que Open-Meteo.
- Cursos de agua de OpenStreetMap o del IGN para reemplazar el esquema. El GeoJSON ya sale por la API.

Los umbrales son de trabajo para el hackathon. Hay que contrastarlos con eventos reales antes de usarlos en una guardia.

## Reparto sugerido

- **Frontend, mapa, UI** — `web/`. El esquema está en el panel; el GeoJSON sale de la API.
- **Modelo, datos, simulación** — `engine/`. Índice, escenarios, Open-Meteo y tests.
- **Pitch, narrativa, validación** — el texto de abajo y los cuatro escenarios. Quien valide tiene que poder decir, con el panel abierto, qué término subió el índice.

## Pitch de tres minutos

- **0:30 Problema.** Volcán está sobre un cono de deyección, al pie de quebradas de fuerte pendiente. El golpe duele más cuando lo que pasa arriba llega tarde.
- **0:45 Solución.** Un motor de reglas explicables. No adivina la tormenta: detecta el cruce de umbrales y dice el margen.
- **1:00 Demo.** Reproducí *Pico en cuenca alta*. Paren cuando la cuenca esté en rojo y el casco siga abajo. Muestren los puntos del fast-trigger y el margen en minutos. Si queda un segundo, suban la edad del dato: el verde no sobrevive a un sensor mudo.
- **0:45 Cierre.** Sirve a Defensa Civil y al municipio como mesa de situación. Escala con un pluviómetro real porque el contrato del dato ya está. No reemplaza la decisión humana ni una orden de evacuación.

## Límites, dichos en voz alta

- El dibujo no es un mapa de evacuación.
- Kirpich no modela una colada de barro y piedra.
- Open-Meteo no ve la quebrada.
- Nadie debería evacuar por este prototipo.
