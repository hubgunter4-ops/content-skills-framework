# Auditoría de seguridad — 0.3.1

Fecha de ejecución: 2026-09-10.

## Alcance

Se revisaron el código Python de `toolkit/` y `desktop/`, el paquete Debian, el historial Git, los patrones de secretos y las dependencias declaradas por `pyproject.toml`. La validación de instalación se ejecutó en un rootfs mínimo de Debian Bookworm con Python 3.11.

## Resultados

| Control | Resultado |
| --- | --- |
| Suite del proyecto | 89 pruebas, `OK` |
| Compilación Python 3.11 | Correcta para `toolkit/` y `desktop/` |
| Instalación Debian limpia | Correcta mediante `dpkg -i` |
| Smoke test GUI | Correcto: health, catálogo de 304 herramientas y routing |
| Bandit | 0 hallazgos altos; hallazgos restantes son subprocess controlado y red validada |
| pip-audit del entorno limpio | Sin vulnerabilidades conocidas en las dependencias instaladas del entorno del proyecto; el proyecto no está publicado en PyPI |
| Búsqueda local de secretos | No encontró claves privadas, tokens conocidos ni credenciales incrustadas |
| Dependabot / Secret Scanning API | No verificable con el token disponible: GitHub respondió `403 Resource not accessible by integration` |

## Controles aplicados en 0.3.1

Los endpoints HTTP de integraciones solo aceptan `http` y `https`, requieren un host resoluble y rechazan direcciones privadas, loopback, link-local y reservadas. El circuit breaker ya no depende de `assert` para lógica de producción. Los subprocess quedan limitados a runners resueltos por el registro local o por el supervisor, con workspace temporal, entorno filtrado, timeout y límites de recursos.

## Límites

La revisión no constituye una certificación formal ni sustituye un pentest. El aislamiento `subprocess-limited` no es un sandbox de kernel completo. La consulta de alertas nativas de GitHub debe repetirse con una credencial que tenga permisos de lectura de Dependabot, Secret Scanning y Code Scanning.

## Reproducción

```bash
python3 -m unittest discover -s tests
python3 -m bandit -r toolkit desktop -x '*/tests/*'
python3 -m pip_audit --local
sudo dpkg -i dist/content-skills-framework_0.3.1_all.deb
```
