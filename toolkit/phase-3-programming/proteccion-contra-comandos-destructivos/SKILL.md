---
name: proteccion-contra-comandos-destructivos
description: Esta habilidad implementa barreras de seguridad en torno a operaciones destructivas de shell y control de versiones, advirtiendo a los usuarios antes de ejecutar rm -rf, DROP TABLE, git force-push, kubectl delete y comandos similares. Ayuda a prevenir la pérdida accidental de datos al solicitar confirmaciones, marcar contextos de riesgo como entornos de producción o compartidos, y permitir anulaciones deliberadas cuando sea necesario.
---

# Protección contra Comandos Destructivos

## Propósito
Esta habilidad implementa barreras de seguridad en torno a operaciones destructivas de shell y control de versiones, advirtiendo a los usuarios antes de ejecutar rm -rf, DROP TABLE, git force-push, kubectl delete y comandos similares. Ayuda a prevenir la pérdida accidental de datos al solicitar confirmaciones, marcar contextos de riesgo como entornos de producción o compartidos, y permitir anulaciones deliberadas cuando sea necesario.

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

- **Runner:** `toolkit/phase-3-programming/proteccion-contra-comandos-destructivos/run.py`
- **Motor:** `toolkit/phase_3_engine.py`
- **Entrada de ejemplo:** `toolkit/phase-3-programming/proteccion-contra-comandos-destructivos/input.example.json`
- **Esquema de salida:** `toolkit/phase-3-programming/proteccion-contra-comandos-destructivos/output.schema.json`
- **Prueba smoke:** `toolkit/phase-3-programming/proteccion-contra-comandos-destructivos/tests/test_smoke.py`

La documentación debe mantenerse sincronizada con el runner, el catálogo de la fase y el contrato JSON. El runner local no debe interpretarse como una ejecución externa, publicación o despliegue.
