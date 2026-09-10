# Plan de ejecución del framework de plugins

**Solicitud identificable:** plan para implementar caché, índice persistente, módulos por fase, sandboxing, cuotas y circuit breakers  
**Estado:** Fases 0–2 completadas; Fase 3 — caché en memoria y carga diferida implementada
**Repositorio:** `content-skills-framework`  
**Fecha:** 9 de septiembre de 2026

## 1. Objetivo

Evolucionar el toolkit actual hacia una arquitectura de framework extensible que pueda descubrir, validar y ejecutar herramientas integradas y plugins externos de forma eficiente, aislada y controlada.

La implementación se realizará de forma incremental y compatible con el comportamiento actual. El CLI existente y las 304 herramientas no se reemplazarán de una sola vez.

## 2. Alcance propuesto

### Incluido

- Índice persistente de herramientas y entry points.
- Caché en memoria para resolución, metadatos y esquemas.
- Invalidación basada en huella del entorno.
- API interna para registro y descubrimiento.
- Modularización por fases mediante paquetes o módulos instalables.
- Supervisor de ejecución y workers aislados.
- Límites de tiempo, tamaño, CPU, memoria y concurrencia.
- Cuotas globales, por fase, por plugin y por usuario o tenant.
- Circuit breakers por plugin y proveedor.
- Interfaz de peticiones del usuario con normalización, selección explicable y ejecución completa mediante el script de la herramienta.
- Selector determinista por metadatos, con soporte opcional para un LLM configurado por el usuario mediante API.
- Pruebas unitarias, de integración, seguridad y carga.
- Documentación técnica y ejemplos reproducibles.

### No incluido en la primera iteración

- Publicación en PyPI.
- Despliegue como servicio público.
- Integración automática con APIs externas.
- Uso obligatorio de un LLM para decidir herramientas; el LLM será opcional y complementario.
- Activación o distribución de credenciales.
- Migración destructiva de rutas actuales.
- Ejecución de acciones de publicación, compra, borrado o despliegue.
- Sandbox de nivel contenedor si el entorno de pruebas no lo permite; en ese caso se dejará una interfaz y un backend local seguro como primera etapa.

## 3. Principios de implementación

1. **Compatibilidad primero:** las pruebas actuales deben mantenerse verdes.
2. **Cambios reversibles:** cada etapa debe poder revisarse y revertirse de forma independiente.
3. **Caché como aceleración:** el índice persistente nunca será la única fuente de verdad.
4. **Carga diferida:** descubrir metadatos no debe importar ni ejecutar todos los plugins.
5. **Denegación por defecto:** red, credenciales, escritura externa y procesos hijos estarán deshabilitados salvo autorización explícita.
6. **Cuotas separadas de salud:** una cuota excedida por el consumidor no debe abrir un circuit breaker del plugin.
7. **Contratos verificables:** entradas y salidas deben validarse mediante esquemas versionados.
8. **Observabilidad sin secretos:** las métricas no deben registrar payloads sensibles.
9. **LLM como complemento:** el LLM puede proponer candidatas o normalizar intención, pero nunca puede saltarse contratos, capacidades, cuotas, circuit breakers o políticas de seguridad.
10. **Script como unidad de ejecución:** cada herramienta conserva su `run.py` o entry point equivalente; la interfaz coordina, pero no reimplementa la lógica de dominio.

## 4. Arquitectura objetivo

```text
content_skills_core/
├── api.py
├── models.py
├── registry.py
├── persistent_index.py
├── cache.py
├── contracts.py
├── runtime.py
├── supervisor.py
├── quotas.py
├── circuit_breaker.py
├── sandbox.py
├── providers.py
├── request_normalizer.py
├── tool_router.py
├── execution_planner.py
├── llm_router.py             # opcional; API configurada por el usuario
└── cli.py

content_skills_phase_content/
content_skills_phase_data/
content_skills_phase_programming/
content_skills_phase_automation/
content_skills_phase_business/
content_skills_phase_media/
```

El core proporcionará una sola API y política de ejecución. Las fases expondrán herramientas y metadatos mediante entry points. La organización por fases será modular, pero no habrá seis runtimes incompatibles.

## 5. Fases de trabajo

### Fase 0 — Preparación y línea base

**Objetivo:** congelar el estado actual antes de comenzar.

**Actividades:**

