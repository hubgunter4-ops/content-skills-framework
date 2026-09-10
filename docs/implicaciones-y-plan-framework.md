# Implicaciones y plan estructurado para convertir Content Skills Toolkit en un framework

**Solicitud identificable:** análisis de implicaciones de creación y plan de realización para `content-skills-toolkit`  
**Repositorio analizado:** [hubgunter4-ops/content-skills-toolkit][1]  
**Fecha del análisis:** 9 de septiembre de 2026  
**Autor:** **Manus AI**

## 1. Resumen ejecutivo

El repositorio tiene una base adecuada para evolucionar hacia un **framework local de herramientas ejecutables y habilidades documentadas**, pero todavía no debe tratarse como un framework público completamente estabilizado. Actualmente contiene un catálogo de **304 herramientas**, un registro unificado, seis motores de fase, runners independientes, contratos JSON, integración diferida y una interfaz CLI. La línea base verificada es verde: las 23 pruebas unitarias pasan, la compilación de Python pasa y `python3 -m toolkit validate` informa que las 304 herramientas tienen contratos válidos.

La implicación principal es que el trabajo no consiste en reescribir 304 herramientas. Consiste en definir y estabilizar una **plataforma de extensión** alrededor de ellas. Esa plataforma debe separar cuatro responsabilidades: el núcleo de ejecución, el registro y descubrimiento de herramientas, los contratos de entrada y salida, y las extensiones opcionales como APIs externas o proveedores de inteligencia artificial.

La recomendación es ejecutar el proyecto en siete etapas. Primero se congela la compatibilidad actual. Después se formaliza la API pública, se normalizan los contratos, se introduce un sistema de plugins, se aíslan las integraciones, se fortalece la seguridad y se prepara la distribución. La publicación en PyPI, la ejecución remota, el despliegue como servicio y la activación automática de credenciales deben quedar fuera de la primera versión estable.

## 2. Qué existe hoy

El proyecto ya implementa un patrón coherente: el CLI consulta un registro, el registro localiza una herramienta, el runner invoca un motor de fase y el resultado se expresa como JSON. El README describe el flujo como `CLI → registro → SKILL.md → runner → motor de fase → JSON → pruebas`.[1]

| Área | Situación observada | Consecuencia para el framework |
| --- | --- | --- |
| Catálogo | 304 herramientas distribuidas en seis fases | Existe una masa crítica para probar descubrimiento, compatibilidad y escalabilidad. |
| Ejecución | Runners Python independientes que leen JSON y escriben JSON | El contrato puede convertirse en una API estable, pero debe desacoplarse del proceso hijo. |
| Registro | `ToolSpec`, resolución por `fase/slug` y detección de slugs ambiguos | Es un buen núcleo de descubrimiento local; falta convertirlo en una interfaz extensible. |
| Motores | Un motor para la Fase 1 y motores específicos para las Fases 2–6 | Hay reutilización, pero también lógica centralizada por fase y acoplamiento a nombres de slug. |
| Documentación | `SKILL.md`, ejemplos, esquemas, recursos y pruebas smoke | La documentación es parte del contrato y debe versionarse junto con el código. |
| Integraciones | Carga diferida y explícita mediante variables de entorno | La decisión de seguridad es correcta; el framework necesita interfaces de proveedor y políticas de permisos. |
| CLI | `list`, `show`, `run`, `validate` e `integrations` | Es una buena interfaz de referencia, pero la API programática aún debe formalizarse. |
| Empaquetado | `pyproject.toml` básico, versión `0.1.0`, Python `>=3.10` | Falta declarar scripts, metadatos completos, dependencias opcionales, licencia y política de compatibilidad. |
| Calidad | Workflow de GitHub Actions y pruebas unitarias/smoke | La base de CI existe; faltan pruebas de contratos, seguridad, compatibilidad y distribución. |
| Licencia | No se encontró un archivo de licencia explícito | Es un bloqueo para redistribuir el framework con seguridad jurídica. |

## 3. Definición de framework propuesta

En este contexto, un framework sería una plataforma que permite a una aplicación o a un tercero:

1. descubrir herramientas instaladas;
2. leer sus metadatos y contratos;
3. validar entradas antes de ejecutar;
4. ejecutar una herramienta mediante una API uniforme;
5. validar la salida producida;
6. registrar eventos, advertencias y trazabilidad;
7. añadir nuevas herramientas sin modificar el núcleo;
8. activar integraciones mediante proveedores explícitos y permisos controlados.

Esta definición es más exigente que una colección de scripts. Un script puede funcionar por convención. Un framework debe ofrecer **interfaces estables**, **errores previsibles**, **versionado**, **aislamiento** y **extensibilidad documentada**.

## 4. Implicaciones de creación

### 4.1 Implicaciones de arquitectura

El código actual mezcla, en distintos niveles, descubrimiento, documentación, resolución, ejecución y adaptación por slug. Para un framework conviene establecer una arquitectura por capas:

```text
Aplicación consumidora
        |
API pública: discover / validate / execute
        |
Runtime y políticas de ejecución
        |
Registro de herramientas y plugins
        |
Contratos de entrada/salida + validadores
        |
Runners y adaptadores
        |
Motores locales o proveedores externos
```

La API pública debe dejar de depender de rutas de archivos o de ejecutar siempre un subproceso. El modo de subproceso puede mantenerse como backend seguro y compatible, pero debe existir también un `Runner` programático. El objetivo es que una aplicación pueda ejecutar una herramienta sin conocer si internamente se utiliza una función Python, un subproceso o un proveedor remoto.

### 4.2 Implicaciones de extensibilidad

El catálogo actual está definido principalmente dentro del repositorio. Para que terceros agreguen capacidades, el framework necesita una estrategia de plugins. La especificación de Python Packaging define los *entry points* como metadatos con los que una distribución instalada anuncia componentes que otras aplicaciones pueden descubrir y utilizar.[2] Esto permite registrar grupos propios, por ejemplo `content_skills_toolkit.tools`, sin editar el registro central.

La extensión debe incluir:

| Elemento | Decisión recomendada |
| --- | --- |
| Identidad | Nombre cualificado, versión y proveedor. |
| Interfaz | Métodos `metadata()`, `input_schema()`, `output_schema()` y `execute()`. |
| Descubrimiento | Catálogo integrado más plugins instalados por entry points. |
| Colisiones | Rechazar nombres duplicados salvo que exista una política explícita de prioridad. |
| Compatibilidad | Declarar versión del contrato y versión mínima del runtime. |
| Estado | Distinguir `available`, `needs_input`, `not_loaded`, `error` y `disabled`. |
| Recursos | Declarar si requiere red, credenciales, archivos, GPU o herramientas externas. |

No conviene convertir cada carpeta actual en un paquete independiente desde el primer día. Primero debe definirse el contrato; después se puede ofrecer un SDK de plugins y una plantilla de creación.

### 4.3 Implicaciones de contratos de datos

Los archivos `input.example.json` y `output.schema.json` ya apuntan a un modelo contractual. Para hacerlo confiable, el runtime debe validar ambos lados de la ejecución. JSON Schema 2020-12 separa el núcleo de la especificación de los vocabularios de validación y proporciona metaschemas para validar los propios esquemas.[3]

El contrato común debería incluir al menos:

```json
{
  "schema_version": "1.0",
  "tool": {
    "id": "phase-2-datos/validacion-de-datos",
    "version": "0.1.0"
  },
  "status": "ready",
  "analysis": {},
  "deliverable": {},
  "warnings": [],
  "provenance": {
    "runtime_version": "...",
    "external_calls": [],
    "inputs_digest": "..."
  }
}
```

El campo `provenance` es importante para diferenciar una ejecución local de una ejecución con APIs externas. También debe impedir que una herramienta declare resultados externos que no haya obtenido realmente.

### 4.4 Implicaciones del empaquetado y distribución

El `pyproject.toml` actual declara el backend, el nombre, la versión, la descripción y la versión mínima de Python. La guía oficial de empaquetado recomienda usar `build-system`, `project`, dependencias opcionales y `project.scripts` para exponer comandos instalables.[4]

La evolución del empaquetado debería contemplar:

- un comando instalable, por ejemplo `content-skills`;
- metadatos completos de autoría, licencia, URLs y clasificadores;
- una política de versiones compatible con SemVer o una política equivalente explícita;
- dependencias mínimas sin red para el núcleo;
- extras opcionales para validación, proveedores, renderizado o integraciones;
- inclusión correcta de `SKILL.md`, ejemplos, esquemas y recursos en wheels y sdists;
- pruebas de instalación en un entorno limpio;
- una matriz de Python soportado.

