---
name: validacion-de-datos
description: Realiza controles de calidad QA en los análisis antes de compartirlos con las partes interesadas, comprobando la metodología, verificando la precisión y detectando fuentes de sesgo para aumentar la confianza. Valida la lógica de agregación, señala el posible sesgo de supervivencia y las brechas de reproducibilidad.
---

# Validación de datos

## Propósito

Esta herramienta prepara una revisión de calidad de un análisis antes de compartirlo con partes interesadas. Organiza controles sobre la entrada recibida, la existencia de filas estructuradas, los valores faltantes, los posibles duplicados, el sesgo de supervivencia y la reproducibilidad.

El runner realiza un análisis local y determinista del contenido proporcionado. Puede detectar filas cuando recibe texto tabular delimitado por comas o tabulaciones y puede contar valores numéricos. No sustituye una auditoría estadística, una revisión metodológica de dominio ni una verificación independiente de las fuentes.

## Runner asociado

La cadena de ejecución actualmente soportada para esta herramienta es:

```text
python3 toolkit/phase-2-datos/validacion-de-datos/run.py
        └── toolkit/phase_2_engine.py::run_tool
```

El archivo `toolkit/__main__.py` es el dispatcher del CLI del repositorio. Su comando `run` resuelve actualmente las herramientas ubicadas en `skills/content-toolkit/`; no despacha todavía las herramientas de las fases especializadas. Por ello, esta herramienta se ejecuta directamente mediante su runner de fase porque está ubicada bajo `toolkit/phase-2-datos/`.

Para ejecutar esta herramienta desde la raíz del repositorio:

```bash
python3 toolkit/phase-2-datos/validacion-de-datos/run.py \
  --input toolkit/phase-2-datos/validacion-de-datos/input.example.json
```

También acepta JSON por entrada estándar:

```bash
cat toolkit/phase-2-datos/validacion-de-datos/input.example.json \
  | python3 toolkit/phase-2-datos/validacion-de-datos/run.py
```

El runner puede escribir el JSON resultante en un archivo mediante `--output`:

```bash
python3 toolkit/phase-2-datos/validacion-de-datos/run.py \
  --input entrada.json \
  --output resultado.json
```

El runner específico importa `run_tool` desde `toolkit/phase_2_engine.py` y le entrega el diccionario JSON validado. El motor selecciona el adaptador de `validacion-de-datos`, genera el entregable Markdown y devuelve el contrato con `skill`, `status`, `analysis`, `deliverable` y `warnings`.

Estados de salida relevantes:

| Estado | Significado | Código del proceso |
| --- | --- | ---: |
| `ready` | Se generó el entregable local | `0` |
| `needs_input` | Faltan `objective`, `audience`, `content` o `format` | `1` |
| `error` | JSON inválido, archivo ilegible o entrada no válida | `2` |

La asociación normativa de esta documentación es el runner específico `toolkit/phase-2-datos/validacion-de-datos/run.py`; `toolkit/phase_2_engine.py` es su motor compartido y `toolkit/__main__.py` es el dispatcher general del repositorio.

## Flujo de trabajo

1. **Definir la revisión.** Especificar el objetivo, la audiencia, el formato de salida y el análisis que se desea revisar.
2. **Recibir la entrada.** Proporcionar el contenido disponible, preferiblemente con encabezados y filas delimitadas si se requiere comprobar estructura tabular.
3. **Inspeccionar el corpus local.** Identificar si existen filas estructuradas, valores numéricos y contenido suficiente para producir un diagnóstico inicial.
4. **Aplicar controles QA.** Registrar si la entrada no está vacía, si se detectan filas, y qué controles requieren una revisión adicional sobre faltantes, duplicados, sesgo de supervivencia y reproducibilidad.
5. **Separar evidencia de pendientes.** Diferenciar lo observado automáticamente de lo que aún necesita una persona responsable del análisis o del dominio.
6. **Revisar antes de compartir.** Comprobar la metodología, los outliers, la lógica de agregación, las fuentes, la fecha de corte y las transformaciones antes de comunicar conclusiones.

## Entradas aceptadas

La entrada es un objeto JSON con estos campos obligatorios:

| Campo | Tipo | Obligatorio | Uso |
| --- | --- | --- | --- |
| `objective` | Cadena | Sí | Define el propósito de la revisión. |
| `audience` | Cadena | Sí | Identifica quién utilizará el resultado. |
| `content` | Cadena | Sí | Contiene el análisis, texto, tabla o resumen que se revisará. |
| `format` | Cadena | Sí | Indica el formato solicitado para el entregable, por ejemplo `markdown`. |

Ejemplo mínimo:

```json
{
  "objective": "Revisar la calidad de un análisis de ventas",
  "audience": "Analista de datos y responsable de negocio",
  "content": "region,ventas\nNorte,120\nSur,95\nNorte,120",
  "format": "markdown"
}
```

El campo opcional `integration` o `integrations` puede indicar una integración externa solicitada explícitamente. La herramienta no debe interpretar su presencia como autorización suficiente para consultar un servicio: cualquier conexión requiere un conector, credencial y autorización configurados fuera de este archivo.

