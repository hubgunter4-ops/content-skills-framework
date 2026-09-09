---
name: asistente-de-contribucion-de-repositorio
description: Esta herramienta/habilidad aplica las guías de contribución de un repositorio buscando automáticamente CONTRIBUTING.md, plantillas de PR/incidencias y reglas de rama antes de registrar incidencias, crear commits, subir código o abrir pull requests. Genera nombres de rama conformes, mensajes de commit formateados y descripciones de PR, y ejecuta los pasos de la lista de verificación para que las contribuciones sean consistentes y estén listas para revisión.
---

# Asistente de Contribución de Repositorio

## Propósito
Esta herramienta/habilidad aplica las guías de contribución de un repositorio buscando automáticamente CONTRIBUTING.md, plantillas de PR/incidencias y reglas de rama antes de registrar incidencias, crear commits, subir código o abrir pull requests. Genera nombres de rama conformes, mensajes de commit formateados y descripciones de PR, y ejecuta los pasos de la lista de verificación para que las contribuciones sean consistentes y estén listas para revisión.

## Flujo de trabajo
1. Definir objetivo, repositorio, runtime, restricciones y criterio de éxito.
2. Inspeccionar código, configuración, dependencias y pruebas sin modificar antes de proponer cambios.
3. Diseñar una modificación mínima, reproducible y reversible.
4. Implementar con pruebas primero cuando corresponda.
5. Ejecutar validaciones actualizadas y registrar limitaciones.

## Entradas aceptadas
- Solicitud, código, configuración, logs, especificaciones y archivos proporcionados por el usuario.
- Fuentes externas solo mediante integración explícita y autorizada.

## Salida esperada
Un plan o artefacto técnico revisable, con comandos, archivos afectados, pruebas y supuestos.

## Guardrails
- No ejecutar comandos destructivos, cambios de permisos, despliegues, commits, pushes ni acciones externas sin alcance explícito.
- No instalar dependencias ni consultar APIs sin informar el servicio, credencial, riesgos y alternativa local.
- No afirmar que una compilación, prueba o despliegue pasó sin ejecutarlo.

## Plantilla de solicitud
Objetivo: [resultado]
Repositorio o código: [ruta]
Runtime: [lenguaje y versión]
Restricciones: [límites]
Formato: [salida]

## Lista de control
- [ ] La entrada y el alcance están definidos.
- [ ] El plan no cambia archivos fuera de alcance.
- [ ] Las pruebas y comandos son reproducibles.
- [ ] Los riesgos y límites están documentados.

## Runner asociado

- **Runner:** `toolkit/phase-3-programming/asistente-de-contribucion-de-repositorio/run.py`
- **Motor:** `toolkit/phase_3_engine.py`
- **Entrada de ejemplo:** `toolkit/phase-3-programming/asistente-de-contribucion-de-repositorio/input.example.json`
- **Esquema de salida:** `toolkit/phase-3-programming/asistente-de-contribucion-de-repositorio/output.schema.json`
- **Prueba smoke:** `toolkit/phase-3-programming/asistente-de-contribucion-de-repositorio/tests/test_smoke.py`

La documentación debe mantenerse sincronizada con el runner, el catálogo de la fase y el contrato JSON. El runner local no debe interpretarse como una ejecución externa, publicación o despliegue.