El núcleo debe seguir siendo pequeño. Las dependencias de proveedores externos no deben instalarse para quien solo necesita descubrir y ejecutar herramientas locales.

### 4.5 Implicaciones de seguridad

El repositorio adopta una postura segura al no cargar integraciones cuando el usuario no las solicita y al no incluir credenciales en las salidas. Esa política debe convertirse en un modelo formal de capacidades.

Cada herramienta debe declarar capacidades como:

| Capacidad | Ejemplo de política |
| --- | --- |
| `filesystem.read` | Solo rutas incluidas en el workspace permitido. |
| `filesystem.write` | Deshabilitada por defecto o limitada a una carpeta de salida. |
| `network` | Requiere integración explícita, dominio permitido y timeout. |
| `credentials.read` | Solo puede leer variables declaradas por su proveedor. |
| `process.spawn` | Deshabilitada para plugins no confiables. |
| `publish` | Fuera del núcleo y siempre detrás de confirmación externa. |
| `destructive_action` | Nunca implícita; debe producir un plan y no una ejecución automática. |

El riesgo más importante no es el runner local actual. Es el futuro ecosistema de plugins: un plugin instalado es código ejecutable. Por eso, la documentación debe advertir que el descubrimiento por entry points no equivale a aislamiento. Para plugins de terceros se debe ofrecer un modo de subproceso, límites de tiempo, límites de tamaño, filtrado de secretos y, si el entorno lo requiere, aislamiento por contenedor o proceso separado.

### 4.6 Implicaciones de calidad y mantenibilidad

La centralización actual por grandes funciones de despacho facilita una primera implementación, pero puede crecer con demasiadas ramas condicionadas por `slug`. Para evitar una matriz difícil de mantener, se recomienda migrar gradualmente a adaptadores declarativos:

```python
class ToolAdapter(Protocol):
    def metadata(self) -> ToolMetadata: ...
    def execute(self, request: ExecutionRequest) -> ExecutionResult: ...
```

El motor debe conocer contratos y políticas, no detalles de cada slug. Cada herramienta debe contener o referenciar su adaptador. Las pruebas deben cubrir el contrato común, mientras que las pruebas específicas deben cubrir el comportamiento propio de cada adaptador.

### 4.7 Implicaciones legales y de gobierno

La ausencia de una licencia explícita es un bloqueo para distribuir el código, copiar documentación, aceptar contribuciones y publicar un paquete. Antes de abrir el framework a terceros se debe:

1. identificar al titular de los componentes del repositorio;
2. elegir una licencia compatible con el objetivo del proyecto;
3. revisar si las descripciones, nombres o materiales de origen tienen restricciones;
4. añadir `LICENSE` y metadatos de licencia al paquete;
5. definir un `CODE_OF_CONDUCT`, una política de vulnerabilidades y un proceso de releases;
6. establecer quién puede aceptar plugins, cambios de contrato y excepciones de seguridad.

Esta decisión requiere confirmación del propietario del repositorio; no debe inferirse automáticamente.

## 5. Arquitectura objetivo

### 5.1 Paquetes propuestos

```text
content-skills-toolkit/
├── src/content_skills/
│   ├── api.py                 # API pública estable
│   ├── models.py              # Request, Result, Metadata, Capability
│   ├── registry.py            # catálogo local + plugins
│   ├── runtime.py             # ejecución, timeouts y políticas
│   ├── contracts.py           # carga y validación JSON Schema
│   ├── errors.py              # jerarquía de errores pública
│   ├── providers.py           # interfaces de integraciones
│   ├── cli.py                 # comando instalable
│   └── builtins/              # adaptadores del catálogo actual
├── skills/
│   └── ...                    # documentación y recursos
├── schemas/
│   ├── tool-metadata.schema.json
│   ├── execution-request.schema.json
│   └── execution-result.schema.json
├── tests/
│   ├── contract/
│   ├── integration/
│   ├── security/
│   └── compatibility/
├── docs/
├── LICENSE
└── pyproject.toml
```

