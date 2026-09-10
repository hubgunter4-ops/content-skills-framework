# Pruebas de cuotas y circuit breakers para plugins

**Solicitud identificable:** estrategia de pruebas unitarias y de integración para cuotas y circuit breakers  
**Sistema objetivo:** framework de plugins de Content Skills Toolkit  
**Fecha:** 9 de septiembre de 2026  
**Autor:** **Manus AI**

## 1. Objetivo

El sistema de cuotas debe impedir que un plugin consuma más recursos de los permitidos. El circuit breaker debe evitar que un plugin o proveedor inestable continúe recibiendo solicitudes después de una secuencia de fallos.

La estrategia de pruebas debe verificar cuatro propiedades:

1. **Aislamiento:** una infracción de cuota afecta al plugin responsable y no al host completo.
2. **Determinismo:** la misma secuencia de eventos produce el mismo estado y la misma decisión.
3. **Recuperación:** el plugin puede volver a operar después de transcurrir el periodo de enfriamiento o de ejecutarse una prueba satisfactoria.
4. **Composición:** las cuotas globales, de fase, de plugin y de usuario se aplican de forma restrictiva.

La suite debe dividirse en pruebas rápidas de unidad, pruebas de integración con workers reales y pruebas de carga controladas. Las pruebas que miden tiempo deben utilizar un reloj inyectable, no `sleep()` real, para evitar resultados inestables.

## 2. Modelo mínimo bajo prueba

Se presupone un modelo conceptual como el siguiente:

```python
class QuotaPolicy:
    max_concurrency: int
    max_wall_time_seconds: float
    max_cpu_seconds: float
    max_memory_mb: int
    max_input_bytes: int
    max_output_bytes: int
    max_requests_per_window: int
    max_network_bytes: int

class QuotaDecision:
    allowed: bool
    reason: str | None
    retry_after_seconds: float | None

class CircuitState:
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    def allow(self, plugin_id: str) -> bool: ...
    def record_success(self, plugin_id: str) -> None: ...
    def record_failure(self, plugin_id: str, error_class: str) -> None: ...
    def state(self, plugin_id: str) -> CircuitState: ...
```

La implementación real puede usar clases distintas, pero debe conservar semánticas equivalentes y estados observables.

## 3. Matriz general de pruebas

| Nivel | Área | Cantidad inicial sugerida | Dependencias externas |
| --- | --- | ---: | --- |
| Unidad | Composición de cuotas | 8 | Ninguna |
| Unidad | Token bucket y ventanas | 8 | Reloj falso |
| Unidad | Concurrencia lógica | 6 | Locks o scheduler controlado |
| Unidad | Circuit breaker | 12 | Reloj falso |
| Unidad | Clasificación de errores | 6 | Ninguna |
| Unidad | Estados y métricas | 6 | Recolector en memoria |
| Integración | Worker y supervisor | 10 | Subprocesos locales |
| Integración | Timeouts y cancelación | 6 | Plugins de prueba |
| Integración | Memoria, salida y archivos | 8 | Worker local |
| Integración | Red y credenciales | 6 | Servidor HTTP local controlado |
| Integración | Recuperación del circuit breaker | 6 | Worker local y reloj |
| Carga | Fairness y saturación | 4 | Pool de workers |
| Seguridad | Escape y abuso de recursos | 8 | Entorno aislado |

La primera versión no necesita implementar todos los casos de carga en cada pull request. Las pruebas unitarias e integración deben ejecutarse en cada cambio; las de carga y abuso pueden ejecutarse en CI nocturna o antes de publicar una release.

## 4. Pruebas unitarias de cuotas

### 4.1 Composición restrictiva de políticas

**Objetivo:** confirmar que la cuota efectiva no puede superar ninguna política aplicable.

Casos:

| Caso | Global | Fase | Plugin | Resultado esperado |
| --- | ---: | ---: | ---: | --- |
| Todos iguales | 4 | 4 | 4 | 4 |
| Plugin más restrictivo | 8 | 4 | 2 | 2 |
| Fase más restrictiva | 8 | 2 | 6 | 2 |
| Global más restrictiva | 1 | 4 | 4 | 1 |
| Campo no definido | 4 | `None` | 2 | 2 |
| Política inválida | 0 | 4 | 2 | Error de configuración |
| Valor negativo | -1 | 4 | 2 | Error de configuración |
| Unidad incompatible | `"10 MB"` | 4 | 2 | Error de configuración |

```python
def test_effective_quota_uses_restrictive_minimum():
    effective = compose_quota(
        global_policy=QuotaPolicy(max_concurrency=8),
        phase_policy=QuotaPolicy(max_concurrency=4),
        plugin_policy=QuotaPolicy(max_concurrency=2),
    )
    assert effective.max_concurrency == 2


def test_invalid_zero_concurrency_is_rejected():
    with pytest.raises(InvalidQuotaPolicy):
        QuotaPolicy(max_concurrency=0).validate()
```

### 4.2 Token bucket

**Objetivo:** confirmar que el límite de solicitudes por ventana se aplica sin depender del tiempo real del sistema.

Casos mínimos:

1. El bucket comienza con su capacidad completa.
2. Una solicitud consume un token.
3. Una solicitud sin tokens se rechaza.
4. El paso del tiempo repone tokens hasta la capacidad máxima.
5. La reposición no puede superar la capacidad.
6. Un coste mayor que uno consume varios tokens.
7. Una solicitud con coste superior al máximo se rechaza.
8. El cálculo es correcto en los límites exactos.

```python
def test_bucket_rejects_after_capacity_is_consumed():
    clock = FakeClock(start=100.0)
    bucket = TokenBucket(capacity=2, refill_per_second=1.0, clock=clock)

    assert bucket.take() is True
    assert bucket.take() is True
    assert bucket.take() is False


def test_bucket_refills_without_exceeding_capacity():
    clock = FakeClock(start=100.0)
    bucket = TokenBucket(capacity=2, refill_per_second=1.0, clock=clock)
    assert bucket.take(2) is True

    clock.advance(10.0)
    assert bucket.take(2) is True
    assert bucket.take() is False
```

### 4.3 Cuota de concurrencia

**Objetivo:** confirmar que no se admiten más workers activos que los autorizados.

Casos:

- El primer `acquire` tiene éxito.
- Los siguientes `acquire` tienen éxito hasta el límite.
- El siguiente `acquire` devuelve `quota_exceeded`.
- `release` libera exactamente un slot.
- Un `release` duplicado no aumenta la capacidad disponible por encima del límite.
- Un error o cancelación libera el slot mediante un bloque `finally`.
- Las solicitudes de un plugin no consumen la cuota de otro plugin cuando la política es por plugin.

```python
def test_concurrency_slot_is_released_after_failure():
    limiter = ConcurrencyLimiter(limit=1)
    lease = limiter.acquire()
    assert lease.allowed

    try:
        raise PluginCrashed("worker exited with code 1")
    except PluginCrashed:
        lease.release()

    assert limiter.acquire().allowed
```

### 4.4 Límites de tamaño

**Objetivo:** rechazar entradas y salidas demasiado grandes antes de transferir o almacenar el contenido completo.

Casos:

- Entrada exactamente igual al máximo: se acepta.
- Entrada un byte por encima: se rechaza.
- Salida exactamente igual al máximo: se acepta.
- Salida un byte por encima: el worker se termina o la respuesta se trunca según la política; nunca se acepta silenciosamente.
- Un stream que supera el límite activa cancelación y libera recursos.
- Un payload Unicode se mide de acuerdo con bytes serializados, no solo con número de caracteres.

```python
def test_input_quota_uses_serialized_bytes():
    payload = {"content": "á" * 10}
    encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    policy = QuotaPolicy(max_input_bytes=len(encoded))

    assert check_input_size(payload, policy).allowed
    assert not check_input_size({"content": "á" * 11}, policy).allowed
```

