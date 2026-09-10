# Arquitectura de caché, sandboxing y organización por fases

**Solicitud identificable:** caché e índice persistente para entry points, aislamiento de plugins, cuotas y evaluación del modelo por fases  
**Repositorio de referencia:** [Content Skills Toolkit][1]  
**Fecha:** 9 de septiembre de 2026  
**Autor:** **Manus AI**

## 1. Recomendación ejecutiva

Sí es viable organizar el framework por fases o módulos, porque las seis fases actuales ya agrupan herramientas con objetivos comunes. Sin embargo, no conviene convertir cada fase en un framework completamente independiente. La opción más robusta es una arquitectura **híbrida**:

```text
content-skills-core
├── runtime común
├── contratos y validadores
├── caché e índice global
├── scheduler y cuotas
├── sandbox de procesos
└── API pública

módulos de dominio
├── content-toolkit
├── datos
├── programming
├── automatizacion
├── negocios
└── medios
```

Cada fase debe comportarse como un **módulo instalable y registrable**, pero compartir el mismo runtime, los mismos contratos, la misma política de seguridad y el mismo sistema de cuotas. Esto evita duplicar infraestructura y mantiene una experiencia uniforme.

Para las 304 herramientas actuales, el descubrimiento debe dividirse en dos caminos:

1. **Índice persistente:** permite resolver una herramienta sin volver a inspeccionar todas las distribuciones instaladas.
2. **Caché en memoria:** permite resolver repetidamente una herramienta sin leer disco ni reconstruir objetos.

La caché no debe considerarse una fuente de verdad. La fuente de verdad son los metadatos de las distribuciones instaladas y el contenido de los paquetes. El índice se puede invalidar y reconstruir.

## 2. Objetivos y límites

### Objetivos

- Reducir el coste de `list`, `show` y resolución de herramientas.
- Evitar importar módulos de plugins durante el arranque.
- Detectar cambios de instalación, actualización o eliminación de plugins.
- Mantener consistencia entre metadatos, esquemas y distribución.
- Aislar plugins de terceros del proceso principal.
- Evitar que un plugin consuma todos los recursos del host.
- Permitir despliegues por fase sin duplicar el runtime.

### Límites

- El sandboxing no convierte automáticamente en confiable un plugin malicioso.
- Un proceso separado reduce el impacto, pero no sustituye los permisos del sistema operativo o de un contenedor.
- La caché no debe almacenar secretos ni payloads de usuario por defecto.
- La ejecución de plugins con capacidades de red o escritura requiere políticas adicionales.

## 3. Diseño del índice persistente

### 3.1 Información que debe indexarse

El índice debe contener únicamente metadatos necesarios para descubrimiento y validación ligera. No debe almacenar objetos Python cargados ni el contenido completo de cada `SKILL.md`.

| Campo | Propósito |
| --- | --- |
| `tool_id` | Identificador cualificado, por ejemplo `community/analizador-de-legibilidad`. |
| `entry_point_name` | Nombre publicado en el grupo de entry points. |
| `group` | Grupo de plugins, por ejemplo `content_skills_toolkit.tools`. |
| `distribution` | Paquete que proporciona la herramienta. |
| `distribution_version` | Versión instalada del paquete. |
| `object_ref` | Referencia, por ejemplo `plugin:create_tool`. |
| `metadata_digest` | Hash de metadatos y recursos contractuales. |
| `contract_version` | Versión del contrato del framework. |
| `tool_version` | Versión propia de la herramienta. |
| `capabilities` | Capacidades declaradas. |
| `schema_refs` | Referencias a esquemas de entrada y salida. |
| `status` | `available`, `invalid`, `disabled` o `conflict`. |
| `indexed_at` | Fecha de construcción del registro. |
| `runtime_range` | Versiones del runtime compatibles. |

No debe guardarse en el índice la fábrica ya importada. El índice debe ser serializable, inspeccionable y seguro de regenerar.

### 3.2 Formato recomendado

Para 304 herramientas, SQLite es una mejor base que un JSON monolítico si se quiere evolucionar a miles de plugins. SQLite aporta consultas indexadas, transacciones atómicas y actualización incremental sin añadir un servicio externo.

Una tabla mínima podría ser:

