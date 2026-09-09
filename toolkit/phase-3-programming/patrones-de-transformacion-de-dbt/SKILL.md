---
name: patrones-de-transformacion-de-dbt
description: Esta Skill proporciona patrones de transformación de datos dbt de grado de producción, que cubren la organización de modelos, pruebas de calidad, estrategias incrementales y estándares de documentación. Ayuda a los equipos de ingeniería de datos a construir pipelines de datos eficientes, implementar mejores prácticas de analítica y mantener modelos de datos claros y escalables para tareas complejas de ingeniería de datos.
---

# Patrones de transformación de dbt

## Propósito
Esta Skill proporciona patrones de transformación de datos dbt de grado de producción, que cubren la organización de modelos, pruebas de calidad, estrategias incrementales y estándares de documentación. Ayuda a los equipos de ingeniería de datos a construir pipelines de datos eficientes, implementar mejores prácticas de analítica y mantener modelos de datos claros y escalables para tareas complejas de ingeniería de datos.

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
