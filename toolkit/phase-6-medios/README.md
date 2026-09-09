# Fase 6: Medios

## Objetivo

Crear herramientas reproducibles para producción de video, animación, prompts audiovisuales, TTS, subtítulos, transcripción, imágenes, música, storyboards y edición. El catálogo contiene **49 subherramientas** derivadas del documento fuente.

## Flujo de trabajo

1. Definir objetivo, audiencia, derechos de uso, formato, duración, plataforma y criterio de éxito.
2. Inspeccionar material, codecs, metadatos, licencias, identidad y restricciones antes de modificar.
3. Crear storyboard, prompt, subtítulo, receta o plan de producción editable.
4. Validar sincronización, accesibilidad, calidad, continuidad, derechos y exportación.
5. Entregar el artefacto y registrar supuestos, fuentes y límites.

## Herramientas incluidas

El catálogo cubre creación de videos HTML, Manim, TTS Prompter, videos para redes, shorts, anuncios y campañas, UGC, transcripción, motion graphics, dirección cinematográfica, prompts para modelos audiovisuales, ImageMagick, subtítulos, selección de modelos, música, Remotion, efectos de títulos, HyperFrames y producción de escenas.

## Guardrails de promoción responsable

No se genera ni publica audio, video o imagen sin solicitud explícita y revisión. No se clona voz, rostro, identidad o estilo protegido sin autorización. No se usa material con derechos dudosos ni se presenta una maqueta como render final. No se llaman APIs de video, música, TTS, transcripción o imágenes por defecto.

Los runners generan planes, storyboards, prompts, SRT/WebVTT, HTML, SVG y comandos revisables localmente. La generación binaria, el render, el procesamiento de archivos y los conectores externos requieren material, dependencia, credenciales y autorización explícita.

## Estructura

Cada subcarpeta contiene `SKILL.md`, `run.py`, `input.example.json`, `output.schema.json`, `resources/` y `tests/`. El catálogo `catalog.json` conserva nombres y descripciones del documento fuente. Las métricas de uso y estrellas se omiten del catálogo.

## Validación

```bash
python3 -m compileall -q toolkit/phase_6_engine.py toolkit/phase-6-medios
python3 toolkit/phase-6-medios/tests/test_phase6.py
```

No deben afirmarse renders, transcripciones, generaciones o publicaciones sin una ejecución autorizada y evidencia revisada.