```sql
CREATE TABLE tools (
    tool_id TEXT PRIMARY KEY,
    entry_point_name TEXT NOT NULL,
    entry_point_group TEXT NOT NULL,
    distribution TEXT NOT NULL,
    distribution_version TEXT NOT NULL,
    object_ref TEXT NOT NULL,
    metadata_digest TEXT NOT NULL,
    contract_version TEXT NOT NULL,
    tool_version TEXT NOT NULL,
    capabilities_json TEXT NOT NULL,
    input_schema_ref TEXT NOT NULL,
    output_schema_ref TEXT NOT NULL,
    status TEXT NOT NULL,
    indexed_at TEXT NOT NULL,
    runtime_range TEXT NOT NULL
);

CREATE INDEX idx_tools_distribution ON tools(distribution);
CREATE INDEX idx_tools_status ON tools(status);
CREATE INDEX idx_tools_entry_group ON tools(entry_point_group);
```

También debe existir una tabla de estado del inventario:

```sql
CREATE TABLE registry_state (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
```

Claves recomendadas:

- `python_executable`;
- `python_version`;
- `environment_fingerprint`;
- `entry_points_fingerprint`;
- `framework_contract_version`;
- `last_full_scan`.

### 3.3 Ubicación y atomicidad

El índice debe vivir fuera del repositorio de código, en una ruta de caché del usuario o del entorno de ejecución. La ruta debe poder configurarse mediante `TOOLKIT_INDEX_PATH` o una opción equivalente.

La reconstrucción debe ser atómica:

1. Crear una base temporal en el mismo directorio.
2. Escanear las distribuciones y validar metadatos.
3. Insertar registros y construir índices.
4. Ejecutar `PRAGMA integrity_check`.
5. Cerrar la base temporal.
6. Cambiarla a la ruta activa con `os.replace`.

No debe modificarse una base activa mientras otro proceso la está leyendo. Si existe concurrencia entre lectores y un escritor, SQLite en modo WAL puede ayudar, pero la sustitución completa del archivo sigue siendo más sencilla para un índice reconstruible.

## 4. Detección de cambios e invalidación

### 4.1 Huella del entorno

El índice debe invalidarse cuando cambie cualquiera de estos componentes:

```text
fingerprint = SHA-256(
    python_executable
    + python_version
    + framework_contract_version
    + distribution_name
    + distribution_version
    + distribution_location
    + entry_point_group
    + entry_point_name
    + object_ref
)
```

No es necesario recalcular el hash del contenido completo de todos los archivos en cada arranque. Para una comprobación rápida se puede usar la lista de distribuciones instaladas, sus versiones, ubicaciones y entry points. La validación profunda de recursos puede ejecutarse solo cuando cambie esa huella o cuando se solicite `validate --all`.

### 4.2 Algoritmo de arranque

```python
from dataclasses import dataclass
from importlib.metadata import distributions, entry_points
from pathlib import Path
import hashlib
import json
import sqlite3

GROUP = "content_skills_toolkit.tools"


def installed_fingerprint() -> str:
    rows = []
    for distribution in distributions():
        rows.append({
            "name": distribution.metadata.get("Name", ""),
            "version": distribution.version,
            "location": str(distribution.locate_file("")),
        })
    rows.sort(key=lambda row: (row["name"].lower(), row["version"], row["location"]))
    payload = json.dumps(rows, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()


def ensure_index(path: Path) -> sqlite3.Connection:
    fingerprint = installed_fingerprint()
    if not index_is_current(path, fingerprint):
        rebuild_index_atomically(path, fingerprint)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    return connection
```

El ejemplo es esquemático. En producción, `rebuild_index_atomically` debe descubrir entry points sin invocar las fábricas, extraer metadatos declarativos y rechazar entradas inconsistentes.

### 4.3 Tres niveles de validación

| Momento | Validación | Coste esperado |
| --- | --- | ---: |
| Arranque | Huella del entorno e integridad SQLite | Bajo |
| Primera selección | Carga de fábrica, metadatos y esquemas del plugin | Medio |
| CI o auditoría | Documentación, runner, esquemas, capacidades y pruebas | Alto |

Este modelo evita pagar la validación completa de 304 herramientas cada vez que el usuario ejecuta una sola.

## 5. Caché en memoria

### 5.1 Capas de caché

Se recomienda utilizar tres niveles, con responsabilidades diferentes:

```text
L1: resolución de identificador
    tool_id -> IndexedToolRecord

L2: metadatos y esquemas
    tool_id + digest -> ToolMetadata + compiled schemas

L3: fábrica o worker
    tool_id -> loaded factory / persistent worker handle
```

