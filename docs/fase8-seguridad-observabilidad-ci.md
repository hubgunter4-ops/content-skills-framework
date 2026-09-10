# Fase 8 — Seguridad, observabilidad y CI

## Controles de seguridad

El supervisor exige que el script exista bajo el `root` autorizado y rechaza symlinks para impedir que una entrada aparentemente local apunte fuera del catálogo. El worker utiliza workspace temporal, stdin desconectado, entorno mínimo y límites de recursos del sandbox.

Las variables extra también pasan por el filtro de secretos. Las claves que contienen `KEY`, `TOKEN`, `SECRET`, `PASSWORD` o `CREDENTIAL` se eliminan salvo que el perfil permita credenciales explícitamente. La red sigue deshabilitada por defecto; la política de red no debe interpretarse como una garantía de aislamiento fuerte mientras el backend sea `subprocess-limited`.

## Threat model resumido

| Amenaza | Control actual | Límite residual |
| --- | --- | --- |
| Traversal de script | `root` resuelto y comprobación `relative_to` | Requiere mantener el root correctamente configurado |
| Symlink hacia código externo | Symlinks rechazados | El catálogo debe controlar también sus propios archivos |
| Fuga de secretos | Entorno mínimo y redacción de eventos | Un plugin puede intentar leer archivos accesibles por el usuario del proceso |
| Worker infinito | Timeout y terminación de grupo | Aislamiento por proceso, no VM/contenedor |
| Salida excesiva | Límite lógico y RLIMIT de archivo | El proceso host debe proteger también sus logs |
| Procesos hijos | `RLIMIT_NPROC` cuando está disponible y terminación de grupo | Depende de permisos y plataforma |
| Red no autorizada | `allow_network=False` como política | No es un firewall de kernel |
| Payload sensible en observabilidad | No se registran payloads por defecto; `redact` para mapas | Los consumidores deben usar el redactor |

## Observabilidad

`ExecutionMetrics` registra duración y estado sin almacenar payloads. Produce:

- cantidad total de muestras;
- conteo por estado;
- p50;
- p95;
- p99.

El almacenamiento está limitado por `max_samples` para evitar crecimiento indefinido. La función `redact` reemplaza valores de campos sensibles, incluso en mapas anidados.

Ejemplo:

```python
from toolkit import ExecutionMetrics

metrics = ExecutionMetrics(max_samples=10_000)
metrics.observe(42.5, "ready")
print(metrics.snapshot())
```

## CI

El workflow `.github/workflows/validate.yml` separa cuatro jobs:

1. `fast`: contratos, suite unitaria, compilación y catálogo;
2. `integration-security`: pruebas del supervisor, breakers, documentación y runners;
3. `load`: smoke checks de cuotas, percentiles y observabilidad;
4. `dependency-audit`: auditoría con `pip-audit`.

Los jobs de integración, carga y auditoría dependen de `fast`, reduciendo trabajo innecesario cuando fallan los contratos básicos.

## Criterio de aceptación

La Fase 8 se considera satisfecha cuando las pruebas críticas pasan, los scripts fuera del root o symlinks se rechazan, los secretos no aparecen en el entorno por defecto ni en eventos redactados, las métricas entregan percentiles y CI ejecuta validaciones separadas.