La migración de `toolkit/` a `src/content_skills/` no debe realizarse en la primera iteración si rompe rutas existentes. Puede hacerse mediante una capa de compatibilidad y una migración en dos versiones.

### 5.2 API pública mínima

```python
from content_skills import Toolkit

kit = Toolkit()

for tool in kit.discover():
    print(tool.id, tool.version)

result = kit.execute(
    "phase-2-datos/validacion-de-datos",
    {
        "objective": "Validar un dataset",
        "audience": "Equipo de análisis",
        "content": "...",
        "format": "markdown"
    },
)
```

La API debe devolver objetos tipados o diccionarios con un contrato documentado. El CLI debe ser un consumidor de esa API, no una implementación paralela.

## 6. Plan detallado de realización

### Fase 0 — Gobierno, alcance y línea base

**Objetivo:** fijar las decisiones que no deben cambiar durante la implementación.

**Actividades:**

1. Confirmar si el producto será un framework interno, un paquete privado, un paquete público o una combinación.
2. Definir usuarios primarios: desarrolladores de plugins, autores de skills, equipos editoriales y aplicaciones consumidoras.
3. Elegir licencia y política de contribuciones.
4. Registrar la revisión base `a7e1fac` y conservar la compatibilidad del CLI actual.
5. Crear una matriz de herramientas con fase, slug, runner, motor, esquema, capacidades y estado.

**Criterio de salida:** alcance aprobado, licencia decidida, inventario reproducible y pruebas base verdes.

### Fase 1 — Especificación del contrato de framework

**Objetivo:** convertir convenciones internas en interfaces públicas.

**Actividades:**

1. Definir `ToolMetadata`, `ExecutionRequest`, `ExecutionResult`, `Capability` y `ProviderStatus`.
2. Definir la jerarquía de excepciones: entrada inválida, herramienta inexistente, conflicto, contrato inválido, proveedor no disponible y ejecución fallida.
3. Elegir la versión de JSON Schema soportada.
4. Definir reglas de compatibilidad para añadir campos, renombrar campos y retirar estados.
5. Documentar qué significa cada estado: `ready`, `needs_input`, `not_loaded`, `error` y `disabled`.

**Criterio de salida:** esquemas publicados, ejemplos válidos e inválidos y una prueba que verifique que el runtime rechaza resultados incompatibles.

### Fase 2 — Separación del núcleo y compatibilidad

**Objetivo:** extraer una API de runtime sin romper el CLI.

**Actividades:**

1. Crear modelos y funciones públicas sobre la lógica actual.
2. Mantener `python3 -m toolkit` como compatibilidad temporal.
3. Hacer que `__main__.py` delegue en la API pública.
4. Centralizar la carga de configuración y la resolución de rutas.
5. Proporcionar dos backends: `in_process` para adaptadores confiables y `subprocess` para runners existentes.
6. Añadir límites de tiempo, tamaño de entrada y tamaño de salida configurables.

**Criterio de salida:** todas las pruebas existentes pasan y el mismo runner produce el mismo resultado usando CLI y API programática.

### Fase 3 — Registro extensible y plugins

**Objetivo:** permitir capacidades externas sin editar el núcleo.

**Actividades:**

1. Definir el grupo de entry points con un nombre propiedad del proyecto, por ejemplo `content_skills_toolkit.tools`.
2. Implementar descubrimiento con `importlib.metadata`.
3. Validar metadatos del plugin antes de cargar su código.
4. Resolver conflictos por identificador y versión de forma determinista.
5. Crear un paquete plantilla `content-skills-toolkit-plugin-template` o un comando `content-skills plugin init`.
6. Documentar que un plugin instalado ejecuta código y no está aislado automáticamente.

**Criterio de salida:** un plugin de ejemplo, instalado localmente, aparece en `list`, se muestra con `show` y se ejecuta con el mismo contrato que una herramienta integrada.

### Fase 4 — Normalización de las 304 herramientas

**Objetivo:** asegurar que todo el catálogo use el contrato público.

**Actividades:**

1. Eliminar dependencias de rutas relativas en los runners.
2. Sustituir progresivamente los grandes dispatchers por adaptadores registrados.
3. Validar entrada y salida para cada herramienta.
4. Añadir `schema_version`, versión de herramienta y capacidades.
5. Auditar que cada `SKILL.md` describa lo que realmente hace el runner.
6. Marcar explícitamente las herramientas que producen plantillas o planes, en lugar de resultados ejecutados.

