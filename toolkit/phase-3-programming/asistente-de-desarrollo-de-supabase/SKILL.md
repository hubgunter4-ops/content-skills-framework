---
name: asistente-de-desarrollo-de-supabase
description: Crea y asegura aplicaciones de Supabase con la guía oficial del proveedor que cubre Auth, políticas RLS, migraciones, Edge Functions y el CLI de Supabase y el servidor MCP. Incorpora la propia lista de verificación de seguridad de Supabase para detectar vulnerabilidades silenciosas como el mal uso de user_metadata, las trampas de SECURITY DEFINER y la falta de cláusulas WITH CHECK.
---

# Asistente de Desarrollo de Supabase

## Propósito
Crea y asegura aplicaciones de Supabase con la guía oficial del proveedor que cubre Auth, políticas RLS, migraciones, Edge Functions y el CLI de Supabase y el servidor MCP. Incorpora la propia lista de verificación de seguridad de Supabase para detectar vulnerabilidades silenciosas como el mal uso de user_metadata, las trampas de SECURITY DEFINER y la falta de cláusulas WITH CHECK.

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
