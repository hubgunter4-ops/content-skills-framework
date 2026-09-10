# Fase 7 — Circuit breakers

## Estados

`toolkit/circuit_breaker.py` implementa una máquina por clave de herramienta o proveedor:

| Estado | Comportamiento |
| --- | --- |
| `closed` | Las ejecuciones se permiten y los fallos contables se acumulan. |
| `open` | No se crea ningún worker; las solicitudes reciben `circuit_open`. |
| `half_open` | Después del cooldown se permite un único probe concurrente. |

Un probe exitoso cierra el circuito y limpia la ventana de fallos. Un probe fallido lo vuelve a abrir.

## Política

`CircuitPolicy` configura:

- `failure_threshold`;
- `failure_window_seconds`;
- `cooldown_seconds`;
- `max_backoff_seconds`;
- estados que cuentan como fallo.

Por defecto cuentan:

```text
error
timeout
worker_crashed
```

`quota_exceeded` no abre el circuito, porque representa una restricción del consumidor y no necesariamente una falla del plugin.

## Backoff

Cada apertura aumenta el cooldown efectivo:

```text
min(max_backoff_seconds, cooldown_seconds × 2^(opened_count - 1))
```

Esto evita reintentos agresivos contra un plugin o proveedor que continúa fallando.

## Integración con supervisor

```python
from toolkit import CircuitBreakerManager, CircuitPolicy, Supervisor

breakers = CircuitBreakerManager(
    CircuitPolicy(
        failure_threshold=3,
        failure_window_seconds=60,
        cooldown_seconds=10,
        max_backoff_seconds=300,
    )
)

supervisor = Supervisor(
    root=Path("."),
    circuit_breaker=breakers,
)

result = supervisor.run_script(
    script,
    payload,
    circuit_key="phase-2-datos/validacion-de-datos",
)
```

La secuencia es:

```text
Circuit breaker acquire
        ↓ permitido
Quota reserve
        ↓ permitido
Crear worker
        ↓
Liberar cuota
        ↓
Registrar éxito o fallo en breaker
```

Si el circuito está abierto, el supervisor devuelve `circuit_open` antes de crear el worker. Si la cuota falla después de adquirir un probe, el probe se cancela y la cuota no modifica la salud del circuito.

## Métricas

`CircuitSnapshot` expone:

- clave;
- estado;
- fallos activos en ventana;
- número de aperturas;
- transiciones;
- probe en vuelo;
- próximo instante de probe.

Los snapshots no incluyen payloads ni secretos.

## Límites

El estado vive en memoria del proceso supervisor. Un despliegue con varios hosts debe usar un almacén coordinado o afinidad por worker si necesita un circuito global. La Fase 7 no añade persistencia distribuida ni circuit breaking de red a nivel kernel.
