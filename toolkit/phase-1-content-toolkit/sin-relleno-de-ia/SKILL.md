---
name: sin-relleno-de-ia
description: Una habilidad de edición que elimina más de 20 patrones reveladores de relleno de IA de tus borradores mientras preserva tu voz personal. Consigue una redacción que se lea más nítida, más humana y sea inconfundiblemente tuya.
---

# Sin relleno de IA

## Propósito

Una habilidad de edición que elimina más de 20 patrones reveladores de relleno de IA de tus borradores mientras preserva tu voz personal. Consigue una redacción que se lea más nítida, más humana y sea inconfundiblemente tuya.

## Flujo de trabajo

1. **Definir el encargo.** Identifica audiencia, objetivo, idioma, formato de salida, restricciones y criterios de éxito antes de producir contenido.
2. **Reunir entradas.** Separa material aportado por el usuario de datos que requieren investigación. No inventes fuentes, resultados, métricas ni ejemplos presentados como hechos.
3. **Planificar la salida.** Construye un esquema verificable: afirmaciones o secciones, evidencia necesaria, tono, estructura y controles de calidad.
4. **Ejecutar la transformación.** Produce el resultado respetando el formato solicitado, conservando datos, enlaces, metadatos y marcas que no estén autorizados para cambiar.
5. **Revisar y entregar.** Comprueba exactitud, claridad, consistencia, accesibilidad, trazabilidad y cumplimiento de las restricciones. Señala incertidumbres y decisiones pendientes.

## Entradas aceptadas

- Solicitud del usuario y audiencia objetivo.
- Texto, Markdown, URLs, transcripciones, tablas o archivos proporcionados.
- Restricciones de marca, estilo, idioma, longitud, formato y fecha de corte.
- Fuentes externas sólo cuando el usuario autorice investigación o las solicite explícitamente.

## Salida esperada

Entrega un resultado autocontenido en el formato pedido. Incluye un resumen breve de decisiones, una sección de supuestos y, cuando corresponda, una tabla de fuentes o un registro de cambios. Conserva la información original relevante y separa hechos, inferencias y recomendaciones.

## Guardrails

- No publiques, envíes, compres, borres ni modifiques sistemas externos sin autorización explícita.
- No presentes contenido generado como evidencia primaria ni afirmes que una fuente fue consultada si no lo fue.
- No inventes estadísticas, citas, URLs, resultados de pruebas, testimonios o credenciales.
- Respeta derechos de autor, privacidad, datos sensibles y las políticas de la plataforma de destino.
- Si una entrada es insuficiente, formula preguntas concretas o declara el límite en lugar de rellenar con suposiciones.

## Plantilla de solicitud

```text
Objetivo: [qué necesito conseguir]
Audiencia: [quién leerá o usará el resultado]
Entradas: [archivos, texto, URLs o datos]
Idioma y tono: [preferencias]
Formato: [Markdown, tabla, JSON, HTML, PDF, etc.]
Restricciones: [longitud, marca, fuentes, fecha de corte]
Criterio de éxito: [cómo se evaluará]
```

## Lista de control

- [ ] El objetivo y la audiencia están definidos.
- [ ] Las entradas y fuentes están diferenciadas.
- [ ] Las afirmaciones importantes tienen respaldo o están marcadas como inciertas.
- [ ] El formato y el idioma cumplen la solicitud.
- [ ] No se alteraron datos o metadatos fuera del alcance.
- [ ] La salida incluye limitaciones y próximos pasos cuando son relevantes.

## Runner asociado

- **Runner:** `toolkit/phase-1-content-toolkit/sin-relleno-de-ia/run.py`
- **Motor:** `toolkit/skill_engine.py`
- **Entrada de ejemplo:** `toolkit/phase-1-content-toolkit/sin-relleno-de-ia/input.example.json`
- **Esquema de salida:** `toolkit/phase-1-content-toolkit/sin-relleno-de-ia/output.schema.json`
- **Prueba smoke:** `toolkit/phase-1-content-toolkit/sin-relleno-de-ia/tests/test_smoke.py`

La documentación debe mantenerse sincronizada con el runner, el contrato JSON y el comportamiento local de la herramienta.