## 5. Pruebas unitarias de circuit breakers

### 5.1 Máquina de estados

El circuit breaker debe probarse como una máquina de estados explícita:

```text
CLOSED --fallos consecutivos--> OPEN
OPEN --cooldown transcurrido--> HALF_OPEN
HALF_OPEN --éxito--> CLOSED
HALF_OPEN --fallo--> OPEN
```

Casos mínimos:

| Secuencia | Estado final esperado |
| --- | --- |
| Inicialización | `CLOSED` |
| Éxitos repetidos | `CLOSED` |
| Fallos inferiores al umbral | `CLOSED` |
| Fallo que alcanza el umbral | `OPEN` |
| Solicitud mientras está abierto | Rechazada sin ejecutar plugin |
| Cooldown no transcurrido | `OPEN` |
| Cooldown transcurrido | `HALF_OPEN` |
| Prueba half-open exitosa | `CLOSED` |
| Prueba half-open fallida | `OPEN` |
| Reinicio manual | `CLOSED`, con contadores reiniciados |

```python
def test_breaker_opens_at_failure_threshold():
    clock = FakeClock(start=0.0)
    breaker = CircuitBreaker(failure_threshold=3, cooldown=30, clock=clock)

    for _ in range(2):
        breaker.record_failure("plugin-a", "timeout")
        assert breaker.state("plugin-a") == CircuitState.CLOSED

    breaker.record_failure("plugin-a", "timeout")
    assert breaker.state("plugin-a") == CircuitState.OPEN
    assert breaker.allow("plugin-a") is False
```

### 5.2 Cooldown y estado half-open

El estado `HALF_OPEN` debe permitir solo una prueba de recuperación concurrente. Este caso es crítico porque varios workers podrían observar simultáneamente que terminó el cooldown.

```python
def test_only_one_probe_is_allowed_in_half_open():
    clock = FakeClock(start=0.0)
    breaker = CircuitBreaker(failure_threshold=1, cooldown=10, clock=clock)
    breaker.record_failure("plugin-a", "provider_5xx")

    clock.advance(10.0)
    assert breaker.allow("plugin-a") is True
    assert breaker.allow("plugin-a") is False
```

Casos adicionales:

- Si la prueba half-open tarda más que su deadline, se considera fallo.
- Si la prueba half-open se cancela, el circuito vuelve a `OPEN` o aplica una política explícita equivalente.
- Un éxito en `HALF_OPEN` reinicia contador de fallos y latencia acumulada.
- Un fallo en `HALF_OPEN` actualiza `opened_at` para reiniciar el cooldown.
- El estado de un plugin no debe afectar al estado de otro.

### 5.3 Clasificación de errores

No todos los errores deben abrir el circuito. La política debe distinguir entre fallos transitorios del plugin o proveedor y errores permanentes de entrada.

| Error | ¿Cuenta para circuit breaker? | Motivo |
| --- | --- | --- |
| Timeout del worker | Sí | Puede indicar saturación o bloqueo. |
| Worker terminado inesperadamente | Sí | Indica inestabilidad del plugin. |
| Error HTTP 500 | Sí | Fallo transitorio del proveedor. |
| Error HTTP 429 | Sí, con backoff | Indica límite del proveedor. |
| Error HTTP 401 | Normalmente no como fallo de salud | Requiere corregir configuración o credenciales. |
| Entrada inválida | No | El plugin puede estar sano. |
| Esquema de salida inválido | Sí | El plugin incumple el contrato. |
| Cuota excedida del consumidor | No | No es fallo del plugin. |
| Cancelación solicitada por usuario | No | No demuestra inestabilidad. |
| Error de programación determinista | Sí, con límite | Puede abrir el circuito para proteger al host. |

```python
def test_invalid_input_does_not_open_breaker():
    breaker = CircuitBreaker(failure_threshold=1)
    breaker.record_failure("plugin-a", "invalid_input")
    assert breaker.state("plugin-a") == CircuitState.CLOSED
```

### 5.4 Ventanas y fallos consecutivos

