# Interfaz de peticiones y enrutamiento de herramientas

**Solicitud identificable:** interfaz para peticiones del usuario, selección de herramienta y ejecución completa mediante el script de cada herramienta  
**Estado:** diseño arquitectónico, sin implementación todavía  
**Repositorio:** `content-skills-toolkit`  
**Fecha:** 9 de septiembre de 2026

## 1. Confirmación del requisito

El framework necesita una capa que permita al usuario expresar una petición completa sin conocer necesariamente el identificador técnico de la herramienta. Esa capa debe analizar la petición, determinar qué herramienta o secuencia de herramientas es adecuada y ejecutar la herramienta seleccionada de principio a fin.

La herramienta seleccionada debe conservar su propio script ejecutable. El runtime no debe sustituirlo por lógica genérica. El script es el punto de entrada operativo de la herramienta y debe declarar o referenciar:

- identidad y versión;
- contrato de entrada;
- contrato de salida;
- capacidades requeridas;
- motor o adaptador utilizado;
- procedimiento de ejecución;
- pruebas smoke;
- límites y advertencias.

El flujo central quedaría así:

```text
Petición del usuario
        ↓
Interfaz de peticiones
        ↓
Normalizador de intención
        ↓
Enrutador / selector de herramientas
        ↓
Validación de capacidades y contratos
        ↓
Cuotas + circuit breaker + política de seguridad
        ↓
Script de la herramienta seleccionada
        ↓
Resultado completo y trazable
        ↓
Interfaz de respuesta
```

## 2. Interfaz propuesta

La interfaz debe tener dos modos complementarios.

### 2.1 Modo guiado

Está dirigido a usuarios que no conocen las 304 herramientas. Permite escribir una petición y ofrece una selección explicada.

Componentes principales:

1. **Campo de petición:** texto libre o entrada estructurada.
2. **Objetivo detectado:** resumen de lo que el sistema cree que se solicita.
3. **Fase sugerida:** Contenido, Datos, Programming, Automatización, Negocios o Medios.
4. **Herramienta recomendada:** identificador, descripción, capacidades y motivo de selección.
5. **Alternativas:** otras herramientas compatibles, con sus diferencias.
6. **Recursos requeridos:** red, archivos, credenciales, tiempo estimado y nivel de aislamiento.
7. **Solicitud normalizada:** JSON que se enviará al script.
8. **Vista previa de ejecución:** cuotas, circuit breaker y backend que se utilizará.
9. **Ejecución:** botón o comando para iniciar la herramienta.
10. **Resultado:** entregable, advertencias, fuentes, métricas y trazabilidad.

### 2.2 Modo experto

Está dirigido a desarrolladores y operadores. Permite seleccionar directamente:

```text
Fase: phase-2-datos
Herramienta: validacion-de-datos
Script: toolkit/phase-2-datos/validacion-de-datos/run.py
Entrada: request.json
Backend: worker aislado
```

El modo experto no debe omitir las validaciones de contrato, cuotas o seguridad. Solo evita la selección automática.

## 3. Flujo de toma de decisiones

### Paso 1: recepción

El usuario proporciona una solicitud en lenguaje natural, un formulario o un JSON. Ejemplo:

> Valida este CSV, identifica valores faltantes y genera un informe en Markdown para el equipo de análisis.

### Paso 2: normalización

La interfaz convierte la petición en una estructura común:

```json
{
  "objective": "Validar un CSV e identificar valores faltantes",
  "audience": "Equipo de análisis",
  "content": "columna_a,columna_b\n1,\n2,3",
  "format": "markdown",
  "constraints": {
    "external_network": false,
    "write_files": false
  },
  "requested_output": "informe de validación",
  "user_selected_tool": null
}
```

La normalización debe separar hechos proporcionados por el usuario de inferencias realizadas por el selector. Por ejemplo, `format=markdown` puede ser explícito, mientras que `phase=phase-2-datos` puede ser una clasificación sugerida.

### Paso 3: selección

El selector consulta el índice de herramientas y calcula candidatas a partir de:

- intención de la petición;
- fase o dominio;
- formato solicitado;
- capacidades permitidas;
- disponibilidad del plugin;
- compatibilidad de entrada;
- estado del circuit breaker;
- cuotas disponibles;
- restricciones de seguridad;
- preferencia explícita del usuario.

La selección debe producir una explicación estructurada:

```json
{
  "selected_tool": "phase-2-datos/validacion-de-datos",
  "confidence": 0.94,
  "reason": [
    "La petición solicita validación de datos",
    "La entrada contiene una tabla CSV",
    "La salida solicitada es Markdown",
    "La herramienta no requiere red ni credenciales"
  ],
  "alternatives": [
    {
      "tool_id": "phase-2-datos/extractor-de-datos-de-documentos",
      "reason_not_selected": "Está orientada a PDF, DOCX o PPTX"
    }
  ],
  "requires_confirmation": false
}
```

