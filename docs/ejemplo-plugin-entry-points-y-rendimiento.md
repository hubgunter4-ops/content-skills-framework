# Ejemplo práctico: plugin con Python entry points y escalabilidad del framework

**Solicitud identificable:** ejemplo de implementación de plugin y desafíos de rendimiento al escalar el framework  
**Repositorio de referencia:** [Content Skills Toolkit][1]  
**Fecha:** 9 de septiembre de 2026  
**Autor:** **Manus AI**

## 1. Resumen

El sistema de Python *entry points* permite que un paquete externo anuncie una herramienta sin modificar el registro central del framework. El host descubre el plugin mediante `importlib.metadata`, carga una fábrica, obtiene sus metadatos y valida el contrato antes de exponerlo.

El ejemplo incluido en esta guía implementa un plugin llamado `community/analizador-de-legibilidad`. Es local, determinista y no utiliza red, credenciales ni archivos externos. La implementación es deliberadamente ilustrativa: las clases `ToolMetadata`, `ExecutionRequest` y `ExecutionResult` representan la API pública propuesta en el informe anterior y todavía deben existir en el runtime real antes de instalar este ejemplo.

A escala de miles de herramientas, el problema más importante no será únicamente ejecutar una herramienta. Será mantener rápido y confiable el ciclo completo de **descubrimiento, carga, validación, selección, ejecución, aislamiento y observabilidad**. La solución debe combinar índices persistentes, carga diferida, validación por etapas, límites de concurrencia y una separación estricta entre metadatos y código ejecutable.

## 2. Estructura del plugin

```text
plugin-analizador-legibilidad/
├── plugin.py
├── pyproject.toml
├── host_demo.py
└── schemas.json
```

En una implementación de producción, los dos esquemas contenidos en `schemas.json` se distribuirían como archivos independientes:

```text
schemas/
├── input.schema.json
└── output.schema.json
```

La separación es recomendable porque el runtime debe poder validar o mostrar el contrato sin importar el código del plugin.

## 3. Contrato mínimo del runtime

El plugin presupone los siguientes objetos conceptuales:

```python
class ToolMetadata:
    id: str
    version: str
    name: str
    description: str
    input_schema: str
    output_schema: str
    capabilities: frozenset[str]
    contract_version: str

class ExecutionRequest:
    payload: dict
    request_id: str
    workspace: str | None

class ExecutionResult:
    status: str
    analysis: dict
    deliverable: dict
    warnings: list[str]
    provenance: dict
```

Estos tipos deben considerarse parte de la API estable. El plugin no debería depender de clases internas del registro ni de rutas privadas del repositorio.

## 4. Implementación del plugin

El archivo `plugin.py` contiene una clase que expone `metadata()` y `execute()`, además de una fábrica pública llamada `create_tool`.

```python
class AnalizadorDeLegibilidad:
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            id="community/analizador-de-legibilidad",
            version="1.0.0",
            name="Analizador de legibilidad",
            description="Calcula indicadores simples de longitud y legibilidad sobre texto proporcionado.",
            input_schema="schemas/input.schema.json",
            output_schema="schemas/output.schema.json",
            capabilities=frozenset(),
            contract_version="1.0",
        )

    def execute(self, request: ExecutionRequest) -> ExecutionResult:
        # Validar la entrada antes de ejecutar.
        # Calcular resultados únicamente sobre request.payload.
        # Devolver provenance y advertencias explícitas.
        ...


def create_tool() -> AnalizadorDeLegibilidad:
    return AnalizadorDeLegibilidad()
```

La herramienta declara `capabilities=frozenset()`. Esto comunica que no requiere red, credenciales, escritura en disco ni procesos hijos. En un framework con políticas de seguridad, esa declaración puede utilizarse para seleccionar el backend de ejecución más económico: una herramienta pura y confiable puede ejecutarse en proceso, mientras que un plugin no confiable puede ejecutarse en un subproceso aislado.

La fórmula del ejemplo es heurística. El plugin debe advertirlo y no presentarla como una evaluación lingüística completa. Esta distinción es importante para conservar fidelidad entre la documentación, el contrato y el comportamiento real.

## 5. Declaración del entry point

El `pyproject.toml` del paquete externo contiene:

```toml
[project]
name = "content-skills-plugin-legibilidad"
version = "1.0.0"
requires-python = ">=3.10"
dependencies = [
  "content-skills-toolkit>=0.2,<0.3",
]

[project.entry-points."content_skills_toolkit.tools"]
community-analizador-de-legibilidad = "plugin:create_tool"
```

