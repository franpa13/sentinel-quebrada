# Spec 006 — ¿Se corta la ruta? Viaje por la RN9

Estado: implementada en el motor y mostrada en el panel.

## Contexto

La spec 005 da una chance de corte por punto y por semana. Quien viaja no pregunta eso: pregunta "salgo de Volcán y voy a Tilcara, ¿qué día me conviene?". Un corte en cualquier pueblo del medio corta el viaje entero. Esta spec arma esa lectura en el motor y le da al panel una vista propia, separada de la simulación de la cuenca.

## Requisitos

### RF-31 Chance por día

`GET /ruta9/semana` DEBE devolver `days`: para cada día de la grilla, la chance de corte calculada con la misma regla de la spec 005 (`evaluar_corte`), usando el índice de ese día en lugar del pico de la semana. Cada día DEBE traer sus factores con nombre y puntos. Un día sin milímetros DEBE tener `chance` nula y nivel operativo `atencion`.

### RF-32 Pueblos de la traza

`GET /ruta9/pueblos` DEBE listar los pueblos de la RN9 de sur a norte, con coordenadas y la cantidad de episodios publicados a menos de 15 km. El panel DEBE tomar la lista de ahí, no de una copia propia.

### RF-33 Viaje de un pueblo a otro

`GET /ruta9/viaje?desde=&hasta=` DEBE consultar cada pueblo del tramo, extremos incluidos. Para cada día:

- La chance del viaje DEBE ser la del pueblo más comprometido ese día, y DEBE nombrar ese pueblo. No es una suma ni una probabilidad combinada, y el motor lo DEBE decir en los límites.
- El nivel operativo del viaje DEBE ser el peor de los pueblos (orden: baja, atención, media, alta, muy alta).
- Si algún pueblo no trajo dato ese día, el viaje NO DEBE quedar en `baja`: pasa a `atencion` como mínimo.

El motor DEBE marcar el mejor día para salir: el de menor chance del viaje entre los días con dato en todos los pueblos. Si ninguno califica, no hay mejor día. DEBE devolver los cortes publicados a menos de 15 km de algún pueblo del tramo.

La frase DEBE hablar de quien viaja y NO DEBE presentarse como orden de cancelar ni como parte de Vialidad.

### RF-34 Una vista para quien viaja

El panel DEBE abrir en la vista de viaje, con Volcán como salida y llegada, y preguntar en orden: de dónde sale, a dónde va y qué día viaja. La respuesta DEBE aparecer recién cuando la persona eligió el día; la pregunta del día muestra solo fechas, sin adelantar el resultado. DEBE dejar:

- elegir salida y llegada sobre la traza;
- ver los 7 días con la chance del viaje y el mejor día marcado;
- tocar un día y ver la traza pintada por pueblo con la chance de ese día;
- tocar un pueblo y ver los factores de ese día y los cortes publicados cerca;
- ver los cortes publicados del tramo agrupados por mes, con el mes de hoy marcado, y filtrar la lista por mes.

Todo número que muestre DEBE ser del motor. La simulación de la cuenca de Volcán DEBE seguir disponible en otra pestaña.

### RF-35 Lenguaje de cualquier persona

La vista de viaje DEBE responder primero en palabras, no en puntos: cada nivel del motor se traduce a una frase (poco probable, posible, probable, muy probable) con ícono y color. `atencion` NO DEBE leerse como "libre": dice que no hay señales pero que hay que confirmar. El puntaje 0–100, los factores y el historial completo quedan a un toque, en "por qué". La vista DEBE decir qué hacer antes de salir sin presentarlo como orden ni inventar teléfonos o umbrales.

## Enmienda a la spec 005

RF-30 pedía abrir con la lectura de Volcán y elegir un pueblo tocando la traza. La vista de viaje lo cumple con salida y llegada en Volcán. La lectura de la ruta deja de convivir con el esquema de la cuenca: el dibujo de Volcán no se muestra al lado de la ruta de otro pueblo.

## Fuera de alcance

- Probabilidad estadística combinada del tramo.
- Rutas alternativas (RN52, caminos vecinales).
- Estado de transitabilidad en tiempo real.
