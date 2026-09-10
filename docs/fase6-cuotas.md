# Fase 6 — Sistema de cuotas

## Alcance

`toolkit/quotas.py` implementa cuotas en memoria para host, fase, herramienta, tenant o cualquier scope definido por la aplicación. Una reserva se acepta únicamente si todos los scopes aplicables están disponibles; por tanto, la política efectiva siempre es la más restrictiva.

## Dimensiones

Cada `QuotaPolicy` controla:

- `max_concurrent`: ejecuciones simultáneas;
- `rate_per_second` y `burst`: token bucket para solicitudes;
- `max_input_bytes`;
- `max_output_bytes`;
- `max_duration_seconds`.

El `QuotaManager` devuelve un `QuotaLease`. El lease debe liberarse en éxito, error, timeout o cancelación. La liberación es idempotente y reduce siempre el contador activo, incluso cuando el tamaño de salida o la duración excedieron el límite.

## Composición

```python
from toolkit import QuotaManager, QuotaPolicy, Supervisor

policy = QuotaPolicy(
    "production",
    max_concurrent=4,
    rate_per_second=10,
    burst=20,
    max_input_bytes=2_000_000,
    max_output_bytes=8_000_000,
    max_duration_seconds=120,
)
quotas = QuotaManager({
    "host": policy,
    "phase-2-datos": QuotaPolicy("data-phase", max_concurrent=2, burst=10, rate_per_second=5),
    "tenant-acme": policy,
})

supervisor = Supervisor(root=Path("."), quota_manager=quotas)
result = supervisor.run_script(
    script,
    payload,
    quota_scopes=("host", "phase-2-datos", "tenant-acme"),
)
```

Una solicitud consume un token y una plaza de concurrencia en cada scope. Si cualquiera falla, toda la reserva se rechaza con `quota_exceeded` y no se crea el worker.

## Métricas

`QuotaManager.snapshot()` devuelve por scope:

- ejecuciones activas;
- tokens disponibles;
- aceptadas;
- rechazadas;
- liberadas.

Estas métricas no contienen payloads ni credenciales.

## Relación con sandbox

Las cuotas son controles de consumo y no sustituyen al sandbox. El supervisor continúa aplicando límites de CPU, memoria, archivos, procesos, stdout/stderr y timeout. Una cuota excedida no debe abrir un circuit breaker; esa separación será responsabilidad de la Fase 7.

## Configuración declarativa futura

El siguiente archivo muestra una representación TOML que puede consumir una capa de configuración posterior:

```toml
[host]
max_concurrent = 8
rate_per_second = 20
burst = 40
max_input_bytes = 2000000
max_output_bytes = 8000000
max_duration_seconds = 120

[phase.phase-2-datos]
max_concurrent = 2
rate_per_second = 5
burst = 10

[tenant.acme]
max_concurrent = 4
rate_per_second = 10
burst = 20
```

Esta fase mantiene la API Python como fuente ejecutable y no añade todavía un parser TOML, para evitar introducir una política de configuración incompleta.