La confianza no debe presentarse como una garantía de corrección. Si existen dos herramientas cercanas o la confianza está por debajo de un umbral, la interfaz debe pedir al usuario que elija o confirmar la herramienta recomendada.

### Paso 4: validación previa

Antes de ejecutar el script, el runtime debe comprobar:

1. La herramienta existe y no está duplicada.
2. La versión del contrato es compatible.
3. La entrada cumple el esquema.
4. Las capacidades solicitadas están permitidas.
5. La herramienta no tiene el circuito abierto.
6. Existe cuota disponible.
7. El backend de ejecución es compatible con el perfil de confianza.
8. Las rutas y archivos de entrada están autorizados.
9. Las credenciales requeridas están presentes solo si fueron solicitadas explícitamente.

Si falla una comprobación, no debe ejecutarse el script.

### Paso 5: ejecución completa

La ejecución completa significa que la herramienta debe recibir la solicitud normalizada y producir su resultado según su propio contrato. El runtime debe encargarse de la plataforma, no de reimplementar la lógica específica de cada herramienta.

El supervisor ejecutará algo equivalente a:

```bash
python toolkit/phase-2-datos/validacion-de-datos/run.py \
  --input /workspace/input/request.json \
  --output /workspace/output/result.json
```

En una versión basada en plugins instalables, el script puede ser expuesto por el paquete mediante un entry point, pero debe conservar un punto de ejecución equivalente:

```toml
[project.entry-points."content_skills_toolkit.tools"]
validacion-de-datos = "phase_data.tools:build_validacion"
```

La fábrica devuelve un objeto de herramienta; el worker llama a su método `execute()`. Para las herramientas existentes, el backend puede continuar invocando `run.py` como subproceso durante la migración.

## 4. Contrato de la herramienta

Cada herramienta debe conservar una estructura mínima:

```text
<fase>/<slug>/
├── SKILL.md
├── run.py
├── input.example.json
├── output.schema.json
├── resources/
│   └── README.md
└── tests/
    └── test_smoke.py
```

El script debe cumplir una interfaz común:

```bash
python run.py --input request.json --output result.json
```

También debe aceptar entrada por stdin y escribir salida por stdout cuando se use dentro de un pipeline:

```bash
cat request.json | python run.py > result.json
```

Reglas del script:

- leer únicamente la entrada declarada;
- validar que el JSON sea un objeto;
- devolver un resultado JSON completo;
- escribir errores operativos en stderr;
- no mezclar logs con stdout;
- devolver códigos de salida documentados;
- respetar timeout y cancelación;
- no ejecutar acciones externas no declaradas;
- no afirmar que realizó una operación que no ejecutó;
- incluir estado, advertencias y trazabilidad.

## 5. Componentes de la interfaz

### 5.1 Pantalla de nueva petición

```text
┌──────────────────────────────────────────────────────────────┐
│ Nueva petición                                                │
├──────────────────────────────────────────────────────────────┤
│ ¿Qué necesitas realizar?                                     │
│ [ Validar este CSV y generar un informe...                 ] │
│                                                              │
│ Entrada                                                       │
│ [ Pegar texto ] [ Subir archivo ] [ Usar ruta autorizada ]   │
│                                                              │
│ Formato de salida                                             │
│ [ Markdown ▼ ]                                                │
│                                                              │
│ Restricciones                                                 │
│ [x] No usar red     [x] No modificar archivos                │
│                                                              │
│                         [ Analizar petición ]                 │
└──────────────────────────────────────────────────────────────┘
```

### 5.2 Pantalla de decisión

```text
┌──────────────────────────────────────────────────────────────┐
│ Herramienta recomendada                                      │
├──────────────────────────────────────────────────────────────┤
│ phase-2-datos/validacion-de-datos                            │
│ Confianza de clasificación: 94 %                             │
│                                                              │
│ Motivos                                                      │
│ • Detectó una petición de validación de datos                │
│ • La entrada parece una tabla CSV                            │
│ • La salida solicitada es Markdown                           │
│ • No requiere red ni credenciales                            │
│                                                              │
│ Cuotas: disponible     Circuit breaker: CLOSED               │
│ Backend: worker aislado                                        │
│                                                              │
│ Alternativas: extractor de documentos                        │
│                                                              │
│ [ Cambiar herramienta ]             [ Ejecutar herramienta ]  │
└──────────────────────────────────────────────────────────────┘
```

### 5.3 Pantalla de ejecución y resultado

```text
┌──────────────────────────────────────────────────────────────┐
│ Ejecución                                                     │
├──────────────────────────────────────────────────────────────┤
│ Herramienta: phase-2-datos/validacion-de-datos                │
│ Worker: #w-1842       Tiempo: 1.12 s       Estado: LISTO     │
│ Cuota utilizada: 1 ejecución / 8 permitidas                  │
│ Circuit breaker: CLOSED                                       │
├──────────────────────────────────────────────────────────────┤
│ Resultado                                                     │
│ [ Informe Markdown                                           ] │
│                                                              │
│ Advertencias                                                 │
│ • No se consultaron servicios externos                       │
│                                                              │
│ Trazabilidad                                                 │
│ • Entrada: hash de solicitud                                 │
│ • Script: versión y ruta                                     │
│ • Contrato: 1.0                                              │
│                                                              │
│ [ Descargar ] [ Copiar ] [ Ejecutar otra petición ]          │
└──────────────────────────────────────────────────────────────┘
```