Debe definirse si el umbral cuenta fallos consecutivos o fallos dentro de una ventana temporal. Ambas estrategias requieren pruebas diferentes.

Para fallos consecutivos:

- `failure, failure, success, failure` no debe abrir con umbral 3;
- el éxito reinicia el contador;
- fallos de plugins distintos no se mezclan.

Para ventana temporal:

- tres fallos dentro de 60 segundos abren el circuito;
- dos fallos dentro de la ventana no lo abren;
- los fallos fuera de la ventana expiran;
- el reloj adelantado exactamente al borde debe seguir una regla documentada.

## 6. Pruebas de integración con supervisor y worker

### 6.1 Plugin de prueba controlado

La suite debe incluir plugins artificiales, no plugins reales, para producir comportamientos deterministas:

```text
plugins_test/
├── healthy_plugin.py
├── slow_plugin.py
├── crash_plugin.py
├── oversized_output_plugin.py
├── memory_hog_plugin.py
├── child_process_plugin.py
├── network_plugin.py
└── invalid_contract_plugin.py
```

Cada plugin debe exponerse solo en el entorno de pruebas y declarar sus capacidades de manera conocida.

### 6.2 Flujo normal

**Objetivo:** confirmar que el supervisor no penaliza una ejecución saludable.

Prueba:

1. Registrar `healthy_plugin`.
2. Enviar una solicitud válida.
3. Recibir un resultado válido.
4. Confirmar estado `CLOSED`.
5. Confirmar que la cuota vuelve a estar disponible.
6. Confirmar métricas de éxito y duración.

```python
def test_healthy_worker_completes_and_releases_quota(supervisor):
    result = supervisor.execute("test/healthy", valid_payload())
    assert result.status == "ready"
    assert supervisor.breaker.state("test/healthy") == "closed"
    assert supervisor.quota.active_workers("test/healthy") == 0
```

### 6.3 Timeout

**Objetivo:** confirmar que un plugin bloqueado no retiene indefinidamente el host.

Prueba:

1. Ejecutar `slow_plugin` con timeout de 100 ms.
2. Confirmar que el supervisor termina o cancela el worker.
3. Confirmar resultado `timeout`.
4. Confirmar liberación del slot de concurrencia.
5. Confirmar incremento del contador de fallos.
6. Repetir hasta abrir el circuito.
7. Confirmar que una solicitud posterior se rechaza sin crear otro worker.

```python
def test_repeated_timeouts_open_breaker(supervisor):
    for _ in range(3):
        result = supervisor.execute("test/slow", valid_payload())
        assert result.status == "timeout"

    assert supervisor.breaker.state("test/slow") == "open"
    assert supervisor.worker_factory.created_count("test/slow") == 3

    rejected = supervisor.execute("test/slow", valid_payload())
    assert rejected.status == "circuit_open"
    assert supervisor.worker_factory.created_count("test/slow") == 3
```

### 6.4 Crash del worker

**Objetivo:** distinguir un proceso terminado de forma anómala de un error de entrada.

Casos:

- salida con código distinto de cero;
- terminación por señal;
- stdout no válido como JSON;
- stdout mezclado con logs;
- worker que muere antes de responder;
- worker que muere después de emitir una respuesta parcial.

El resultado debe ser tipado, no una excepción no controlada del supervisor. Después del umbral definido, el circuito debe abrirse.

### 6.5 Salida superior al límite

**Objetivo:** impedir que un plugin agote la memoria del host mediante stdout o artefactos.

Prueba:

1. Ejecutar `oversized_output_plugin`.
2. Leer la respuesta en streaming.
3. Detener la lectura al alcanzar `max_output_bytes`.
4. Terminar el worker.
5. El resultado debe ser `output_quota_exceeded`.
6. El circuito debe contar el incidente solo si la política lo considera un incumplimiento de salud del plugin.
7. Confirmar que no se conserva la salida parcial como resultado válido.

### 6.6 Memoria y CPU

**Objetivo:** confirmar que el supervisor puede terminar un worker que supera límites de recursos.

