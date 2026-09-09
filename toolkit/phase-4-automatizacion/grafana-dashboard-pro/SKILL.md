---
name: grafana-dashboard-pro
description: Proporciona plantillas y mejores prácticas para crear tableros de Grafana listos para producción. Ayuda a construir rápidamente interfaces de visualización profesionales para métricas de sistemas y aplicaciones.
---

# Grafana Dashboard Pro

## Propósito
Proporciona plantillas y mejores prácticas para crear tableros de Grafana listos para producción. Ayuda a construir rápidamente interfaces de visualización profesionales para métricas de sistemas y aplicaciones.

## Flujo de trabajo
1. Definir disparador, objetivo, entradas, acciones permitidas, destino y criterio de parada.
2. Inspeccionar permisos, secretos, dominios, ramas, frecuencia y efectos antes de automatizar.
3. Diseñar modo observación o simulación, allowlists, límites, reintentos e idempotencia.
4. Ejecutar solo el alcance autorizado y registrar un resumen auditable.
5. Verificar, detener ante cambios inesperados y documentar reversión.

## Entradas aceptadas
Solicitud, configuración, eventos, archivos, logs y credenciales autorizadas sin incluir secretos en el repositorio.

## Salida esperada
Plan o artefacto de automatización con disparadores, permisos, efectos, pruebas y procedimiento de apagado.

## Guardrails
- No evadir autenticación, CAPTCHA, Cloudflare, límites ni controles de plataforma.
- No publicar, borrar, desplegar, cambiar permisos, ejecutar comandos destructivos ni enviar datos sin autorización explícita.
- No activar integraciones ni leer credenciales si la entrada no las solicita.

## Plantilla de solicitud
Objetivo: [automatización]
Disparador: [manual, webhook, horario o evento]
Entradas: [datos]
Acciones permitidas: [allowlist]
Destino: [salida]
Modo: [simulación o ejecución autorizada]

## Lista de control
- [ ] Disparador y criterio de parada definidos.
- [ ] Permisos mínimos y secretos separados.
- [ ] Dry-run, logs, límites y reversión definidos.
- [ ] Pruebas ejecutadas sin publicar ni desplegar.
