# AGENTS.md

Contrato para cualquier asistente de código (Cursor, Copilot, Claude, Codex, Gemini u otro). No depende de un plugin. Si tu herramienta solo lee un archivo, es este.

## Antes de cambiar comportamiento

1. Leé `.specify/memory/constitution.md`. Un DEBE de la constitución no se negocia en el código.
2. Leé `.specify/feature.json` y abrí la spec activa: `spec.md`, después `plan.md` y `tasks.md`.
3. Si el cambio es comportamiento nuevo, actualizá o creá la spec antes de implementar. La spec dice qué y por qué. El plan dice cómo. Las tareas son la lista verificable.
4. Si el código y la spec se contradicen, no elijas en silencio. Parás y dejás la contradicción escrita.
5. El motor de riesgo vive en `engine/`. El panel no reimplementa el puntaje.

## Cómo se escribe una spec nueva

Copiá `.specify/templates/` a `specs/NNN-nombre-corto/` con el siguiente número libre. Completá `spec.md` sin elegir stack. Después `plan.md` y `tasks.md`. Apuntá `.specify/feature.json` a esa carpeta mientras esté en curso.

Marcadores:

- `DEBE` es obligatorio. Si no se cumple, el cambio no está listo.
- `PUEDE` es opcional.
- `[NEEDS CLARIFICATION]` es un hueco. No lo inventes.

## Verificar

```powershell
npm test
```

Los tests del motor son la compuerta del índice. Una spec de riesgo sin test que la fije no está cerrada.

## Qué no hacer

- No declares calma cuando el dato es viejo o de baja calidad.
- No bajes el índice para “compensar” un sensor malo.
- No presentes el esquema SVG ni el GeoJSON como cartografía oficial ni como orden de evacuación.
- No agregues un modelo opaco sin casos etiquetados y sin mantener el desglose en puntos.