El grupo `content_skills_toolkit.tools` es el espacio de descubrimiento del framework. La especificación de Python Packaging define los entry points como metadatos mediante los cuales una distribución instalada anuncia componentes que otra aplicación puede descubrir y utilizar.[2]

La clave del entry point debe ser estable y no debe confundirse con el identificador completo de la herramienta. El host debe comprobar que el objeto cargado confirma su identidad mediante `metadata().id`. Una discrepancia entre el nombre anunciado y los metadatos debe producir un error de registro, no una herramienta parcialmente disponible.

## 6. Descubrimiento por el host

El host puede implementar una primera versión así:

```python
from importlib.metadata import entry_points


def discover_tools():
    entries = entry_points(group="content_skills_toolkit.tools")
    for entry in entries:
        factory = entry.load()
        tool = factory()
        metadata = tool.metadata()
        validate_metadata(metadata)
        yield tool
```

El ejemplo incluido en `host_demo.py` comprueba la identidad del entry point y muestra la versión de cada herramienta. En producción el host debe agregar validaciones adicionales:

1. Confirmar que el identificador sigue el formato `namespace/slug`.
2. Confirmar que la versión cumple la política de versiones del framework.
3. Confirmar que los esquemas existen dentro de la distribución.
4. Confirmar que el contrato declarado es compatible.
5. Confirmar que las capacidades están dentro del vocabulario permitido.
6. Detectar duplicados antes de hacer visible el registro.
7. Registrar el nombre de la distribución que proporciona el plugin.
8. No ejecutar la herramienta durante el descubrimiento.

El punto 8 es esencial. Importar un módulo ya ejecuta parte de su código de inicialización. Por ello, el contrato del plugin debe exigir inicialización mínima y sin llamadas externas. La ejecución real debe ocurrir solamente después de que el usuario seleccione la herramienta.

## 7. Instalación y prueba conceptual

Desde un entorno virtual, la secuencia esperada sería:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e /ruta/al/framework
python -m pip install -e /ruta/al/plugin-analizador-legibilidad
python host_demo.py
```

La salida conceptual sería:

```text
community/analizador-de-legibilidad 1.0.0
```

Una invocación posterior podría verse así:

```python
from content_skills import Toolkit