La L1 debe ser pequeña y de larga duración. La L2 puede usar caché limitada porque los esquemas pueden ser grandes. La L3 debe ser la más restrictiva, ya que mantener módulos cargados o workers persistentes consume memoria y recursos.

### 5.2 Política recomendada

- `list --brief` usa solo el índice persistente y L1.
- `show` carga `SKILL.md` bajo demanda y puede usar una caché LRU.
- `validate_input` carga y compila solo el esquema seleccionado.
- `execute` carga la fábrica o asigna un worker.
- Los plugins que no se usan durante un periodo configurable se desalojan de L3.
- Los resultados de usuario no se guardan en caché salvo solicitud explícita.

### 5.3 Caché LRU de metadatos

```python
from functools import lru_cache


@lru_cache(maxsize=512)
def load_tool_metadata(tool_id: str, metadata_digest: str):
    record = index_lookup(tool_id)
    if record.metadata_digest != metadata_digest:
        raise RuntimeError("Registro obsoleto")
    return load_and_validate_metadata(record)
```

El `metadata_digest` forma parte de la clave para evitar devolver metadatos antiguos después de una actualización.

Para esquemas compilados, se recomienda una caché separada:

```python
@lru_cache(maxsize=256)
def compile_schema(schema_ref: str, schema_digest: str):
    schema = read_schema(schema_ref)
    validate_schema_document(schema)
    return compile_validator(schema)
```

El número de entradas debe medirse. La capacidad correcta depende del tamaño medio de los esquemas y del número de workers. Un valor fijo como 256 es solo un punto inicial.

### 5.4 Caché entre procesos

La caché en memoria no se comparte automáticamente entre procesos. Hay tres opciones:

| Opción | Uso recomendado |
| --- | --- |
| Caché independiente por worker | CLI, baja complejidad y cargas moderadas. |
| Índice SQLite compartido | Metadatos y resolución de herramientas. |
| Servicio de caché externo | Solo cuando exista una arquitectura multi-host con alta concurrencia. |

Para 304 herramientas no se justifica introducir Redis únicamente para descubrimiento. SQLite persistente más caché LRU local ofrece menor complejidad y suficiente rendimiento.

## 6. Registro por fase o módulo

### 6.1 ¿Es viable?

Sí. Las fases actuales tienen cohesión temática y ya poseen motores diferenciados. Por ejemplo, Datos concentra análisis y validación; Programming concentra herramientas de desarrollo; Automatización concentra flujos y ejecución; Negocios concentra procesos de negocio; y Medios concentra capacidades multimedia.

La modularización por fase tiene ventajas:

| Ventaja | Explicación |
| --- | --- |
| Menor superficie instalada | Una aplicación puede instalar solo las fases que necesita. |
| Mejor propiedad del dominio | Cada módulo puede mantener sus adaptadores y documentación. |
| Actualizaciones independientes | Una fase puede evolucionar sin publicar todo el catálogo. |
| Aislamiento de dependencias | Un módulo de medios puede requerir dependencias que Datos no necesita. |
| Mejor organización de CI | Las pruebas se pueden ejecutar por módulo y por contrato común. |
| Política de capacidades más clara | Las fases pueden declarar perfiles de recursos. |

También existen riesgos:

- duplicación de lógica de registro, seguridad y validación;
- incompatibilidades entre versiones de módulos;
- conflictos de identificadores;
- dificultad para ejecutar flujos que combinan fases;
- experiencia inconsistente si cada fase implementa su propio CLI;
- mayor coste de empaquetado y soporte.

### 6.2 Modelo recomendado

No usaría seis runtimes diferentes. Usaría:

```text
content-skills-core                  # obligatorio
content-skills-phase-content         # catálogo de Fase 1
content-skills-phase-data            # Fase 2
content-skills-phase-programming     # Fase 3
content-skills-phase-automation      # Fase 4
content-skills-phase-business        # Fase 5
content-skills-phase-media           # Fase 6
```

Cada paquete de fase publica entry points en el mismo grupo:

```toml
[project.entry-points."content_skills_toolkit.tools"]
validacion-de-datos = "phase_data.tools:build_validacion"
```

Además, cada paquete de fase puede publicar metadatos del módulo en otro grupo:

```toml
[project.entry-points."content_skills_toolkit.phases"]
data = "phase_data.module:get_phase"
```

