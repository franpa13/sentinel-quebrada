# Spec 005 — Chance de corte de la RN9

Estado: implementada en el motor. El panel no la muestra.

## Contexto

La RN9 es la única traza que une la Quebrada. El carnaval y las excursiones dependen de que siga abierta. Esta spec pide una lectura de chance de corte por lluvia o alud, armada con cortes publicados y con el índice de la semana. No es un parte de Vialidad ni una orden de cancelar la salida.

## Requisitos

### RF-26 Catálogo citado

`GET /ruta9/cortes` DEBE listar episodios con fecha, lugar, tipo y fuente. El catálogo es de prensa verificable. DEBE decir que no es el registro completo de Vialidad Nacional.

### RF-27 La lluvia manda

`GET /ruta9/semana` DEBE calcular un puntaje 0–100 con tres factores con nombre y puntos: lluvia de la semana, historia local y temporada. Historia y temporada DEBEN valer 0 si el índice de la semana es 0. Un punto a más de 25 km de la traza NO DEBE recibir una chance de corte de la RN9.

### RF-28 No se declara la ruta tranquila

Si la confianza de la grilla es baja y el puntaje físico queda en banda baja, el nivel operativo DEBE ser `atencion`.

### RF-29 Para quién

La frase DEBE hablar de excursión, turismo y de que un corte en la traza deja el pueblo sin salida. No DEBE presentarse como orden de cancelar.

## Fuera de alcance

- Cambiar `web/`.
- Inventar milímetros de los cortes viejos.
- Incluir la RN52 en la chance de la RN9.
