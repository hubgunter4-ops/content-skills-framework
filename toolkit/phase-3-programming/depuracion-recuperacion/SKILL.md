---
name: depuracion-recuperacion
description: Esta es una guía de depuración sistemática que ayuda a los desarrolladores a identificar y corregir las causas raíz cuando las pruebas fallan, las compilaciones se rompen o se producen errores inesperados. Al proporcionar un enfoque estructurado para la recuperación de errores, elimina las suposiciones a ciegas y ayuda a los equipos a resolver problemas complejos de código más rápido en cualquier escenario de desarrollo.
---

# Depuración & recuperación

## Propósito
Esta es una guía de depuración sistemática que ayuda a los desarrolladores a identificar y corregir las causas raíz cuando las pruebas fallan, las compilaciones se rompen o se producen errores inesperados. Al proporcionar un enfoque estructurado para la recuperación de errores, elimina las suposiciones a ciegas y ayuda a los equipos a resolver problemas complejos de código más rápido en cualquier escenario de desarrollo.

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