- Crear rama de trabajo o confirmar workspace limpio.
- Registrar `HEAD`, versión de Python y dependencias.
- Ejecutar pruebas unitarias, compilación y validación del catálogo.
- Medir tiempo de `list`, `show`, `validate` y `run` con el catálogo actual.
- Confirmar que las pruebas no realizan llamadas externas.

**Entregables:**

- Registro de línea base.
- Tabla de métricas iniciales.
- Lista de compatibilidades que no deben romperse.

**Criterio de aceptación:** el estado inicial permanece verde y todas las mediciones pueden repetirse.

### Fase 1 — Modelos, contratos y peticiones públicas

**Objetivo:** definir los objetos que usarán el runtime y los plugins.

**Actividades:**

- Crear `ToolMetadata`.
- Crear `ExecutionRequest`.
- Crear `ExecutionResult`.
- Crear `Capability`.
- Crear errores públicos tipados.
- Definir estados: `ready`, `needs_input`, `not_loaded`, `error`, `timeout`, `quota_exceeded`, `circuit_open` y `worker_crashed`.
- Definir esquemas JSON versionados.
- Definir `NormalizedRequest`, `ToolSelection` y `ExecutionPlan`.
- Definir el contrato de explicación de selección: herramienta, confianza, motivos, alternativas y necesidad de confirmación.
- Definir el contrato de proveedor LLM opcional: modelo, endpoint, límites, timeout, esquema de salida y política de datos.
- Garantizar que el selector determinista funcione sin LLM.

**Entregables:**

- Módulo de modelos.
- Esquemas de metadatos, solicitud y resultado.
- Ejemplos válidos e inválidos.
- Pruebas de compatibilidad de contratos.
- Ejemplos de petición libre, petición estructurada y selección ambigua.

**Criterio de aceptación:** los modelos se pueden importar sin cargar integraciones ni plugins.

### Fase 2 — Registro e índice persistente

**Objetivo:** evitar escaneos completos e importaciones innecesarias durante cada arranque.

**Actividades:**

- Implementar descubrimiento de entry points del grupo `content_skills_toolkit.tools`.
- Crear índice SQLite reconstruible.
- Añadir huella del entorno y de las distribuciones.
- Implementar reconstrucción atómica.
- Añadir índices por `tool_id`, distribución, fase y estado.
- Detectar duplicados y metadatos inconsistentes.
- Mantener compatibilidad con el registro actual.

**Entregables:**

- `persistent_index.py`.
- Migración o adaptador desde `toolkit/registry.py`.
- Comando de reconstrucción del índice.
- Pruebas de instalación, actualización, eliminación y conflicto.

**Criterio de aceptación:** el registro resuelve herramientas sin importar sus módulos y detecta cambios del entorno.

### Fase 3 — Caché en memoria y carga diferida

**Objetivo:** reducir lecturas de disco, validaciones repetidas e importaciones.

**Actividades:**

- Implementar L1 para resolución de identificadores.
- Implementar L2 para metadatos y esquemas compilados.
- Implementar L3 limitada para fábricas o workers.
- Usar claves con `metadata_digest`.
- Añadir TTL o LRU donde corresponda.
- Desalojar entradas obsoletas tras invalidación.
- Medir hit rate, memoria y latencia.

**Entregables:**

- `cache.py`.
- Métricas de hit/miss y desalojos.
- Pruebas de invalidación y consistencia.
- Benchmark con 304, 1.000, 5.000 y 10.000 herramientas sintéticas.

**Criterio de aceptación:** las consultas repetidas no reconstruyen el registro ni recargan esquemas sin necesidad.

### Fase 4 — Modularización por fases y enrutamiento de peticiones

**Objetivo:** separar ciclos de instalación y dependencias sin duplicar el core.

**Actividades:**

- Definir paquetes de fase.
- Publicar entry points de herramientas.
- Publicar entry points de módulos de fase.
- Añadir filtros `--phase` al CLI.
- Mantener identificadores cualificados.
- Añadir perfiles de recursos por fase.
- Definir compatibilidad entre versiones del core y fases.
- Añadir metadatos de selección: `input_kinds`, `output_formats`, `tags`, `phase`, `script` y `capabilities`.
- Implementar selección determinista por intención normalizada, fase, formato, capacidades y disponibilidad.
- Mostrar alternativas cuando la selección sea ambigua o la confianza esté bajo el umbral.
- Permitir seleccionar manualmente una herramienta sin omitir las validaciones del runtime.
- Ejecutar la petición completa mediante el `run.py` o entry point de la herramienta seleccionada.
- Añadir pipelines explícitos como capacidad posterior; no crear cadenas complejas silenciosamente.