El runtime mantiene un solo índice global, pero permite filtros:

```bash
content-skills list --phase data
content-skills validate --phase data
content-skills run data/validacion-de-datos --input request.json
```

El identificador completo debe incluir el módulo o namespace. No conviene depender solo de `validacion-de-datos`, porque un ecosistema grande puede tener colisiones.

### 6.3 Cuándo separar físicamente una fase

Una fase debe convertirse en un paquete independiente cuando cumpla al menos dos de estas condiciones:

1. Tiene dependencias específicas de tamaño significativo.
2. Tiene un ciclo de releases distinto.
3. Es mantenida por un equipo diferente.
4. Puede instalarse y probarse de manera autónoma.
5. Tiene un perfil de seguridad o recursos diferente.
6. Tiene usuarios que no necesitan las demás fases.

La separación física no debe hacerse solo porque una carpeta tiene muchas herramientas. La cohesión y la independencia operativa son criterios más importantes.

## 7. Sandboxing de procesos

### 7.1 Principio de confianza

Un plugin de terceros debe considerarse **código no confiable por defecto**. El entry point solo permite descubrir y cargar una referencia; no proporciona aislamiento. El runtime debe decidir dónde ejecutar la herramienta según su procedencia, capacidades declaradas y política local.

Perfiles recomendados:

| Perfil | Condición | Backend |
| --- | --- | --- |
| `trusted-pure` | Código integrado, auditado y sin capacidades externas | En proceso o worker compartido. |
| `trusted-io` | Plugin auditado que necesita archivos o red limitada | Worker persistente con límites. |
| `third-party` | Plugin instalado desde una distribución externa | Subproceso dedicado o pool aislado. |
| `untrusted` | Plugin no revisado o con capacidades elevadas | Contenedor o sandbox fuerte. |

### 7.2 Proceso supervisor y worker

La arquitectura recomendada es un supervisor que nunca importe ni ejecute directamente plugins no confiables:

```text
Host API
   |
   v
Supervisor de ejecución
   |-- valida contrato y capacidades
   |-- aplica cuotas
   |-- crea o reutiliza worker
   |-- controla timeout y tamaño
   |-- redacciona errores
   |
   +--> Worker aislado del plugin
           |-- importa el entry point
           |-- recibe JSON por stdin o IPC
           |-- ejecuta una solicitud
           |-- devuelve JSON por stdout o IPC
```

El protocolo inicial puede ser JSON Lines:

```json
{"request_id":"r-123","tool_id":"community/analizador-de-legibilidad","payload":{}}
```

La respuesta debe incluir el mismo `request_id`:

```json
{"request_id":"r-123","status":"ready","analysis":{},"warnings":[]}
```

No se debe mezclar logging con stdout del protocolo. Los logs deben ir a stderr o a un canal estructurado independiente.

### 7.3 Ciclo de vida del worker

1. El supervisor consulta el índice.
2. Comprueba el estado del plugin y sus capacidades.
3. Selecciona el perfil de aislamiento.
4. Crea un worker con un entorno mínimo.
5. Pasa solo la configuración permitida.
6. Envía una solicitud con `request_id` y deadline.
7. Lee la respuesta limitada por tamaño.
8. Valida la salida contra el esquema.
9. Registra métricas sin payload sensible.
10. Reutiliza o destruye el worker según la política.

Un worker persistente reduce el coste de importar dependencias pesadas, pero debe reiniciarse después de un número máximo de ejecuciones, una excepción no controlada, una fuga detectada o un cambio de versión.

### 7.4 Límites del proceso

El supervisor debe aplicar, como mínimo:

- timeout total de ejecución;
- timeout de lectura y escritura IPC;
- límite de bytes recibidos;
- límite de memoria;
- límite de CPU;
- límite de procesos hijos;
- límite de archivos abiertos;
- directorio de trabajo temporal;
- entorno de variables filtrado;
- lista explícita de capacidades de red;
- límite de conexiones y tamaño de respuesta.

En Linux, un primer nivel puede utilizar `resource.setrlimit`, `os.setsid`, un directorio de trabajo temporal y un entorno limpio. Para plugins verdaderamente no confiables se recomienda un contenedor sin privilegios o una tecnología de sandbox del sistema operativo. Un subproceso por sí solo no impide que un plugin lea archivos para los que el usuario del proceso ya tiene permisos.

