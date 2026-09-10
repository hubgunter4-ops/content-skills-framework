# Plugin de ejemplo: analizador de legibilidad

Este directorio muestra cómo un paquete externo puede registrar una herramienta mediante el entry point `content_skills_toolkit.tools`.

El ejemplo depende de la API pública propuesta del framework:

```bash
python -m pip install -e /ruta/al/framework
python -m pip install -e .
python host_demo.py
```

El plugin usa las clases públicas `ToolMetadata`, `ExecutionRequest` y `ExecutionResult` de la release interna `0.3.0`. El host puede descubrirlo mediante el grupo `content_skills_toolkit.tools`; el índice lee la declaración del entry point sin importar ni ejecutar el plugin durante el descubrimiento.

El plugin no usa red, credenciales, escritura de archivos ni procesos hijos. Su resultado es heurístico y debe ser revisado editorialmente.