**Entregables:**

- Paquetes o estructura modular para las seis fases.
- Registro unificado con filtros.
- Documentación de instalación selectiva.
- Pruebas de fase individual y combinación de fases.
- Interfaz de peticiones, selector y ejecución de script.

**Criterio de aceptación:** se puede instalar y descubrir una fase sin perder la API común ni las pruebas de compatibilidad.

La interfaz de peticiones debe permitir que el usuario escriba una solicitud sin conocer el slug, mostrar la herramienta recomendada y el motivo de selección, y delegar la ejecución completa al script de la herramienta. El LLM no será requisito para operar el sistema.

### Fase 4A — LLM opcional para normalización y decisión asistida

**Objetivo:** añadir una capa complementaria de decisión mediante un proveedor LLM configurable por el usuario, sin acoplarla al núcleo ni convertirla en una autoridad de ejecución.

**Actividades:**

- Definir configuración por entorno o archivo para `base_url`, `api_key`, `model`, timeout y límites de tokens.
- No incluir claves en repositorio, payloads, logs ni resultados.
- Consultar el catálogo de modelos del proveedor solo cuando el usuario active el modo LLM.
- Solicitar salida estructurada con JSON Schema para `NormalizedRequest` o `ToolSelection`.
- Validar la respuesta del LLM y rechazar identificadores inexistentes.
- Aplicar después filtros deterministas de contrato, capacidades, cuotas, circuit breaker y seguridad.
- Permitir modos `off`, `suggest` y `required` solo cuando el usuario lo configure; el modo recomendado por defecto será `off` o `suggest` según la aplicación.
- Registrar proveedor, modelo, latencia y hashes de entrada/salida, nunca el secreto ni el contenido completo por defecto.
- Añadir fallback determinista si el proveedor falla o está deshabilitado.

**Entregables:**

- `llm_router.py` como adaptador opcional.
- Configuración documentada de proveedor y modelo.
- Esquemas de salida estructurada.
- Stub local para pruebas sin red.
- Pruebas de timeout, respuesta inválida, modelo no disponible, fuga de secreto y fallback.

**Criterio de aceptación:** con el LLM deshabilitado, el framework conserva toda su funcionalidad. Con el LLM habilitado, este solo propone o normaliza; el runtime mantiene la autoridad final sobre la herramienta que puede ejecutarse.

### Fase 5 — Supervisor, sandboxing y ejecución de scripts

**Objetivo:** evitar que plugins de terceros afecten al proceso host.

**Actividades:**

- Definir perfiles `trusted-pure`, `trusted-io`, `third-party` y `untrusted`.
- Implementar supervisor.
- Implementar protocolo JSON Lines o IPC equivalente.
- Separar stdout de stderr.
- Añadir timeout total y timeout de I/O.
- Filtrar variables de entorno.
- Crear workspace temporal por ejecución.
- Limitar archivos, procesos, memoria, CPU y salida.
- Implementar terminación y reinicio de workers.
- Dejar preparada la integración con contenedor sin privilegios.
- Ejecutar los scripts existentes mediante un backend de subproceso compatible con `--input` y `--output`.
- Separar los logs del script de la respuesta JSON del protocolo.

**Entregables:**

- `supervisor.py`.
- `sandbox.py`.
- Worker de referencia.
- Plugins de prueba saludable, lento, defectuoso y abusivo.
- Registro de causas de terminación.

**Criterio de aceptación:** un plugin bloqueado o terminado no derriba el host y no retiene indefinidamente una cuota.

### Fase 6 — Sistema de cuotas

**Objetivo:** controlar recursos por host, fase, plugin y usuario.

**Actividades:**

- Implementar composición restrictiva de políticas.
- Implementar límites de concurrencia.
- Implementar token bucket para solicitudes.
- Implementar límites de bytes de entrada y salida.
- Implementar límites temporales.
- Integrar límites de memoria, CPU, archivos y procesos.
- Añadir cuotas de red y proveedor.
- Implementar backpressure, prioridades y rechazo temprano.
- Añadir estado `quota_exceeded`.

