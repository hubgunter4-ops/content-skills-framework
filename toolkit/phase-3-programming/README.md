# Fase 3: Programming

## Objetivo

Crear herramientas de ingeniería de software reproducibles para diseñar, implementar, depurar, probar, documentar y operar sistemas. El catálogo contiene **89 subherramientas** derivadas del documento de instrucciones adjunto.

## Flujo de trabajo obligatorio

1. **Inspeccionar sin modificar.** Revisar repositorio, código, configuración, dependencias, pruebas y reglas de contribución.
2. **Definir especificación.** Documentar objetivo, entradas, salidas, restricciones, runtime y criterios de aceptación.
3. **Diseñar el cambio mínimo.** Mantener compatibilidad, reversibilidad y separación entre plan y ejecución.
4. **Implementar con pruebas.** Priorizar TDD, casos límite, errores y pruebas de regresión.
5. **Verificar.** Ejecutar comandos actualizados, revisar diff, compilación, pruebas, seguridad y artefactos.
6. **Entregar.** Informar archivos, comandos, resultados, riesgos y acciones externas no realizadas.

## Categorías incluidas

El catálogo cubre prompting, rendimiento, diseño de skills, CLAUDE.md, memoria, GSAP, accesibilidad, Tailwind, SQL, debugging, Markdown, Gemini, Excalidraw, comandos destructivos, workflows, verificación, plugins, APIs, Mermaid, GCP, Grafana, SLO, Git, Stripe, Supabase, MongoDB, vector search, Remotion, Microsoft, Selenium, MLOps, SecOps, dependencias, observabilidad, GraphQL, AWS Serverless, React Email, Airflow, dbt y otras herramientas del documento fuente.

## Guardrails de promoción responsable

No se ejecutan comandos destructivos, despliegues, commits, pushes, cambios de permisos, llamadas cloud, actualizaciones de dependencias ni operaciones externas desde los runners. La herramienta de protección marca comandos de riesgo y exige una confirmación fuera del runner. No se evaden CAPTCHA, Cloudflare ni controles de acceso. Las integraciones, SDKs y credenciales solo se añaden cuando el usuario los solicita explícitamente.

## Estructura por subherramienta

Cada carpeta incluye `SKILL.md`, `run.py`, `input.example.json`, `output.schema.json`, `resources/` y `tests/`. `catalog.json` conserva nombres y descripciones del documento fuente. Las descripciones incompletas se marcan como tales y no se rellenan con afirmaciones inventadas.

## Validación

```bash
python3 -m compileall -q toolkit/phase_3_engine.py toolkit/phase-3-programming
python3 toolkit/phase-3-programming/tests/test_phase3.py
```

La implementación inicial genera planes y artefactos locales como HTML, Mermaid, JSON Excalidraw, contratos OpenAPI, checklists SQL, flujos TDD, revisiones de rendimiento y guardrails de comandos. Los conectores oficiales de Gemini, GCP, AWS, Azure, Stripe, Supabase, Grafana, MongoDB, GitHub y otros servicios quedan fuera de línea hasta recibir una solicitud explícita y configuración autorizada.