## Salida esperada

El runner devuelve un objeto JSON con estos campos de primer nivel:

| Campo | Contenido |
| --- | --- |
| `skill` | Nombre, descripción y slug de la herramienta. |
| `status` | `ready`, `needs_input` o `not_loaded`, según el flujo ejecutado. |
| `analysis` | Campos ausentes, caracteres y palabras recibidos, y supuestos aplicados. |
| `deliverable` | Título, formato, contenido de la revisión y próximos pasos. |
| `warnings` | Advertencias sobre entradas incompletas o integraciones no cargadas. |

Cuando la entrada es válida, el entregable se estructura en Markdown con:

1. **Resumen:** filas detectadas, valores numéricos y, cuando corresponde, columnas, mínimo, máximo, media y mediana.
2. **QA:** controles de entrada no vacía, filas estructuradas, valores faltantes, duplicados, sesgo de supervivencia y reproducibilidad.
3. **Decisión:** condición de revisión previa a compartir el análisis.

Los controles de valores faltantes y duplicados no se presentan como resultados definitivos cuando no existe una clave o estructura suficiente. Se marcan como elementos que requieren inspección.

## Guardrails

- No inventar filas, métricas, fuentes, resultados estadísticos ni decisiones de negocio.
- No tratar una entrada de ejemplo como evidencia de un dataset real.
- No afirmar que se comprobó la precisión metodológica si sólo se realizaron controles locales de estructura y conteo.
- No afirmar que se detectaron todos los duplicados sin una clave, regla de unicidad o definición de entidad.
- No afirmar que se descartó el sesgo de supervivencia; sólo se señala como control que debe revisarse.
- No afirmar reproducibilidad sin registrar fuente, fecha, versión y transformaciones.
- No sustituir valores faltantes ni corregir outliers automáticamente.
- No consultar bases de datos, APIs, fuentes regulatorias o servicios de terceros por defecto.
- No exponer credenciales, tokens, datos personales ni información sensible en `content`, `resources/` o la salida.
- No compartir el resultado como aprobación metodológica definitiva sin revisión de una persona responsable del dominio.
- Si faltan `objective`, `audience`, `content` o `format`, devolver un estado de entrada incompleta en vez de rellenar los campos con suposiciones.

## Plantilla de solicitud

```text
Objetivo: [qué análisis se desea revisar]
Audiencia: [quién leerá el informe]
Contenido: [tabla, consulta, resumen o análisis proporcionado]
Formato: [markdown, json u otro formato compatible]
Fuente y fecha de corte: [origen de los datos y periodo analizado]
Unidad de análisis: [cliente, transacción, sesión, producto u otra entidad]
Clave de unicidad: [campo o combinación de campos, si existe]
Reglas de calidad: [rangos, restricciones, tolerancias o criterios esperados]
Transformaciones realizadas: [limpieza, filtros, joins, agregaciones y versiones]
Restricciones: [privacidad, permisos, límites de uso y revisiones requeridas]
Criterio de éxito: [qué debe quedar claro antes de compartir el análisis]
```

## Lista de control

### Entrada y alcance

- [ ] El objetivo de la revisión está definido.
- [ ] La audiencia y el uso previsto están documentados.
- [ ] El contenido fue proporcionado por una fuente autorizada.
- [ ] La unidad de análisis y el periodo están identificados.

### Calidad y metodología

- [ ] Se confirmó si la entrada contiene filas estructuradas.
- [ ] Se revisaron tipos, rangos, unidades y valores numéricos.
- [ ] Se definieron las reglas para valores faltantes.
- [ ] Se definió la clave o regla para detectar duplicados.
- [ ] Se revisaron outliers y valores imposibles sin reemplazarlos automáticamente.
- [ ] Se verificó la lógica de filtros, joins y agregaciones.
- [ ] Se consideró qué población quedó fuera y el posible sesgo de supervivencia.

### Trazabilidad y reproducibilidad

- [ ] La fuente y la fecha de corte están registradas.
- [ ] Las transformaciones y versiones relevantes están documentadas.
- [ ] Las decisiones analíticas pueden repetirse con las mismas entradas.
- [ ] Los resultados observados están separados de hipótesis y recomendaciones.

### Entrega responsable

- [ ] Las advertencias del runner fueron revisadas.
- [ ] No se presentan controles pendientes como aprobaciones definitivas.
- [ ] No se incluyen credenciales ni datos sensibles.
- [ ] Una persona responsable del dominio revisó el resultado antes de compartirlo.
- [ ] Se registraron los próximos pasos para los controles que el runner no puede resolver automáticamente.

## Límites de implementación

Esta documentación describe el comportamiento actual de `toolkit/phase_2_engine.py` para `validacion-de-datos`. El runner genera una revisión estructurada y controles de QA; no ejecuta por sí solo una auditoría estadística completa, un modelo de detección de anomalías, una consulta externa, una validación contractual ni una aprobación de publicación.