**Entregables:**

- `quotas.py`.
- Configuración declarativa TOML.
- Métricas por dimensión.
- Pruebas unitarias y de concurrencia.

**Criterio de aceptación:** ningún plugin puede superar las cuotas efectivas y todas las reservas se liberan después de éxito, fallo, timeout o cancelación.

### Fase 7 — Circuit breakers

**Objetivo:** proteger al host y a los proveedores frente a fallos repetidos.

**Actividades:**

- Implementar máquina `CLOSED`, `OPEN` y `HALF_OPEN`.
- Añadir umbral de fallos y cooldown configurables.
- Permitir un único probe concurrente en `HALF_OPEN`.
- Clasificar errores que cuentan y que no cuentan.
- Separar estado por plugin y proveedor.
- Añadir backoff para 429 y errores transitorios.
- Añadir métricas de transiciones.
- Definir política de reinicio del estado.

**Entregables:**

- `circuit_breaker.py`.
- Configuración de umbral, ventana y cooldown.
- Integración con supervisor y cuotas.
- Pruebas de recuperación y concurrencia.

**Criterio de aceptación:** un circuito abierto no crea workers, un probe fallido reabre el circuito y un probe exitoso lo cierra.

### Fase 8 — Seguridad, observabilidad y CI

**Objetivo:** verificar que la arquitectura resiste abuso y regresiones.

**Actividades:**

- Pruebas de traversal y symlinks.
- Pruebas de red no autorizada.
- Pruebas de credenciales filtradas.
- Pruebas de procesos hijos.
- Pruebas de salida excesiva.
- Métricas p50, p95 y p99.
- Validación de ausencia de secretos en logs.
- CI rápida para contratos y unidad.
- CI de integración y carga en jobs separados.
- Auditoría de dependencias.

**Entregables:**

- Suite de pruebas de seguridad.
- Dashboard o reporte de métricas de prueba.
- Workflow actualizado.
- Threat model y guía de operación.

**Criterio de aceptación:** las pruebas críticas pasan y los fallos no exponen contenido sensible ni recursos fuera del workspace autorizado.

### Fase 9 — Documentación y release interna

**Objetivo:** entregar una primera versión operable y revisable.

**Actividades:**

- Documentar API y ciclo de vida de plugins.
- Documentar instalación por fases.
- Documentar cuotas y estados de circuit breaker.
- Documentar límites de seguridad.
- Preparar guía de migración del CLI actual.
- Construir artefactos instalables.
- Probar instalación en entorno limpio.
- Preparar changelog y matriz de compatibilidad.

**Entregables:**

- Documentación de usuario y desarrollador.
- Plugin de referencia.
- Artefactos de prueba.
- Informe final de compatibilidad y rendimiento.

**Criterio de aceptación:** un desarrollador puede instalar el core, instalar una fase, registrar un plugin y ejecutarlo con cuotas y aislamiento documentados.

## 6. Orden de ejecución y dependencias

```text
Fase 0
  ↓
Fase 1
  ↓
Fase 2 ───→ Fase 3
  ↓            ↓
Fase 4 ────────┘
  ↓
Fase 5 ───→ Fase 6 ───→ Fase 7
                         ↓
                    Fase 8 → Fase 9
```

La fase 4 puede comenzar parcialmente después de estabilizar el contrato, pero no debe crear runtimes independientes. El sandboxing debe preceder a la activación de plugins no confiables. Las cuotas y circuit breakers deben integrarse después de que exista un supervisor que pueda imponer sus decisiones.

## 7. Entregables globales

| Entregable | Resultado esperado |
| --- | --- |
| Core | Runtime, modelos, registro, caché y contratos. |
| Índice | SQLite reconstruible e invalidable. |
| API | Descubrimiento, validación y ejecución. |
| Peticiones | Normalización, selección explicable y ejecución completa de scripts. |
| Módulos | Seis fases instalables y filtrables. |
| LLM opcional | Adaptador de proveedor configurable, con fallback determinista. |
| Seguridad | Supervisor, workers y capacidades. |
| Cuotas | Políticas jerárquicas y token buckets. |
| Circuit breakers | Protección por plugin y proveedor. |
| Pruebas | Unidad, integración, seguridad, carga y recuperación. |
| Documentación | Guías de plugin, operación y migración. |
| Release | Artefacto instalable y matriz de compatibilidad. |