### 7.5 Sistema de archivos

El worker debe recibir un workspace temporal específico:

```text
/tmp/content-skills/runs/r-123/
├── input/       # solo lectura cuando sea posible
├── output/      # escritura limitada
└── metadata/    # contrato y configuración no secreta
```

El plugin no debe recibir el workspace completo del host. Las rutas deben normalizarse y verificarse contra el directorio permitido para evitar traversal. Los archivos de entrada grandes deben montarse o transmitirse según el tipo de herramienta, sin duplicarlos innecesariamente.

### 7.6 Red y credenciales

La red debe estar deshabilitada por defecto. Si una herramienta declara `network`, el supervisor debe validar:

- proveedor autorizado;
- dominios permitidos;
- método y timeout;
- cuota de solicitudes;
- tamaño máximo de respuesta;
- credencial específica del proveedor;
- redacción de la credencial en errores y logs.

No se debe pasar todo el entorno del host al worker. El supervisor debe construir un entorno mínimo con las variables estrictamente necesarias.

## 8. Control de cuotas

### 8.1 Dimensiones de cuota

Las cuotas no deben limitar solo el número de invocaciones. Deben cubrir recursos distintos:

| Dimensión | Ejemplo |
| --- | --- |
| Concurrencia | Máximo de workers activos por plugin y fase. |
| CPU | Segundos de CPU por ejecución y por ventana temporal. |
| Memoria | Límite de memoria por worker. |
| Tiempo | Deadline total y tiempo máximo en cola. |
| Entrada | Bytes máximos del payload y archivos. |
| Salida | Bytes máximos de respuesta y artefactos. |
| Red | Solicitudes, bytes y dominios por ventana. |
| Procesos | Número de subprocesos hijos permitidos. |
| Disco | Espacio temporal y número de archivos. |
| Proveedor | Cuota por API, credencial, fase o tenant. |

### 8.2 Configuración declarativa

```toml
[quotas.defaults]
max_concurrency = 4
max_wall_time_seconds = 30
max_output_bytes = 5_000_000
max_input_bytes = 10_000_000
max_memory_mb = 512
max_cpu_seconds = 20
network = false

[quotas.phase.data]
max_concurrency = 8
max_wall_time_seconds = 120

[quotas.plugin."community/analizador-de-legibilidad"]
max_concurrency = 2
max_wall_time_seconds = 10
max_memory_mb = 128
network = false
```

La política efectiva debe calcularse de forma restrictiva:

```text
cuota efectiva = mínimo(
    cuota global,
    cuota de fase,
    cuota de plugin,
    cuota del usuario o tenant,
    capacidad real del host
)
```

### 8.3 Token bucket para invocaciones y red

Para solicitudes por ventana temporal se puede utilizar un token bucket:

```python
class TokenBucket:
    def __init__(self, capacity: int, refill_per_second: float):
        self.capacity = capacity
        self.tokens = float(capacity)
        self.refill_per_second = refill_per_second
        self.updated_at = monotonic()

    def take(self, cost: int = 1) -> bool:
        now = monotonic()
        elapsed = now - self.updated_at
        self.tokens = min(
            self.capacity,
            self.tokens + elapsed * self.refill_per_second,
        )
        self.updated_at = now
        if self.tokens < cost:
            return False
        self.tokens -= cost
        return True
```

Cada plugin puede tener un bucket de invocaciones, otro de bytes de salida y otro de solicitudes de red. La implementación real debe ser segura frente a concurrencia y debe decidir si rechaza inmediatamente o espera en cola.

### 8.4 Fairness y backpressure

Una cola global sin prioridades permite que una fase ruidosa bloquee a las demás. Se recomienda:

- cola por fase;
- límite de concurrencia por plugin;
- cuota global del host;
- prioridad para solicitudes interactivas frente a trabajos batch;
- rechazo temprano cuando no existe capacidad;
- circuit breaker después de errores repetidos;
- métricas de tiempo en cola separadas del tiempo de ejecución.

La respuesta ante una cuota excedida debe ser explícita, por ejemplo `quota_exceeded`, y debe incluir la dimensión afectada sin revelar datos internos innecesarios.

## 9. Integración entre caché, fases y sandbox

El flujo completo recomendado es:

```text
1. Resolver tool_id desde L1 o SQLite.
2. Confirmar estado y versión desde el índice.
3. Cargar metadatos y esquema desde L2.
4. Calcular capacidades y cuota efectiva.
5. Seleccionar fase y backend de ejecución.
6. Validar entrada.
7. Adquirir tokens y slot de concurrencia.
8. Ejecutar en proceso o worker aislado.
9. Limitar tiempo, memoria, salida y red.
10. Validar salida.
11. Liberar cuota y actualizar métricas.
12. Mantener o destruir el worker según su política.
```

La fase sirve para organizar y aplicar perfiles predeterminados, pero no debe sustituir la identidad individual de la herramienta. Dos herramientas de la misma fase pueden tener perfiles de recursos completamente distintos.

## 10. Plan de implementación incremental

### Etapa 1: índice persistente sin sandbox

- Crear SQLite local.
- Indexar las 304 herramientas integradas.
- Añadir fingerprint del entorno.
- Implementar resolución por clave primaria.
- Medir tiempo de arranque antes y después.

### Etapa 2: caché en memoria

- Añadir LRU para metadatos y esquemas compilados.
- Aplicar carga diferida de `SKILL.md` y fábricas.
- Medir hit rate, memoria y latencias p50/p95/p99.

### Etapa 3: módulos de fase

- Convertir cada fase en paquete opcional, manteniendo un solo core.
- Publicar entry points de herramientas y de módulos.
- Añadir filtros `--phase` al CLI.
- Mantener identificadores cualificados.

### Etapa 4: supervisor de workers

- Implementar protocolo JSON Lines.
- Crear un worker persistente para un plugin de ejemplo.
- Añadir timeout, límite de salida y terminación controlada.
- Separar stdout de stderr.

### Etapa 5: cuotas

- Añadir cuotas globales y por fase.
- Añadir concurrencia por plugin.
- Añadir token bucket para invocaciones y red.
- Añadir estados `quota_exceeded`, `timeout` y `worker_crashed`.

### Etapa 6: sandbox fuerte

- Filtrar entorno y credenciales.
- Aislar filesystem.
- Deshabilitar red por defecto.
- Evaluar contenedor sin privilegios para plugins no confiables.
- Ejecutar pruebas de escape, traversal y agotamiento de recursos.

## 11. Métricas de aceptación

Antes de afirmar que la arquitectura escala, deben medirse al menos estas variables:

| Métrica | Comparaciones requeridas |
| --- | --- |
| Tiempo de arranque | Sin índice, índice frío e índice caliente. |
| Tiempo de resolución | 304, 1.000, 5.000 y 10.000 herramientas. |
| Memoria RSS | Host sin plugins cargados y con workers activos. |
| Hit rate | Caché L1, L2 y L3. |
| Latencia de ejecución | En proceso, worker persistente y worker nuevo. |
| Tiempo en cola | Por fase y por plugin. |
| Tasa de rechazo | Por cuota, timeout y contrato inválido. |
| Recuperación | Reinicio tras crash, timeout y fuga de memoria. |
| Seguridad | Intentos de leer rutas, usar red y crear procesos no permitidos. |

## 12. Conclusión

La combinación de SQLite persistente, cachés LRU en memoria y carga diferida es suficiente para mitigar el coste de descubrimiento de las 304 herramientas sin introducir una infraestructura externa. El índice debe ser reconstruible, versionado e invalidable; la caché debe tratar los metadatos y esquemas como objetos versionados, no como datos permanentes.

La organización por fases es viable y aporta valor, especialmente para instalación selectiva, dependencias y mantenimiento. La decisión correcta es distribuir las fases como módulos o paquetes, pero mantener un solo core para runtime, contratos, registro, cuotas y seguridad.

El sandboxing debe basarse en un supervisor, workers aislados, capacidades explícitas y límites multidimensionales. Las cuotas deben aplicarse por host, fase, plugin y usuario o tenant. De ese modo, una herramienta pesada de Datos, una herramienta con dependencias de Medios o un plugin de terceros no puede degradar de manera silenciosa a todo el framework.

## Referencias

[1]: https://github.com/hubgunter4-ops/content-skills-toolkit "Repositorio Content Skills Toolkit"
[2]: https://packaging.python.org/specifications/entry-points/ "Entry points specification — Python Packaging User Guide"
[3]: https://packaging.python.org/en/latest/guides/writing-pyproject-toml/ "Writing your pyproject.toml — Python Packaging User Guide"
[4]: https://json-schema.org/specification "JSON Schema Specification"