Casos:

- worker que supera memoria;
- worker que supera CPU;
- worker que crea demasiados procesos;
- worker que abre demasiados archivos;
- worker que escribe más espacio temporal del permitido.

Cada caso debe verificar:

- estado final del worker;
- código o causa de terminación;
- devolución de la cuota;
- actualización de métricas;
- transición del circuit breaker;
- ausencia de contaminación del proceso supervisor.

No se deben usar límites tan bajos que generen falsos positivos en CI. El test debe ejecutar una acción conocida y dejar margen para el runtime del sistema.

## 7. Pruebas de integración de recuperación

### 7.1 Recuperación después de cooldown

```python
def test_breaker_recovers_after_successful_probe(supervisor, fake_clock):
    fail_three_times(supervisor, "test/flaky")
    assert supervisor.breaker.state("test/flaky") == "open"

    rejected = supervisor.execute("test/flaky", valid_payload())
    assert rejected.status == "circuit_open"

    fake_clock.advance(30.0)
    probe = supervisor.execute("test/flaky", valid_payload())
    assert probe.status == "ready"
    assert supervisor.breaker.state("test/flaky") == "closed"
```

### 7.2 Fallo durante half-open

1. Abrir el circuito.
2. Avanzar el reloj hasta el final del cooldown.
3. Permitir una única prueba.
4. Hacer que la prueba falle.
5. Confirmar que el circuito vuelve a `OPEN`.
6. Confirmar que se reinicia el tiempo de cooldown.
7. Confirmar que no se ejecutan dos probes simultáneas.

### 7.3 Reinicio del proceso supervisor

Debe definirse la persistencia del estado:

- Si el estado es solo memoria, el reinicio devuelve el circuito a `CLOSED`.
- Si el estado se persiste, el reinicio debe conservar `OPEN`, su causa y el tiempo restante.

Para el primer diseño recomiendo estado en memoria por proceso, salvo que exista un scheduler distribuido. Si se persiste, hay que probar corrupción, relojes diferentes y concurrencia entre supervisores.

## 8. Pruebas de concurrencia y fairness

### 8.1 Competencia por cuota de concurrencia

**Objetivo:** confirmar que dos solicitudes no obtienen el mismo slot cuando solo existe uno.

Usar una barrera controlada para hacer que varias tareas soliciten el slot simultáneamente. El resultado esperado debe ser exactamente un permitido y el resto rechazado o en cola, según la política.

```python
def test_concurrent_acquire_has_no_double_grant(limiter):
    results = run_concurrently(
        lambda: limiter.acquire(),
        count=20,
    )
    assert sum(result.allowed for result in results) == 1
```

### 8.2 Fairness entre plugins

Con cuota global 2 y dos plugins, un plugin que genera solicitudes continuamente no debe monopolizar los dos slots de forma indefinida.

Criterios:

- cada plugin elegible obtiene servicio dentro de un límite de espera;
- la cola no crece sin límite sin producir `quota_exceeded` o backpressure;
- un circuito abierto no consume slots;
- las solicitudes rechazadas no quedan contabilizadas como ejecuciones exitosas.

### 8.3 Circuit breaker bajo concurrencia

Casos:

- muchos fallos simultáneos no deben generar múltiples transiciones inconsistentes;
- solo un probe debe ejecutarse en `HALF_OPEN`;
- una solicitud rechazada por `OPEN` no debe crear un worker;
- una transición de `CLOSED` a `OPEN` debe ser atómica;
- un éxito concurrente no debe reabrir accidentalmente el circuito después de cerrarlo.

## 9. Pruebas de interacción entre cuotas y circuit breakers

Estas pruebas son esenciales porque ambos mecanismos pueden producir estados parecidos, pero representan causas diferentes.

