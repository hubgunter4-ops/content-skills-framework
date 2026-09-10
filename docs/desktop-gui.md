# GUI de escritorio del Content Skills Framework

La GUI funcional vive en `desktop/` y conserva la separación definida por la arquitectura:

```text
GUI local → /api/route → router determinista → decisión explicable
GUI local → /api/run → cuotas + circuit breaker + supervisor → run.py
```

La aplicación abre un servidor local en `127.0.0.1:8765` y el navegador predeterminado. No expone el servidor en la red y no envía la petición a servicios externos. El panel muestra la petición normalizada, la herramienta recomendada, confianza, razones, alternativas, resultado y métricas locales.

## Ejecución desde el repositorio

```bash
python3 desktop/server.py
```

Abrir `http://127.0.0.1:8765/` si el navegador no se inicia automáticamente.

Endpoints:

- `GET /api/health`;
- `GET /api/metrics`;
- `POST /api/route`;
- `POST /api/run`.

La GUI no ejecuta una selección ambigua: el backend solo devuelve un plan cuando el router no requiere confirmación. El modelo LLM opcional permanece desactivado por defecto y no se invoca desde esta primera GUI.

## Debian

El script `packaging/build-deb.sh` produce:

```text
dist/content-skills-framework_0.3.1_all.deb
```

Instalación:

```bash
sudo dpkg -i content-skills-framework_0.3.1_all.deb
content-skills-framework
```

El paquete instala la aplicación bajo `/opt/content-skills-framework`, un launcher en `/usr/bin` y una entrada de menú `.desktop`.

## Windows

El workflow `desktop.yml` usa Windows nativo y PyInstaller para generar:

```text
ContentSkillsFramework-windows-x64.zip
```

El ejecutable abre el navegador local y almacena el índice en la carpeta de usuario. El artefacto se publica automáticamente en la release cuando se crea un tag `v*`.

## Alcance de la primera versión

La primera GUI incluye petición, routing, ejecución y métricas. Historial persistente, gestión visual de herramientas y carga de archivos quedan como iteraciones siguientes; el CLI y las APIs públicas continúan disponibles para esos casos.
