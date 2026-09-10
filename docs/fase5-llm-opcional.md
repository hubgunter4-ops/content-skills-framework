# Fase 5 — LLM opcional por API para decisiones estructuradas

## Objetivo

La Fase 5 añade `toolkit/llm.py`, un adaptador pequeño para proveedores compatibles con OpenAI Chat Completions. El adaptador complementa al router determinista; no reemplaza el índice, los contratos ni las políticas del runtime.

## Configuración

El usuario crea una configuración sin incluir el secreto:

```python
from toolkit import LLMProviderConfig, StructuredLLMProvider

config = LLMProviderConfig(
    provider="openai-compatible",
    model="modelo-configurado-por-el-usuario",
    base_url="https://proveedor.example/v1",
    api_key_env="FRAMEWORK_LLM_API_KEY",
    mode="suggest",
    timeout_seconds=20,
    max_input_tokens=8000,
    max_output_tokens=1000,
)
provider = StructuredLLMProvider(config)
```

La clave se lee únicamente desde `api_key_env` en el momento de la llamada. No se almacena en `LLMProviderConfig`, no se serializa y no se incorpora al prompt.

## Modos

| Modo | Resultado |
| --- | --- |
| `off` | No se llama al proveedor; el router determinista opera normalmente. |
| `suggest` | El LLM propone una selección; el router valida la candidata y crea un plan solo si no requiere confirmación. |
| `required` | La aplicación solicita el LLM y debe tratar un proveedor ausente como error explícito; esta primera integración conserva fallback seguro en el router para no ejecutar fuera de política. |

El modo recomendado para producción inicial es `suggest`, con el selector determinista como fallback.

## Salida estructurada

El adaptador solicita `response_format.type = json_schema` con un esquema estricto que exige:

- `selected_tool` nulo o una candidata;
- `confidence` entre 0 y 1;
- razones;
- alternativas;
- `requires_confirmation`.

La respuesta se valida localmente. Una herramienta que no pertenezca al conjunto de candidatas es rechazada y nunca se convierte en un `ExecutionPlan`.

## Integración con el router

```python
from pathlib import Path
from toolkit import DeterministicRouter, StructuredLLMProvider, ToolCache

cache = ToolCache(Path("."), Path(".content-skills-index.sqlite3"))
router = DeterministicRouter(Path("."), cache, llm_provider=provider)
decision = router.route("Valida este CSV y genera un informe")
```

El flujo es:

```text
Petición
  ↓
Normalización determinista
  ↓
Candidatas del índice SQLite
  ↓
LLM opcional: sugerencia estructurada
  ↓
Validación contra candidatas disponibles
  ↓
ToolSelection
  ↓
ExecutionPlan o confirmación
```

El LLM no puede añadir herramientas, modificar capacidades, desactivar controles o ejecutar scripts. El supervisor futuro continuará siendo la autoridad final.

## Seguridad y disponibilidad

El cliente:

- usa timeout configurable;
- convierte errores de red, HTTP, JSON y sistema en `ProviderUnavailableError`;
- no imprime payloads ni secretos;
- registra solo proveedor, modelo, latencia y uso de tokens en `LLMCallStats`;
- no realiza llamadas cuando falta la variable de clave;
- permite pruebas mediante un opener inyectable sin red.

Cuando el proveedor está ausente o falla, el router vuelve al selector determinista. Esta integración no activa credenciales por sí sola.

## Límites de esta fase

No se incluye todavía:

- streaming;
- carga automática de catálogo de modelos;
- reintentos complejos o circuit breaker del proveedor;
- ejecución de funciones del LLM;
- envío de payloads a proveedores sin una configuración explícita;
- selección basada exclusivamente en el LLM.