## 6. Selector: reglas deterministas y opción de modelo

La primera implementación debe utilizar un selector determinista basado en metadatos, etiquetas, fase, formatos y capacidades. Esto evita depender de un modelo externo para una operación crítica.

Un selector posterior puede incorporar un modelo de lenguaje para clasificar la intención, pero el modelo solo debe proponer candidatas. El runtime debe aplicar las reglas deterministas antes de ejecutar:

```text
modelo o reglas de intención
        ↓
lista de candidatas
        ↓
filtros de contrato y capacidades
        ↓
filtro de seguridad
        ↓
filtro de cuota y circuit breaker
        ↓
selección final o solicitud de confirmación
```

Nunca se debe permitir que una clasificación automática salte los controles de seguridad, cuota o contrato.

## 7. Peticiones compuestas

Algunas peticiones requieren más de una herramienta. Por ejemplo:

> Extrae los datos de este documento, valida los campos y genera un informe.

La interfaz debe distinguir entre:

- **herramienta única:** una herramienta ejecuta toda la petición;
- **pipeline:** varias herramientas se ejecutan en secuencia;
- **plan pendiente:** el sistema propone pasos, pero requiere confirmación antes de ejecutar.

Para la primera versión, la recomendación es permitir herramienta única y pipelines explícitos, pero no permitir que el selector cree cadenas complejas sin mostrar el plan completo.

Ejemplo de plan:

```json
{
  "steps": [
    {
      "order": 1,
      "tool_id": "phase-2-datos/extractor-de-datos-de-documentos",
      "input_from": "user_request"
    },
    {
      "order": 2,
      "tool_id": "phase-2-datos/validacion-de-datos",
      "input_from": "step_1.output"
    }
  ],
  "requires_confirmation": true
}
```

Cada paso debe tener cuotas, circuit breaker y trazabilidad propios. El pipeline completo debe tener también un límite global.

## 8. Qué cambia en la arquitectura

La arquitectura anterior debe añadir cuatro componentes:

```text
Interfaz de peticiones
        ↓
Request normalizer
        ↓
Tool router / decision engine
        ↓
Execution planner
        ↓
Supervisor → script de herramienta
```

El registro debe incluir campos adicionales:

```python
ToolMetadata(
    id="phase-2-datos/validacion-de-datos",
    phase="datos",
    capabilities=frozenset(),
    input_kinds=frozenset({"text", "csv", "table"}),
    output_formats=frozenset({"markdown", "json"}),
    tags=frozenset({"validacion", "calidad", "datos"}),
    entrypoint="...",
    script="toolkit/phase-2-datos/validacion-de-datos/run.py",
)
```

Sin estos metadatos, la interfaz puede listar herramientas, pero no puede seleccionar de forma explicable la más adecuada.

## 9. Criterios de aceptación de la interfaz

La interfaz de peticiones estará lista para una primera versión cuando:

1. Un usuario pueda escribir una petición sin conocer el slug.
2. El sistema muestre la herramienta recomendada y el motivo.
3. El usuario pueda cambiar la herramienta antes de ejecutar.
4. El sistema muestre capacidades, cuotas y estado del circuit breaker.
5. La solicitud normalizada sea visible y reproducible.
6. El runtime valide el contrato antes de invocar el script.
7. La herramienta seleccionada ejecute su script completo.
8. El resultado incluya estado, entregable, advertencias y trazabilidad.
9. Las herramientas existentes puedan seguir ejecutándose directamente por CLI.
10. Las peticiones ambiguas no se ejecuten silenciosamente.
11. Los pipelines muestren todos sus pasos antes de ejecutarse.
12. Las decisiones automáticas puedan auditarse posteriormente.

## 10. Conclusión

La interfaz de peticiones debe ser una capa superior al catálogo y al runtime. Su función es traducir la intención del usuario, seleccionar una herramienta explicando el motivo, validar que la ejecución sea permitida y delegar el trabajo completo al script específico de la herramienta.

Por tanto, sí: **cada herramienta debe conservar su propio script**. El framework debe proporcionar el sistema operativo de la herramienta —descubrimiento, selección, contratos, cuotas, aislamiento, ejecución y trazabilidad—, mientras que el script contiene la lógica concreta del dominio.

Esta separación permite que una herramienta se ejecute de tres formas sin duplicar su lógica:

```text
Interfaz de usuario → router → supervisor → script
CLI directa         → registro → supervisor → script
API programática    → runtime → supervisor → script
```

## Referencias

[1]: https://github.com/hubgunter4-ops/content-skills-toolkit "Repositorio Content Skills Toolkit"
[2]: https://packaging.python.org/specifications/entry-points/ "Entry points specification — Python Packaging User Guide"
