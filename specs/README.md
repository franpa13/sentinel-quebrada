# Specs

Desarrollo guiado por especificación, sin atarse a un asistente. El punto de entrada para cualquier IA es `AGENTS.md`.

| Spec | Estado | Qué fija |
| --- | --- | --- |
| [001-alerta-explicable](001-alerta-explicable/spec.md) | implementada | Índice, fast-trigger, margen, escenarios y panel |
| [002-lectura-en-vivo](002-lectura-en-vivo/spec.md) | implementada en el motor | Última lectura pública de un punto, sin tocar la fórmula |
| [003-consulta-por-lugar](003-consulta-por-lugar/spec.md) | implementada en el motor | Cualquier coordenada, los próximos 7 días, mismo índice |
| [004-suelos-satelite](004-suelos-satelite/spec.md) | implementada en el motor | Carta de suelos del INTA, cobertura del IGN y humedad SAOCOM |
| [005-corte-ruta9](005-corte-ruta9/spec.md) | implementada en el motor | Chance de corte de la RN9 para excursiones y logística |

La spec en curso está en `.specify/feature.json`. La próxima se copia desde `.specify/templates/`.
