---
name: optimizador-de-contenido-de-blog
description: Esta habilidad reescribe y optimiza entradas de blog existentes para mejorar tanto el posicionamiento en Google como las citas de asistentes de IA. Reemplaza automáticamente estadísticas inventadas con datos reales de fuentes, genera gráficos SVG y aplica un formato de respuesta primero, ayudando a los creadores de contenido a actualizar fácilmente artículos obsoletos y aumentar su visibilidad en motores de búsqueda y plataformas de IA.
---

# Optimizador de Contenido de Blog

## Propósito

Esta habilidad reescribe y optimiza entradas de blog existentes para mejorar tanto el posicionamiento en Google como las citas de asistentes de IA. Reemplaza automáticamente estadísticas inventadas con datos reales de fuentes, genera gráficos SVG y aplica un formato de respuesta primero, ayudando a los creadores de contenido a actualizar fácilmente artículos obsoletos y aumentar su visibilidad en motores de búsqueda y plataformas de IA.

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
