# Fase 3 — Caché en memoria y carga diferida

## Arquitectura

`toolkit/cache.py` implementa tres niveles sobre el índice SQLite de Fase 2:

| Nivel | Contenido | Política |
| --- | --- | --- |
| L1 | Resolución de `tool_id` a `IndexedTool` | LRU con capacidad configurable y TTL. |
| L2 | `ToolMetadata` y esquemas JSON cargados | LRU con clave compuesta por herramienta y `metadata_digest`. |
| L3 | Fábricas, adaptadores o workers | LRU pequeño; la carga requiere un callback explícito. |

La caché no escanea módulos ni carga plugins durante `resolve()`, `metadata()` o `schema()` salvo que el caller invoque explícitamente `factory()` con un loader.

## Consistencia e invalidación

Antes de acceder a los niveles, `ToolCache` llama a `ensure_index()`. Si la huella del entorno cambió, el índice SQLite se reconstruye y las tres capas se limpian.

Las entradas L2 y L3 incluyen el `metadata_digest` en su clave. Si el índice cambia para una herramienta, la nueva versión no puede reutilizar accidentalmente los metadatos, esquemas o fábricas de la versión anterior.

También se ofrece `invalidate(tool_id)` para invalidación selectiva y `clear()` para vaciar las capas completas.

## Métricas

`CacheStats` expone:

- hits y misses por nivel;
- tasa de aciertos global;
- desalojos LRU;
- invalidaciones;
- entradas residentes por nivel;
- estimación acumulada de bytes de metadatos y esquemas.

## Benchmark sintético

El script `docs/benchmarks/benchmark_cache.py` mide 5.000 lecturas sobre 304, 1.000, 5.000 y 10.000 herramientas sintéticas. El resultado de una ejecución local fue:

| Herramientas | Tiempo de 5.000 lookups | Lookups/segundo |
| ---: | ---: | ---: |
| 304 | 2.364 ms | 2,115,464.60 |
| 1.000 | 2.598 ms | 1,924,205.54 |
| 5.000 | 3.309 ms | 1,511,226.45 |
| 10.000 | 2.769 ms | 1,805,520.20 |

Estas cifras miden el LRU en memoria, no el coste de SQLite ni la carga de plugins; sirven para verificar que la resolución cacheada no crece linealmente con el catálogo. Deben repetirse en CI y en hardware representativo antes de usar umbrales operativos.

## Uso

```python
from pathlib import Path
from toolkit import ToolCache

cache = ToolCache(
    root=Path("."),
    index_path=Path(".content-skills-index.sqlite3"),
    l1_capacity=512,
    l2_capacity=512,
    l3_capacity=64,
    ttl_seconds=900,
)

record = cache.resolve("phase-2-datos/validacion-de-datos")
metadata = cache.metadata("phase-2-datos/validacion-de-datos")
output_schema = cache.schema("phase-2-datos/validacion-de-datos")
stats = cache.stats()
```

Para cargar una fábrica de plugin de forma diferida:

```python
factory = cache.factory(tool_id, loader=lambda indexed: load_after_policy_check(indexed))
```

El callback será responsabilidad del supervisor en fases posteriores y debe ejecutarse después de validar capacidades, cuotas y aislamiento.