kit = Toolkit()
result = kit.execute(
    "community/analizador-de-legibilidad",
    {
        "objective": "Revisar una introducción",
        "audience": "Equipo editorial",
        "content": "Este es un texto breve. Tiene dos oraciones.",
        "format": "json",
    },
)
```

El resultado debe incluir `status`, `analysis`, `deliverable`, `warnings` y `provenance`. La salida no debe incluir credenciales ni afirmar que se consultaron servicios externos.

## 8. Pruebas que debe aportar el plugin

El framework debería imponer una suite mínima de conformidad para todos los plugins:

| Prueba | Propósito |
| --- | --- |
| Descubrimiento | Verifica que el entry point aparece en el grupo correcto. |
| Metadatos | Verifica identidad, versión, descripción y contrato. |
| Entrada válida | Verifica el caso normal. |
| Entrada incompleta | Verifica `needs_input` o el error contractual definido. |
| Salida válida | Valida el resultado contra `output.schema.json`. |
| Determinismo | Ejecuta la misma entrada dos veces y compara el resultado permitido. |
| Capacidades | Confirma que el plugin no utiliza capacidades no declaradas. |
| Timeout | Comprueba que el runtime puede cancelar una ejecución lenta. |
| Secretos | Comprueba que valores sensibles no aparecen en logs ni resultados. |
| Compatibilidad | Comprueba la versión mínima y máxima soportada del runtime. |

## 9. Desafíos de rendimiento al escalar a miles de herramientas

### 9.1 Descubrimiento de entry points

Con cientos de paquetes instalados, consultar metadatos de distribuciones, leer `entry_points.txt` y cargar cada módulo puede convertirse en un coste perceptible al iniciar el CLI o el servidor. El problema aumenta si cada plugin realiza trabajo en el nivel superior de su módulo.

**Mitigaciones:**

- usar `importlib.metadata` solo para construir un índice inicial;
- almacenar un índice local con identificador, versión, distribución y referencia de objeto;
- invalidar el índice cuando cambien las distribuciones instaladas;
- cargar la fábrica únicamente después de seleccionar una herramienta;
- exigir que `metadata()` sea barato y no haga red;
- separar metadatos declarativos de código ejecutable;
- ofrecer un comando explícito para reconstruir el índice.

### 9.2 Memoria del catálogo

Miles de objetos `ToolSpec`, descripciones completas, esquemas, documentación Markdown y metadatos pueden incrementar el consumo de memoria, especialmente en procesos de larga duración o múltiples workers.

**Mitigaciones:**

- mantener en memoria solo índices compactos: `id`, versión, distribución y rutas;
- cargar `SKILL.md` y esquemas bajo demanda;
- evitar guardar simultáneamente el contenido completo de todos los documentos;
- usar representación inmutable y compartible entre workers cuando sea posible;
- diferenciar `list --brief` de `show`, que sí carga la documentación completa;
- medir el tamaño del índice con 304, 1.000, 5.000 y 10.000 herramientas.

### 9.3 Coste de validación

Validar cada documentación, esquema y runner durante cada arranque sería una operación innecesariamente costosa. La validación exhaustiva es correcta para CI, pero no debe bloquear todas las ejecuciones de producción.

**Mitigaciones:**

- validación completa en CI y durante la instalación;
- validación ligera al arranque: integridad del índice, versión y presencia de archivos;
- caché por hash de archivo o hash de distribución;
- validación del esquema de entrada solo para la herramienta seleccionada;
- validación de salida únicamente en modo estricto o en entornos de prueba;
- comando separado `validate --all` para auditorías completas.

### 9.4 Resolución de identificadores y colisiones

Con miles de herramientas, buscar linealmente por slug deja de ser apropiado. Además, los slugs cortos pueden colisionar entre comunidades, fases y versiones.

**Mitigaciones:**

- usar un índice hash por identificador cualificado;
- tratar `namespace/slug` como identificador primario;
- mantener alias cortos solo cuando sean inequívocos;
- construir un índice invertido para búsqueda por etiquetas y capacidades;
- rechazar duplicados durante la construcción del registro;
- resolver versiones mediante una regla determinista, nunca por orden de instalación.

### 9.5 Carga de plugins y aislamiento

La ejecución en proceso tiene baja latencia, pero un plugin lento, con fuga de memoria o con una dependencia incompatible puede afectar al host completo. La ejecución por subproceso mejora el aislamiento, pero introduce coste de creación de proceso, serialización JSON y comunicación entre procesos.

**Mitigaciones:**

| Modelo | Ventaja | Coste |
| --- | --- | --- |
| En proceso | Latencia baja y no requiere serialización adicional | Riesgo de contaminación, bloqueo o fuga de memoria. |
| Subproceso persistente | Aislamiento razonable y amortización del arranque | Gestión de workers, IPC y reinicios. |
| Subproceso por ejecución | Aislamiento fuerte y sencillo de razonar | Latencia alta para tareas pequeñas. |
| Contenedor | Aislamiento más fuerte y límites claros | Coste operativo y de arranque elevado. |

La política recomendada es seleccionar el backend según confianza y capacidades. Las herramientas puras, pequeñas y auditadas pueden ejecutarse en proceso. Los plugins de terceros con red, procesos o dependencias complejas deberían ejecutarse en workers persistentes aislados.

### 9.6 Concurrencia y saturación

Miles de herramientas no implican necesariamente miles de ejecuciones concurrentes. El riesgo real es que muchas solicitudes utilicen simultáneamente CPU, memoria, red o proveedores externos. Sin límites, una herramienta de análisis pesado puede degradar todas las demás.

**Mitigaciones:**

- pools separados por clase de recurso;
- límites globales y por plugin;
- cuotas de CPU, memoria, red y tiempo;
- backpressure y colas con prioridad;
- circuit breakers para proveedores externos;
- límites de concurrencia por credencial o endpoint;
- cancelación cooperativa y cancelación forzada del worker;
- métricas de cola, tiempo de espera y tiempo de ejecución.

### 9.7 Serialización y tamaño de resultados

El contrato JSON facilita interoperabilidad, pero serializar textos extensos, tablas, HTML, SVG o documentos grandes puede convertirse en el cuello de botella. También aumenta la memoria temporal al construir la respuesta completa.

**Mitigaciones:**

- establecer límites de entrada y salida;
- usar streaming para resultados grandes cuando el contrato lo permita;
- separar metadatos de artefactos binarios o archivos grandes;
- devolver referencias a artefactos con hashes, en lugar de duplicar contenido;
- comprimir únicamente cuando el transporte lo justifique;
- no copiar varias veces el mismo payload entre host, worker y logger.

### 9.8 Observabilidad a gran volumen

Registrar cada entrada completa y cada salida completa puede consumir más recursos que la ejecución y puede exponer datos sensibles. Sin métricas adecuadas, tampoco será posible identificar qué plugins degradan el sistema.

**Mitigaciones:**

- registrar por defecto solo `request_id`, herramienta, versión, estado, duración, tamaños y error tipado;
- utilizar hashes o identificadores de contenido en lugar de payloads completos;
- muestrear trazas de ejecuciones exitosas;
- conservar el detalle completo solo cuando exista consentimiento o modo diagnóstico;
- medir p50, p95 y p99 por herramienta y backend;
- separar métricas de descubrimiento, validación, espera y ejecución.

### 9.9 Dependencias y conflictos

Miles de plugins pueden requerir versiones incompatibles de librerías, incrementar el tiempo de resolución de paquetes y aumentar el tamaño de instalación. Si todos se instalan en el mismo entorno, un plugin puede romper otro aunque nunca se ejecute.

**Mitigaciones:**

- plugins con dependencias opcionales y límites de versión explícitos;
- aislamiento por entorno o worker para plugins complejos;
- catálogo de compatibilidad probado;
- instalación por grupos o perfiles, no de todo el ecosistema;
- escaneo de vulnerabilidades y revisión de licencias;
- soporte para deshabilitar una distribución sin desinstalarla.

### 9.10 CI y validación del catálogo

La validación de 304 herramientas puede ser cómoda hoy, pero ejecutar pruebas exhaustivas de miles de plugins en cada cambio del núcleo puede volver lento el ciclo de desarrollo.

**Mitigaciones:**

- pruebas de contrato comunes ejecutadas en paralelo;
- pruebas específicas solo para plugins afectados;
- caché de dependencias y artefactos;
- matriz de pruebas por versión de runtime;
- smoke tests rápidos en cada pull request;
- pruebas completas nocturnas o antes de releases;
- compatibilidad certificada por plugin y versión.

## 10. Objetivos de rendimiento sugeridos

No deben fijarse como garantías antes de medir, pero sirven como hipótesis de diseño:

| Operación | Objetivo inicial para investigar |
| --- | ---: |
| Consulta de una herramienta ya indexada | < 1 ms sin cargar código |
| `list --brief` con 5.000 herramientas | < 200 ms desde índice en memoria |
| `show` de documentación local | < 50 ms con caché caliente |
| Validación de entrada pequeña | < 5 ms con esquema cacheado |
| Arranque del host | Independiente del número de plugins no seleccionados, salvo reconstrucción de índice |
| Ejecución aislada de una herramienta pequeña | Medir sobrecoste separado del tiempo propio del plugin |

Estos valores son objetivos de ingeniería, no resultados medidos. La primera tarea de rendimiento debe construir un benchmark reproducible con 304, 1.000, 5.000 y 10.000 entradas sintéticas y una mezcla realista de plugins ligeros y pesados.

## 11. Orden recomendado para resolver el escalamiento

1. **Índice compacto y carga diferida.** Evita el problema de arranque y memoria antes de que exista.
2. **Identificadores cualificados e índices hash.** Evita búsquedas lineales y ambigüedades.
3. **Validación por etapas.** Separa CI, instalación, arranque y ejecución.
4. **Modelo de capacidades y backends.** Permite elegir entre baja latencia y aislamiento.
5. **Pools y cuotas.** Evita que una herramienta monopolice el host.
6. **Resultados por referencia y límites de tamaño.** Evita duplicación de datos.
7. **Observabilidad agregada.** Permite localizar el problema sin registrar contenido sensible.
8. **Benchmarks y pruebas de carga.** Convierte las hipótesis en límites medidos.

## 12. Conclusión

El sistema de entry points es adecuado para convertir el catálogo en un ecosistema extensible, siempre que el framework no confunda descubrimiento con ejecución. Un plugin debe ser identificable, versionado, validable y explícito respecto a sus capacidades.

A escala de miles de herramientas, el diseño debe evitar tres errores: importar todo al iniciar, cargar todos los documentos y esquemas en memoria, y ejecutar todos los plugins con el mismo nivel de confianza. La arquitectura debe usar índices compactos, carga diferida, validación cacheada, identificadores cualificados, workers aislados y límites de recursos.

La recomendación práctica es implementar primero un plugin de referencia como el de esta guía y usarlo para fijar el contrato. Después debe medirse el runtime con un catálogo sintético de al menos 5.000 herramientas antes de comprometer una arquitectura de despliegue o unas garantías de latencia.

## Referencias

[1]: https://github.com/hubgunter4-ops/content-skills-toolkit "Repositorio Content Skills Toolkit"
[2]: https://packaging.python.org/specifications/entry-points/ "Entry points specification — Python Packaging User Guide"
