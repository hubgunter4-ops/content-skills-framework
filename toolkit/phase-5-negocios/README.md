# Fase 5: Diseño

## Objetivo

Crear herramientas reproducibles para UI/UX, sistemas de diseño, animación, accesibilidad, diagramas, dashboards, maquetas, paletas, Canvas y documentación visual. El catálogo contiene **34 subherramientas** derivadas del documento fuente.

## Flujo de trabajo

1. Definir audiencia, objetivo, contenido, plataforma, formato y criterios de éxito.
2. Inspeccionar referencias, tokens, accesibilidad, permisos y datos antes de modificar.
3. Diseñar una propuesta editable, consistente y reversible.
4. Validar responsive, contraste, teclado, legibilidad, rendimiento y coherencia visual.
5. Entregar artefactos, decisiones, supuestos y límites.

## Artefactos incluidos

Los runners locales pueden producir HTML/CSS, SVG, Mermaid, PlantUML, JSON Canvas, JSON Excalidraw, Markdown Marp, tokens CSS, favicons SVG, checklists de accesibilidad, esquemas de dashboard y revisiones de animación.

## Guardrails de promoción responsable

No se afirma que se haya generado una imagen, video, captura o archivo binario sin producirlo y revisarlo. No se usan logos, fuentes, datos ni assets sin permiso o licencia clara. No se envía contenido a APIs de imagen, diseño, MCP o navegador sin solicitud explícita. Se mantiene la accesibilidad, privacidad y reversibilidad como criterio de aceptación.

Las herramientas no activan servicios externos ni incorporan dependencias nuevas por defecto. Chart.js, GSAP, Penpot, Excalidraw, Mermaid, PlantUML y otros runtimes externos quedan como extensiones explícitas; los runners entregan artefactos locales revisables.

## Estructura

Cada subcarpeta contiene `SKILL.md`, `run.py`, `input.example.json`, `output.schema.json`, `resources/` y `tests/`. El catálogo `catalog.json` conserva los nombres y descripciones del documento fuente.

## Validación

```bash
python3 -m compileall -q toolkit/phase_5_engine.py toolkit/phase-5-negocios
python3 toolkit/phase-5-negocios/tests/test_phase5.py
```

Las capturas reales, publicaciones y assets generados deben revisarse antes de incluirse en un release. Una maqueta local no debe presentarse como evidencia de una aplicación desplegada.
