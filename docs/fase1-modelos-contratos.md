# Fase 1 — Modelos y contratos públicos

## Propósito

La Fase 1 introduce una frontera estable entre la interfaz de peticiones, el runtime, las herramientas y los futuros plugins. Los modelos viven en `toolkit/models.py`, los errores en `toolkit/errors.py`, los validadores en `toolkit/contracts.py` y los esquemas en `toolkit/schemas/`.

## Modelos principales

| Modelo | Responsabilidad |
| --- | --- |
| `ToolMetadata` | Identidad, versión, contrato, capacidades, formatos y referencia de ejecución de una herramienta. |
| `ExecutionRequest` | Solicitud ya dirigida a una herramienta concreta. |
| `NormalizedRequest` | Petición del usuario convertida en objetivo, audiencia, contenido, formato, restricciones y etiquetas. |
| `ToolCandidate` | Herramienta candidata con puntuación y motivos. |
| `ToolSelection` | Decisión explicable, alternativas y necesidad de confirmación. |
| `ExecutionStep` | Un paso de ejecución de herramienta. |
| `ExecutionPlan` | Uno o más pasos ordenados; los planes compuestos pueden exigir confirmación. |
| `LLMProviderConfig` | Configuración no secreta del proveedor LLM opcional. Solo guarda el nombre de la variable de entorno de la clave. |
| `ExecutionResult` | Resultado común con estado, análisis, entregable, advertencias, trazabilidad y error opcional. |

## Estados públicos

```text
ready
needs_input
not_loaded
error
timeout
quota_exceeded
circuit_open
worker_crashed
```

Los estados `quota_exceeded`, `circuit_open`, `timeout` y `worker_crashed` se definen desde ahora para que las capas futuras no tengan que inventar respuestas incompatibles.

## Regla de ejecución

`ToolMetadata` exige al menos una referencia ejecutable: `script` o `entrypoint`. Durante la migración, las herramientas existentes pueden declarar un script `run.py`. Los plugins futuros podrán declarar un entry point que produzca un adaptador con `execute()`.

La interfaz de peticiones no ejecuta código directamente. Su salida es un `NormalizedRequest`, una `ToolSelection` o un `ExecutionPlan`. El supervisor será responsable de convertir el plan en un `ExecutionRequest` y de ejecutar el script o worker correspondiente.

## LLM opcional

El LLM se modela con `LLMProviderConfig` y tres modos:

| Modo | Comportamiento |
| --- | --- |
| `off` | No se llama a ningún LLM; se usa selección determinista. |
| `suggest` | El LLM propone normalización o candidatas; el runtime valida y decide. |
| `required` | La aplicación solicita LLM, pero una respuesta inválida o no disponible sigue produciendo un error explícito; no se ejecuta una herramienta fuera de política. |

La configuración contiene `api_key_env`, no el secreto. La implementación futura debe cargar la clave solo en el adaptador del proveedor y nunca incluirla en serializaciones, logs o resultados.

## Compatibilidad

Los esquemas usan JSON Schema 2020-12 y `contract_version = "1.0"`. Los modelos no importan integraciones ni plugins durante la importación. La suite existente del toolkit continúa ejecutándose sin cambios.

## Validación actual

La función `validate_schema_documents()` comprueba la presencia de los siete esquemas públicos y su dialecto JSON Schema. `validate_metadata_dict()` y `validate_result_dict()` proporcionan una validación ligera sin dependencias externas; una validación exhaustiva de JSON Schema podrá añadirse como dependencia opcional en una fase posterior.
