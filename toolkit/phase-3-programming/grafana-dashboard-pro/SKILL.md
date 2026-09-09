---
name: grafana-dashboard-pro
description: Este kit de herramientas de monitoreo proporciona plantillas y mejores prácticas para crear tableros de Grafana listos para producción utilizando las metodologías RED y USE. Ayuda a los equipos a construir rápidamente interfaces de visualización profesionales para métricas de sistemas y aplicaciones, facilitando el establecimiento de una observabilidad operativa robusta.
---

# Grafana Dashboard Pro

## Propósito
Este kit de herramientas de monitoreo proporciona plantillas y mejores prácticas para crear tableros de Grafana listos para producción utilizando las metodologías RED y USE. Ayuda a los equipos a construir rápidamente interfaces de visualización profesionales para métricas de sistemas y aplicaciones, facilitando el establecimiento de una observabilidad operativa robusta.

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

- **Runner:** `toolkit/phase-3-programming/grafana-dashboard-pro/run.py`
- **Motor:** `toolkit/phase_3_engine.py`
- **Entrada de ejemplo:** `toolkit/phase-3-programming/grafana-dashboard-pro/input.example.json`
- **Esquema de salida:** `toolkit/phase-3-programming/grafana-dashboard-pro/output.schema.json`
- **Prueba smoke:** `toolkit/phase-3-programming/grafana-dashboard-pro/tests/test_smoke.py`

La documentación debe mantenerse sincronizada con el runner, el catálogo de la fase y el contrato JSON. El runner local no debe interpretarse como una ejecución externa, publicación o despliegue.
