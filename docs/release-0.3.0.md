# Content Skills Framework 0.3.0 — Release interna

## Alcance

La release interna 0.3.0 convierte el catálogo de Content Skills Toolkit en un framework operable para descubrir, enrutar y ejecutar herramientas con contratos públicos, índice persistente, caché, modularización por fases, LLM opcional, sandbox, cuotas, circuit breakers, observabilidad y CI.

## Instalación del core

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install content_skills_toolkit-0.3.0-py3-none-any.whl
python -m toolkit validate
```

Para desarrollo local:

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
```

## Instalación por fases

El core incluye el catálogo y los módulos de las seis fases actuales. Las fases externas pueden distribuirse como paquetes independientes usando entry points:

```toml
[project.entry-points."content_skills_toolkit.tools"]
community-analizador-de-legibilidad = "plugin:create_tool"
```

Después de instalar un plugin:

```bash
python -m toolkit index --db .content-skills-index.sqlite3
python -m toolkit list
python -m toolkit route "Analiza la legibilidad de este texto"
```

El descubrimiento lee las declaraciones instaladas; no importa ni ejecuta objetos de terceros para construir el índice.

## Flujo recomendado

1. Normalizar la petición.
2. Obtener una selección determinista o una sugerencia LLM validada.
3. Confirmar la herramienta cuando la selección sea ambigua.
4. Adquirir circuit breaker y cuotas.
5. Ejecutar mediante `Supervisor` con un perfil de sandbox.
6. Liberar la cuota y registrar el resultado.
7. Revisar métricas y errores antes de automatizar una promoción.

## Seguridad operativa

Para plugins de terceros se recomienda `third-party`; para código no confiable, `untrusted`. Estos perfiles son aislamiento por proceso con límites, no una máquina virtual ni un contenedor de kernel completo. El despliegue que procese código arbitrario debe añadir un backend de contenedor sin privilegios antes de exponerlo a usuarios no confiables.

## Migración desde el CLI original

| CLI anterior | Framework 0.3.0 |
| --- | --- |
| `python -m toolkit list` | Se mantiene; ahora puede consultar índice persistente. |
| `python -m toolkit show phase/slug` | Se mantiene y usa identificadores cualificados. |
| `python -m toolkit run phase/slug -i file.json` | Se mantiene para ejecución local directa. |
| Selección manual de herramienta | `python -m toolkit route "petición"` antes de ejecutar. |
| Ejecución en proceso host | `Supervisor.run_script(...)` con sandbox. |
| Sin límites por usuario | `QuotaManager` con scopes host/fase/tool/tenant. |
| Sin protección ante fallos repetidos | `CircuitBreakerManager`. |

## Compatibilidad

| Componente | Soporte de release | Verificación |
| --- | --- | --- |
| Python | 3.10+ | `pyproject.toml`, compile y suite |
| Python validado localmente | 3.12.3 | Suite completa |
| Linux | Soporte principal | `resource`, sesiones y límites |
| Windows/macOS | Subproceso y timeout básicos; límites OS reducidos | CI adicional recomendado |
| Dependencias runtime | Biblioteca estándar | Instalación limpia del wheel |
| Catálogo | 304 herramientas | `python -m toolkit validate` |
| Entry points | `content_skills_toolkit.tools` | Índice persistente |
| LLM | Opcional | Fallback determinista y pruebas sin red |
| Sandbox fuerte | No incluido | Requiere backend de contenedor futuro |

## Validación de release

```bash
python -m unittest discover -s tests -v
python -m compileall -q toolkit
python -m toolkit validate
python -m pip check
```

## Artefactos

La release genera:

- wheel universal de Python: `content_skills_toolkit-0.3.0-py3-none-any.whl`;
- source distribution: `content-skills-toolkit-0.3.0.tar.gz`;
- hashes SHA-256 en `dist/SHA256SUMS`.

Estos artefactos son internos y no constituyen todavía una publicación pública en PyPI.