**Criterio de salida:** las 304 herramientas se descubren, validan y ejecutan mediante la API pública, con reporte de excepciones y sin descripciones exageradas.

### Fase 5 — Integraciones y proveedores

**Objetivo:** transformar las integraciones actuales en extensiones controladas.

**Actividades:**

1. Definir `Provider` como interfaz de proveedor.
2. Separar autenticación, transporte, transformación y adaptación de resultados.
3. Aplicar timeouts, reintentos limitados, límites de respuesta y allowlists de dominios.
4. Añadir redacción de secretos en logs y resultados.
5. Registrar proveedor, endpoint, fecha, parámetros no sensibles y estado en `provenance`.
6. Mantener el núcleo sin dependencias de proveedores.

**Criterio de salida:** una integración solicitada explícitamente produce trazabilidad suficiente y una integración no solicitada no genera tráfico de red.

### Fase 6 — Seguridad, observabilidad y pruebas de abuso

**Objetivo:** hacer segura la ejecución en escenarios reales.

**Actividades:**

1. Añadir pruebas de path traversal, entradas JSON enormes, HTML no escapado, URLs no permitidas y secretos en payloads.
2. Definir un sandbox de proceso para plugins no confiables.
3. Añadir cancelación y timeouts.
4. Registrar métricas de duración, estado, tamaño y proveedor sin registrar contenido sensible por defecto.
5. Crear un documento de threat model.
6. Añadir un procedimiento de reporte de vulnerabilidades.

**Criterio de salida:** ninguna prueba de seguridad crítica puede leer secretos, escribir fuera del workspace permitido o realizar una llamada externa no autorizada.

### Fase 7 — Empaquetado, releases y documentación

**Objetivo:** entregar una primera versión consumible del framework.

**Actividades:**

1. Migrar gradualmente al layout `src/` si la compatibilidad lo permite.
2. Declarar `project.scripts`, licencia, URLs, classifiers y dependencias opcionales en `pyproject.toml`.
3. Construir wheel y sdist en CI.
4. Instalar los artefactos en un entorno limpio y ejecutar smoke tests.
5. Publicar documentación de API, guía de plugins, guía de seguridad y matriz de compatibilidad.
6. Adoptar una política de versiones y un changelog orientado a usuarios.
7. Crear releases firmadas o, como mínimo, artefactos con hashes publicados.

**Criterio de salida:** un usuario puede instalar el paquete, descubrir una herramienta integrada, instalar un plugin de ejemplo y ejecutar ambos con documentación suficiente.

## 7. Roadmap priorizado

| Prioridad | Entregable | Valor | Riesgo | Dependencias |
| --- | --- | ---: | ---: | --- |
| P0 | Decisión de licencia y alcance | Muy alto | Alto | Titularidad del código y documentación |
| P0 | Contrato común de ejecución | Muy alto | Medio | Inventario de herramientas |
| P0 | API pública compatible con el CLI | Muy alto | Medio | Contrato común |
| P1 | Validación JSON Schema de entrada y salida | Alto | Medio | Contratos publicados |
| P1 | Límites de runtime y capacidades | Muy alto | Alto | API pública |
| P1 | Registro por entry points | Alto | Medio | Metadatos de herramienta |
| P1 | Plugin de ejemplo y plantilla | Alto | Medio | Registro extensible |
| P2 | Adaptadores por herramienta | Alto | Alto | Compatibilidad estable |
| P2 | Proveedores externos con trazabilidad | Alto | Alto | Modelo de capacidades |
| P2 | Sandbox para plugins | Muy alto | Alto | Backend por subproceso |
| P3 | Distribución pública y releases | Medio | Alto | Licencia, seguridad y CI |
| P3 | Servicio HTTP o ejecución remota | Medio | Muy alto | Autenticación, aislamiento y observabilidad |

## 8. Riesgos principales y mitigaciones