| Escenario | Resultado esperado |
| --- | --- |
| Cuota agotada, plugin sano | `quota_exceeded`; no incrementa fallos del breaker. |
| Plugin con timeouts repetidos | `timeout`; incrementa fallos y puede abrir breaker. |
| Circuito abierto | `circuit_open`; no consume cuota de worker. |
| Entrada demasiado grande | `input_quota_exceeded`; no incrementa breaker. |
| Salida demasiado grande | `output_quota_exceeded`; política explícita sobre breaker. |
| Proveedor responde 429 | `provider_rate_limited`; backoff y posible apertura. |
| Proveedor responde 401 | `provider_auth_error`; no reintentar indefinidamente. |
| Worker crash | `worker_crashed`; incrementa breaker. |
| Cancelación del usuario | `cancelled`; no incrementa breaker. |
| Fase sin capacidad | `phase_quota_exceeded`; no penaliza al plugin. |

Una regla importante es clasificar el incidente en el punto donde ocurre. Un plugin no debe ser penalizado porque otro plugin consumió la cuota global del host.

## 10. Pruebas de seguridad

### 10.1 Escape de filesystem

Un plugin de prueba intenta:

- leer `../secreto`;
- abrir una ruta fuera del workspace;
- seguir un enlace simbólico fuera del workspace;
- escribir en el directorio del host;
- llenar el directorio temporal.

Resultado esperado: operación denegada, worker contenido y evento de seguridad registrado sin incluir secretos.

### 10.2 Acceso a credenciales

El worker debe recibir un entorno filtrado. Las pruebas deben confirmar:

- que `os.environ` no contiene secretos no declarados;
- que una credencial autorizada no aparece en stdout, stderr ni excepciones;
- que el resultado pasa por redacción antes de registrarse;
- que un plugin no puede solicitar variables arbitrarias mediante el payload.

### 10.3 Red no autorizada

Un plugin intenta conectarse a un dominio no permitido. El supervisor debe denegar la conexión o ejecutarlo en un namespace sin red. La prueba debe distinguir entre:

- red deshabilitada;
- dominio no incluido en allowlist;
- cuota de solicitudes agotada;
- timeout de red;
- respuesta demasiado grande.

### 10.4 Creación de procesos

Un plugin intenta ejecutar `subprocess`. Si la capacidad `process.spawn` no está declarada, la operación debe fallar. Si está declarada, debe estar limitada por la cuota de procesos y por el perfil de aislamiento.

## 11. Pruebas de métricas y trazabilidad

Cada ejecución debe producir métricas mínimas:

```text
request_id
plugin_id
plugin_version
phase
status
queue_wait_ms
execution_ms
worker_start_ms
input_bytes
output_bytes
quota_decision
circuit_state_before
circuit_state_after
failure_class
```

Pruebas:

1. Una ejecución exitosa registra estado `closed` antes y después.
2. Una ejecución rechazada por cuota no registra tiempo de ejecución del plugin.
3. Una ejecución rechazada por circuito no crea worker.
4. Un timeout registra deadline y causa, sin payload completo.
5. Una transición del breaker emite un evento único.
6. Los contadores por plugin y por fase coinciden con el número de eventos aceptados.
7. Los secretos no aparecen en ninguna métrica ni etiqueta.

## 12. Pruebas de propiedades e invariantes

Además de casos concretos, conviene usar property-based testing para validar invariantes:

- el número de slots activos nunca supera el límite;
- los tokens nunca son negativos ni superiores a la capacidad;
- un circuito `OPEN` nunca permite ejecución normal;
- un circuito `HALF_OPEN` permite como máximo una prueba simultánea;
- un `release` no puede producir capacidad superior a la configurada;
- el estado de plugin A no cambia al registrar eventos de plugin B;
- el resultado nunca supera `max_output_bytes`;
- toda ejecución aceptada termina en éxito, fallo tipado, timeout o cancelación.

Ejemplo conceptual:

```python
@given(event_sequences())
def test_limiter_invariants(events):
    limiter = ConcurrencyLimiter(limit=3)
    for event in events:
        apply_event(limiter, event)
        assert 0 <= limiter.active <= 3
```

## 13. Fixtures y dobles recomendados

