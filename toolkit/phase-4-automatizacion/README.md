# Fase 4: Automatización

## Objetivo

Construir herramientas de automatización reproducibles para descubrimiento, extracción autorizada, workflows, MCP, CI/CD, observabilidad, agentes y automatización de navegador. El catálogo contiene **23 subherramientas** derivadas del documento fuente.

## Flujo de trabajo

1. Definir disparador, objetivo, entradas, acciones permitidas, destino y criterio de parada.
2. Inspeccionar permisos, secretos, dominios, ramas, frecuencia, reintentos y efectos.
3. Diseñar primero modo observación, simulación o propuesta.
4. Aplicar allowlists, permisos mínimos, límites de volumen, timeouts e idempotencia.
5. Ejecutar solo el alcance autorizado y registrar un resumen auditable.
6. Verificar resultados, detener ante errores repetidos y documentar apagado y reversión.

## Herramientas incluidas

El catálogo cubre buscadores de skills, extracción web, búsqueda y recomendación, n8n, protección de comandos, Vercel Workflow, GCP, Grafana, SLO, fuentes MCP, roles de Azure, Selenium, Claude Code, agentes, MCP CLI, Chrome DevTools, CI/CD y Puppeteer.

## Guardrails

La implementación no evade Cloudflare, CAPTCHA, autenticación, robots, límites ni controles de plataforma. No ejecuta comandos destructivos, instala skills, conecta servidores MCP, publica, despliega, cambia permisos, modifica infraestructura ni envía datos externos por defecto.

Las integraciones con GitHub, n8n, Vercel, MCP, GCP, Azure, Grafana, Chrome DevTools, Selenium, Puppeteer y APIs externas requieren una solicitud explícita, configuración autorizada, credenciales separadas y alcance documentado. Los runners locales generan planes o artefactos revisables.

## Estructura

Cada subcarpeta contiene `SKILL.md`, `run.py`, `input.example.json`, `output.schema.json`, `resources/` y `tests/`. El catálogo `catalog.json` conserva nombres y descripciones. Las métricas de uso y estrellas del documento fuente no se incorporan como afirmaciones del proyecto.

## Validación

```bash
python3 -m compileall -q toolkit/phase_4_engine.py toolkit/phase-4-automatizacion
python3 toolkit/phase-4-automatizacion/tests/test_phase4.py
```

No se deben afirmar ejecuciones externas, despliegues o automatizaciones activas sin evidencia de una ejecución autorizada.
