# Registro de ejecución del plan

## Parte 0: preparación y línea base

**Estado:** completada el 2026-09-09.

### Alcance

Se inspeccionó el estado Git, los catálogos, runners y archivos `SKILL.md` de las Fases 2–6. También se ejecutaron las pruebas base, la compilación Python, la validación del catálogo y las pruebas agregadas de cada fase.

### Línea base Git

- `HEAD`: `12201e5662a0600fe11133c36219053954ae0d11`
- `origin/main`: `12201e5662a0600fe11133c36219053954ae0d11`
- No se creó ningún commit ni se hizo push.
- Ya existían cambios locales de documentación antes de esta parte; no fueron descartados.

### Criterio de fuentes del proyecto

El README raíz se considera documentación histórica de la primera implementación de las skills base. No se utiliza como fuente de alcance ni de estructura para las Fases 2–6. Para esas fases, la línea base se determina exclusivamente mediante sus propios `README.md`, `catalog.json`, motores, runners y pruebas agregadas.

### Conteos observados

| Fase | Catálogo | Runners | `SKILL.md` |
| --- | ---: | ---: | ---: |
| Fase 2: Datos | 57 | 57 | 0 |
| Fase 3: Programming | 89 | 89 | 89 |
| Fase 4: Automatización | 23 | 23 | 23 |
| Fase 5: Diseño | 34 | 34 | 34 |
| Fase 6: Medios | 49 | 49 | 49 |

### Validaciones

| Comprobación | Resultado |
| --- | --- |
| Suite base `unittest` | 13/13 exitosas |
| Compilación `toolkit` y `skills` | Exitosa |
| `python3 -m toolkit validate` | Catálogo válido: 52 habilidades |
| Fase 2 | 57/57 exitosas |
| Fase 3 | 89/89 exitosas |
| Fase 4 | 23/23 exitosas |
| Fase 5 | 34/34 exitosas |
| Fase 6 | 49/49 exitosas |

La reconfirmación específica de fases verificó que cada directorio de fase tiene su propio `README.md`, `catalog.json` y suite de pruebas, con conteos de catálogo de 57, 89, 23, 34 y 49 respectivamente.

### Decisión para la siguiente parte

La línea base está verde. La principal brecha confirmada es la ausencia de `SKILL.md` en las 57 herramientas de la Fase 2. La siguiente parte propuesta es crear el registro unificado de herramientas, sin cambiar todavía la lógica de los runners.

## Parte 1: registro unificado de herramientas

**Estado:** completada el 2026-09-09.

### Implementación

Se añadió `toolkit/registry.py` como capa de descubrimiento de sólo lectura. El registro reúne las 52 skills base y las 252 herramientas de las Fases 2–6, para un total de 304 entradas.

Cada `ToolSpec` asocia:

- fase;
- slug;
- nombre y descripción del catálogo;
- carpeta;
- runner específico;
- ruta esperada de `SKILL.md`;
- motor de fase;
- catálogo de origen.

El registro permite resolver identificadores cualificados, por ejemplo `phase-2-datos/validacion-de-datos`, y slugs cortos cuando no son ambiguos. No importa ni ejecuta runners y no carga integraciones externas.

### Validaciones

- Registro total: 304 entradas.
- Fase 2: 57 entradas.
- Fase 3: 89 entradas.
- Fase 4: 23 entradas.
- Fase 5: 34 entradas.
- Fase 6: 49 entradas.
- Asociación de `validacion-de-datos` con `toolkit/phase-2-datos/validacion-de-datos/run.py`: correcta.
- Asociación con `toolkit/phase_2_engine.py`: correcta.
- Resolución de una skill base (`estratega-de-seo-y-aeo`): correcta.
- Compilación de `toolkit/registry.py`: correcta.
- Suite base: 13/13 pruebas exitosas.
- `git diff --check`: sin errores.

### Limitación deliberada

El registro ya conoce las rutas de las Fases 2–6, pero el dispatcher `toolkit/__main__.py` todavía no lo utiliza. Esa integración corresponde a la Parte 5 y no se realizó en esta parte.

### Cambio de alcance solicitado

Antes de iniciar la Parte 2 se amplió su alcance: no se documentarán únicamente las 57 herramientas de la Fase 2. Se crearán o auditarán `SKILL.md` para las **252 herramientas de las Fases 2–6**, asociando cada documento con su catálogo, runner, motor, contrato JSON y prueba smoke. Las 195 herramientas que ya tienen `SKILL.md` no se sobrescribirán a ciegas; primero se comprobará su coherencia con la implementación real.

## Parte 1A: migración de la fase inicial a un módulo explícito

**Estado:** completada el 2026-09-09.

### Cambio estructural

Las 52 herramientas que estaban en la ruta histórica `skills/content-toolkit/` fueron movidas a:

```text
toolkit/phase-1-content-toolkit/<slug>/
```

La nueva ruta trata la primera implementación como el módulo inicial del toolkit y evita mezclarla con la documentación histórica del README raíz.

### Asociaciones actualizadas

- `toolkit/registry.py` reconoce `phase-1-content-toolkit` como la primera fase.
- `toolkit/__main__.py` continúa ejecutando las 52 herramientas base desde su nueva ruta.
- Las pruebas base fueron actualizadas a la nueva ubicación.
- El registro conserva 304 entradas: 52 de Fase 1 y 252 de Fases 2–6.

### Validaciones

- Registro: 304 entradas correctas.
- Fase 1: 52 runners reconocidos.
- Fases 2–6: 252 runners reconocidos.
- CLI `list`: correcto.
- CLI `run estratega-de-seo-y-aeo`: `ready`.
- Fase 2: 57/57 exitosas.
- Fase 3: 89/89 exitosas.
- Fase 4: 23/23 exitosas.
- Fase 5: 34/34 exitosas.
- Fase 6: 49/49 exitosas.

### Pendiente deliberado

El README raíz y algunas referencias históricas todavía contienen la ruta antigua. Se actualizarán en la parte de documentación y asociaciones de módulos, después de estabilizar la generación y auditoría de las 304 skills.