La suite debe definir fixtures reutilizables:

| Fixture | Función |
| --- | --- |
| `FakeClock` | Avanza el tiempo sin esperar en tiempo real. |
| `FakeMetrics` | Recoge eventos en memoria para aserciones. |
| `HealthyPlugin` | Responde correctamente. |
| `FlakyPlugin` | Falla N veces y luego se recupera. |
| `SlowPlugin` | Duerme o bloquea de forma controlada. |
| `CrashPlugin` | Termina con error o señal. |
| `OversizedOutputPlugin` | Produce más bytes que la cuota. |
| `NetworkTestServer` | Responde con 200, 429, 500 y timeout. |
| `FakeWorkerFactory` | Permite contar workers creados y destruidos. |
| `IsolatedWorkspace` | Crea directorios temporales controlados. |

Las pruebas deben ser deterministas y evitar depender de servicios públicos, APIs reales o credenciales reales.

## 14. Orden de implementación de la suite

### Etapa 1 — Unitarias deterministas

Implementar primero:

- composición de políticas;
- token bucket;
- límites de tamaño;
- concurrencia lógica;
- máquina de estados del breaker;
- clasificación de errores;
- reloj falso;
- invariantes básicas.

### Etapa 2 — Integración local

Después:

- supervisor con worker real;
- timeout;
- crash;
- salida grande;
- liberación de recursos;
- transición a `OPEN`;
- recuperación a `CLOSED`.

### Etapa 3 — Seguridad y concurrencia

Luego:

- filesystem;
- entorno de variables;
- red;
- procesos hijos;
- fairness;
- probes concurrentes;
- reinicio de workers.

### Etapa 4 — Carga y regresión

Finalmente:

- carga sostenida por fase;
- mezcla de plugins saludables y defectuosos;
- 304, 1.000 y 5.000 herramientas indexadas;
- saturación global;
- recuperación después de ráfagas de errores;
- comparación de latencias p50, p95 y p99.

## 15. Criterios de aceptación

La implementación puede considerarse lista para una primera versión cuando cumpla todos estos criterios:

1. Las políticas inválidas se rechazan al cargar configuración.
2. La cuota efectiva siempre es igual o más restrictiva que sus políticas padre.
3. La concurrencia activa nunca supera el límite.
4. Las cuotas de entrada y salida se aplican por bytes serializados.
5. Un timeout libera slots y recursos.
6. Un crash del worker no derriba el supervisor.
7. Un circuito abierto no crea workers ni consume cuota de ejecución.
8. El circuito abre después del umbral documentado.
9. El circuito permite como máximo un probe en `HALF_OPEN`.
10. Un probe exitoso cierra el circuito.
11. Un probe fallido vuelve a abrirlo.
12. Los errores de entrada no abren el circuito.
13. Las cuotas globales no penalizan al plugin equivocado.
14. Los secretos no aparecen en logs, métricas o errores.
15. Las pruebas no dependen de servicios externos reales.
16. Las pruebas de carga no alteran el comportamiento de las pruebas unitarias.
17. Todas las transiciones importantes emiten métricas verificables.

## 16. Conclusión

La suite debe tratar cuotas y circuit breakers como dos mecanismos complementarios. Las cuotas protegen recursos; los circuit breakers protegen la disponibilidad frente a fallos repetidos. No deben compartir indiscriminadamente sus contadores ni sus causas.

La ruta más segura es comenzar con una máquina de estados y un sistema de cuotas completamente deterministas, usando reloj falso y dobles de worker. Después deben añadirse pruebas con procesos reales, límites de salida, timeouts, crashes, concurrencia y seguridad. La primera versión no necesita medir rendimiento distribuido, pero sí debe demostrar que un plugin lento, defectuoso o abusivo no puede bloquear el host ni consumir indefinidamente sus recursos.

## Referencias

[1]: https://github.com/hubgunter4-ops/content-skills-toolkit "Repositorio Content Skills Toolkit"
[2]: https://json-schema.org/specification "JSON Schema Specification"
