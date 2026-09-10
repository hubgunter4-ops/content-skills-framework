# Plugin de ejemplo: analizador de legibilidad

Este directorio muestra cómo un paquete externo puede registrar una herramienta mediante el entry point `content_skills_toolkit.tools`.

El ejemplo depende de la API pública propuesta del framework:

```bash
python -m pip install -e /ruta/al/framework
python -m pip install -e .
python host_demo.py
```

El plugin no es ejecutable contra la revisión actual del repositorio porque las clases `ToolMetadata`, `ExecutionRequest` y `ExecutionResult` forman parte de la API futura del framework descrita en la documentación. La intención es fijar el contrato y la estructura de distribución antes de implementarla.

El plugin no usa red, credenciales, escritura de archivos ni procesos hijos. Su resultado es heurístico y debe ser revisado editorialmente.
