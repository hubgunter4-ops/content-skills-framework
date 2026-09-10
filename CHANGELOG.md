# Changelog

## 0.3.0 — Release interna

- Añadidos modelos y contratos públicos para herramientas, peticiones, selección y resultados.
- Añadidos descubrimiento de entry points, índice SQLite persistente, caché y routing por fases.
- Añadido proveedor LLM opcional con salida estructurada y fallback determinista.
- Añadidos supervisor, sandbox por subproceso, cuotas compositivas y circuit breakers.
- Añadidos controles contra traversal, symlinks y fuga de secretos.
- Añadidas métricas p50/p95/p99, redacción de eventos y CI separada por validación, integración, carga y auditoría.
- Generados artefactos wheel y source distribution para instalación interna.
- Limitación conocida: `subprocess-limited` no sustituye a un contenedor o sandbox de kernel completo.

## 0.1.0

- Añadido el catálogo modular de habilidades suministrado por el usuario.
- Añadidos CLI local, menú guiado, validación y pruebas smoke.
- Omitidas las métricas de uso y estrellas del material generado.