## 8. Riesgos y controles

| Riesgo | Control |
| --- | --- |
| Romper las 304 herramientas actuales | Adaptadores de compatibilidad y pruebas de regresión. |
| Índice obsoleto | Fingerprint, invalidación y reconstrucción atómica. |
| Caché inconsistente | Claves con digest y desalojos explícitos. |
| Plugin bloqueado | Worker separado, deadline y terminación forzada. |
| Cuota no liberada | Reservas con `finally` y pruebas de crash. |
| Circuit breaker demasiado agresivo | Clasificación de errores y pruebas de recuperación. |
| Falsa sensación de seguridad | Documentar que subproceso no equivale a sandbox fuerte. |
| Complejidad excesiva | Implementar primero SQLite, LRU y subprocesos; posponer infraestructura distribuida. |
| Dependencias de fases incompatibles | Rangos de versión y pruebas de matriz. |
| Exposición de secretos | Entorno filtrado, redacción y logs mínimos. |
| Selección incorrecta | Explicación, alternativas, umbral de confianza y confirmación en casos ambiguos. |
| Dependencia excesiva del LLM | Selector determinista funcional sin LLM y filtros finales obligatorios. |

## 9. Criterios globales de finalización

La implementación estará lista para una primera revisión cuando:

1. El CLI existente conserve su comportamiento esencial.
2. El índice pueda reconstruirse y detectar cambios de instalación.
3. La caché demuestre reducción de latencia en benchmarks reproducibles.
4. Las fases puedan filtrarse sin duplicar el runtime.
5. Los plugins de prueba se ejecuten mediante supervisor.
6. Los límites de tiempo, salida, memoria y concurrencia sean efectivos.
7. Los circuit breakers protejan frente a fallos repetidos.
8. Las cuotas se liberen correctamente en todos los caminos de salida.
9. Las pruebas de seguridad no detecten acceso no autorizado.
10. No haya secretos en resultados, métricas ni logs.
11. La documentación permita crear e instalar un plugin de referencia.
12. El propietario haya aprobado las decisiones de licencia, distribución y nivel de aislamiento.
13. Un usuario pueda enviar una petición en lenguaje natural y recibir una herramienta recomendada con explicación.
14. La herramienta seleccionada ejecute su script completo y devuelva el contrato de resultado.
15. El sistema funcione con el LLM deshabilitado.
16. El LLM opcional nunca pueda ejecutar una herramienta fuera del registro o de las políticas autorizadas.

## 10. Decisiones que requieren autorización antes de implementar

Estas decisiones deben confirmarse porque afectan arquitectura, seguridad o compatibilidad:

| Decisión | Propuesta por defecto |
| --- | --- |
| Modularización | Core único + paquetes por fase. |
| Índice | SQLite local reconstruible. |
| Caché | LRU en memoria por proceso. |
| Plugins confiables | Ejecución en proceso o worker persistente. |
| Plugins de terceros | Subproceso aislado con capacidades restringidas. |
| Plugins no confiables | Contenedor sin privilegios cuando esté disponible. |
| Cuotas | Global + fase + plugin + usuario, aplicando el mínimo. |
| Circuit breaker | Estado en memoria por proceso en la primera versión. |
| Distribución | Artefactos internos antes de publicación pública. |
| Compatibilidad | Mantener CLI y rutas existentes durante la migración. |
| Interfaz de peticiones | Normalización + selector determinista + ejecución del script de herramienta. |
| LLM opcional | Deshabilitado por defecto; API/modelo configurados por el usuario; salida JSON Schema; fallback determinista. |

## 11. Próximo paso después de la autorización

Con la autorización recibida, la **Fase 0** queda iniciada sobre `content-skills-framework`:

1. verificar el estado del repositorio nuevo;
2. ejecutar y registrar la línea base;
3. registrar las decisiones de interfaz de peticiones y LLM opcional;
4. crear la estructura mínima del core sin activar todavía sandboxing fuerte;
5. implementar primero modelos y contratos;
6. añadir pruebas antes de migrar el registro.

No se publicarán cambios, no se hará `push`, no se modificarán integraciones externas y no se activarán credenciales sin una autorización separada.
