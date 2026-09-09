---
name: arquitecto-de-modelos-de-contenido
description: Esta guía proporciona las mejores prácticas para diseñar modelos de contenido estructurado escalables y eficientes en Sanity. Traduce los principios arquitectónicos en pautas prácticas, ayudando a los desarrolladores y equipos de contenido a construir estructuras de contenido robustas que mejoren el rendimiento de las consultas, reduzcan la deuda técnica y garanticen la mantenibilidad a largo plazo.
---

# Arquitecto de Modelos de Contenido

## Propósito
Esta guía proporciona las mejores prácticas para diseñar modelos de contenido estructurado escalables y eficientes en Sanity. Traduce los principios arquitectónicos en pautas prácticas, ayudando a los desarrolladores y equipos de contenido a construir estructuras de contenido robustas que mejoren el rendimiento de las consultas, reduzcan la deuda técnica y garanticen la mantenibilidad a largo plazo.

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
