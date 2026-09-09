# Fase 2: Datos

## Objetivo

Construir herramientas reproducibles para ingestión, limpieza, validación, análisis, visualización, modelado, consultas y exportación de datos. Cada habilidad vive en una subcarpeta independiente con instrucciones, runner, ejemplo JSON, esquema de salida, recursos y prueba smoke.

## Habilidades incluidas

El catálogo de `catalog.json` contiene 57 subherramientas derivadas del documento de instrucciones. Las capacidades cubren análisis financiero y de acciones, Excel, tráfico web, dashboards, extracción, SQL, datos científicos, validación, visualización, estadística, riesgo, contratos, búsqueda, bases de datos, machine learning, big data, grafos y pipelines.

## Flujo de trabajo común

1. **Definir la pregunta.** Registrar objetivo, audiencia, formato, periodo, unidad de análisis y criterio de éxito.
2. **Registrar la fuente.** Conservar archivo o URL, fecha de extracción, versión, licencia y permisos.
3. **Inspeccionar el esquema.** Detectar columnas, tipos, faltantes, duplicados, rangos, unidades y codificaciones.
4. **Validar antes de transformar.** Separar errores de datos, supuestos y decisiones metodológicas.
5. **Transformar reproduciblemente.** Aplicar pasos explícitos, deterministas y trazables.
6. **Analizar.** Elegir métricas y métodos adecuados al diseño, evitando inferencias no justificadas.
7. **Visualizar.** Etiquetar unidades, fuentes, incertidumbre y accesibilidad; no usar color como único canal.
8. **Exportar.** Entregar tablas, gráficos, consultas, HTML o informes con metadatos y fecha de corte.
9. **Revisar.** Comprobar resultados, sesgo de supervivencia, sensibilidad, reproducibilidad y límites.

## Contrato de entrada

Los runners aceptan JSON por stdin o por `--input` con `objective`, `audience`, `content` y `format`. La entrada debe contener datos reales proporcionados por el usuario o una referencia autorizada. No se generan datasets simulados para presentarlos como evidencia.

## Integraciones externas

No se cargan integraciones por defecto. Las herramientas financieras, tráfico web, fuentes científicas, Hacker News, datos fiscales, Power BI, MongoDB, Similarweb, Ahrefs, Semrush, APIs SEC, proveedores de mercado, bases públicas o plataformas ML solo deben conectarse cuando el usuario incluya explícitamente `integration` o `integrations` y exista autorización, endpoint y credencial adecuados.

La extracción web no evade Cloudflare, CAPTCHA, controles anti-bot ni permisos. Los datos sensibles y credenciales no se guardan en esta carpeta.

## Pruebas

Cada subcarpeta contiene una prueba smoke. Desde el repositorio, la verificación inicial puede ejecutarse con:

```bash
python3 -m compileall -q toolkit/phase_2_engine.py toolkit/phase-2-datos
python3 toolkit/phase-2-datos/tests/test_phase2.py
```

## Estado de implementación

La primera iteración incluye contratos, runners, plantillas, análisis local básico, resúmenes numéricos, controles QA, HTML offline, SVG, matrices y planes reproducibles. Las conexiones a servicios externos y los formatos binarios como XLSX, Parquet, HDF5, DOCX o PPTX quedan aislados como extensiones explícitas y requieren dependencias y autorización adicionales.
