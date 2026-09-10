# Fase 0 — Decisiones iniciales de alcance

**Repositorio de trabajo:** `content-skills-framework`  
**Repositorio de origen:** `content-skills-toolkit`  
**Estado:** aprobado para implementación incremental

## Decisiones confirmadas

1. El repositorio nuevo será `hubgunter4-ops/content-skills-framework`.
2. El repositorio original se conserva como referencia y no se modificará desde esta línea de trabajo.
3. La arquitectura usará un **core común** y módulos por fase.
4. Cada herramienta conservará su script ejecutable, inicialmente `run.py`, con contrato JSON compatible.
5. Se añadirá una interfaz de peticiones donde el usuario pueda describir el objetivo sin conocer el slug técnico.
6. El framework normalizará la petición, seleccionará una herramienta y mostrará el motivo de la decisión.
7. La herramienta seleccionada ejecutará la petición completa mediante su propio script.
8. La selección manual estará disponible, pero no podrá omitir validaciones, cuotas, circuit breakers ni políticas de seguridad.
9. El selector determinista funcionará sin un LLM.
10. Se añadirá un LLM opcional como complemento para normalizar intención o proponer candidatas.
11. El usuario configurará el proveedor, endpoint, modelo, timeout y límites del LLM.
12. El LLM no tendrá autoridad final para ejecutar una herramienta.
13. Las respuestas del LLM se validarán mediante JSON Schema.
14. Si el LLM está deshabilitado, no disponible o devuelve una respuesta inválida, el sistema usará el selector determinista o devolverá una decisión ambigua.
15. No se activarán credenciales ni llamadas externas durante la Fase 0.

## Decisiones pendientes

- Licencia del repositorio y del futuro paquete.
- Proveedor y modelo LLM predeterminados, si se define alguno.
- Política de persistencia del estado de circuit breakers.
- Nivel final de sandboxing para plugins no confiables.
- Estrategia de publicación del core y de los módulos de fase.

## Criterio de seguridad del LLM opcional

El LLM puede producir:

- una intención normalizada;
- etiquetas y fase sugerida;
- una lista ordenada de herramientas candidatas;
- una explicación de selección;
- un plan de pasos, cuando los pipelines estén habilitados.

El LLM no puede producir directamente una orden de ejecución fuera del registro ni desactivar controles del runtime. La decisión final siempre debe pasar por contratos, capacidades, cuotas, circuit breaker y supervisor.