| Riesgo | Impacto | Mitigación |
| --- | --- | --- |
| Convertir 304 scripts en una API sin contrato estable | Cambios incompatibles y mantenimiento costoso | Estabilizar primero modelos, estados y esquemas. |
| Acoplamiento a slugs y ramas de despacho | Cada nueva herramienta requiere editar el núcleo | Migrar a adaptadores registrados y metadatos declarativos. |
| Plugins maliciosos o defectuosos | Ejecución de código, fuga de secretos o daño al sistema | Entry points con advertencia explícita, subprocesos, capacidades, timeouts y sandbox. |
| Integraciones con credenciales | Exposición de secretos y llamadas inesperadas | Proveedores explícitos, allowlists, redacción y ausencia de red por defecto. |
| Documentación más ambiciosa que la implementación | Usuarios toman decisiones basadas en resultados inexistentes | Validación de fidelidad entre `SKILL.md`, runner y esquema. |
| Ausencia de licencia | Bloqueo para redistribución y contribuciones | Resolver titularidad y añadir licencia antes de publicar. |
| Compatibilidad de Python y dependencias | Instalaciones que funcionan solo en el entorno del autor | CI con matriz de versiones y pruebas en entornos limpios. |
| Resultados no reproducibles | Dificultad para auditar y comparar ejecuciones | `provenance`, versiones, hashes de entrada y registro de fuentes. |

## 9. Criterios de aceptación de la primera versión estable

La primera versión estable del framework debe cumplir estas condiciones:

1. Una aplicación puede descubrir herramientas integradas mediante una API pública.
2. Una herramienta puede ejecutarse desde API y CLI con el mismo contrato.
3. Las entradas y salidas se validan contra esquemas versionados.
4. Los errores tienen tipos y mensajes documentados.
5. Un plugin externo puede instalarse sin modificar el núcleo.
6. Las colisiones de identificadores se rechazan de forma determinista.
7. Las integraciones no generan tráfico de red sin solicitud explícita.
8. Las credenciales no aparecen en resultados ni logs normales.
9. Los límites de tiempo, tamaño y capacidades se pueden configurar.
10. Las 304 herramientas existentes pasan una suite de compatibilidad o están marcadas con una excepción documentada.
11. El paquete se puede instalar desde un artefacto construido en CI.
12. Existe una licencia explícita y una política de seguridad aplicable.

## 10. Decisiones que requieren confirmación del propietario

El análisis técnico permite avanzar sin bloquearse, pero estas decisiones cambian materialmente el resultado y deben ser aprobadas por el propietario:

| Decisión | Alternativas |
| --- | --- |
| Público o privado | Framework público, paquete privado o núcleo público con catálogo privado. |
| Licencia | Permisiva, copyleft o uso interno sin publicación. |
| Modelo de plugins | Solo plugins confiables, plugins por subproceso o sandbox fuerte. |
| Integraciones | Solo interfaces, proveedores incluidos opcionales o servicio remoto. |
| Compatibilidad | Mantener rutas actuales indefinidamente o deprecarlas en una versión mayor. |
| Distribución | Wheel privado, PyPI público, repositorio Git o distribución interna. |

## 11. Conclusión

Sí es técnicamente posible convertir este repositorio en un framework, y la base actual reduce de forma importante el riesgo inicial. El proyecto ya cuenta con catálogo, registro, motores, documentación, contratos, pruebas y CI. Sin embargo, la creación del framework introduce responsabilidades nuevas que no se resuelven solo agregando más herramientas: **API pública, versionado, extensibilidad, seguridad de plugins, trazabilidad, licencia y distribución**.

La estrategia correcta es construir primero un runtime pequeño y estable, conservar el CLI como fachada compatible, validar los contratos con JSON Schema, incorporar plugins mediante entry points y mantener las integraciones fuera del núcleo. La mayor decisión no es tecnológica, sino de gobierno: definir quién puede distribuir el framework, qué código puede ejecutar un plugin y qué garantías de compatibilidad se ofrecerán.

## Referencias

[1]: https://github.com/hubgunter4-ops/content-skills-toolkit "Repositorio Content Skills Toolkit"
[2]: https://packaging.python.org/specifications/entry-points/ "Entry points specification — Python Packaging User Guide"
[3]: https://json-schema.org/specification "JSON Schema Specification"
[4]: https://packaging.python.org/en/latest/guides/writing-pyproject-toml/ "Writing your pyproject.toml — Python Packaging User Guide"
