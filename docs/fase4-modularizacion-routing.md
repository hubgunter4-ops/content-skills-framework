# Fase 4 — Modularización por fases y enrutamiento

## Modularización

`toolkit/phases.py` define descriptores de fase sin duplicar el runtime. Cada descriptor contiene:

- identificador estable;
- nombre y descripción;
- paquete lógico de fase;
- cantidad esperada de herramientas;
- perfil de CPU, memoria, concurrencia y red;
- versión mínima del contrato.

El grupo de entry points para fases es:

```text
content_skills_toolkit.phases
```

La función `discover_phase_entry_points()` lee declaraciones de paquetes sin cargar sus objetos. `tools_for_phase()` conserva el registro unificado y permite filtrar por fase. Por tanto, la modularización separa instalación y políticas de recursos, pero mantiene un solo core y una sola API de contratos.

## Normalización

`RequestNormalizer` acepta texto libre u objeto JSON y produce `NormalizedRequest`. Normaliza:

- objetivo;
- audiencia;
- contenido;
- formato de salida;
- idioma;
- tipo de entrada;
- restricciones;
- etiquetas;
- selección manual, si existe.

El tipo de entrada puede inferirse desde el nombre de archivo (`csv`, `json`, `markdown`, `image`, `audio_video`) sin utilizar un LLM.

## Router determinista

`DeterministicRouter` utiliza el índice SQLite mediante `ToolCache`. La selección considera:

- coincidencia de tokens con identificador, nombre, descripción y etiquetas;
- tipo de entrada;
- formato de salida;
- fase solicitada;
- selección explícita del usuario;
- restricciones de confirmación.

Devuelve `RouteDecision` con:

- `NormalizedRequest`;
- `ToolSelection` explicable;
- candidatas alternativas;
- confianza;
- selector utilizado;
- `ExecutionPlan` cuando la ejecución puede planificarse sin confirmación.

Una herramienta seleccionada manualmente se valida contra el índice y la fase; nunca se ejecuta directamente desde el router. Una petición ambigua produce alternativas y `requires_confirmation = true`.

## CLI

Previsualizar una decisión sin ejecutar la herramienta:

```bash
python3 -m toolkit route "Convierte este Markdown a HTML para el equipo editorial"
```

Usar una petición JSON:

```bash
python3 -m toolkit route -i request.json --phase phase-2-datos
```

La salida es JSON y contiene la petición normalizada, la selección explicable y el plan. El comando no ejecuta runners ni plugins.

## LLM opcional

Esta fase implementa únicamente el camino determinista. El adaptador LLM definido en Fase 1 podrá complementar la normalización o proponer candidatas en una fase posterior, pero deberá entregar el mismo contrato `ToolSelection` y pasar por estos filtros antes de crear un plan.
