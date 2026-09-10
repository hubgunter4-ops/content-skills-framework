# Fase 5 — Supervisor, sandbox y ejecución segura de scripts

## Alcance implementado

La Fase 5 añade un backend de subproceso para ejecutar los `run.py` existentes sin ejecutar el plugin dentro del proceso host. El supervisor usa un workspace temporal por ejecución, entrada JSON mediante `--input` y salida JSON por stdout; stderr queda separado y nunca se mezcla con la respuesta.

Archivos principales:

- `toolkit/supervisor.py`;
- `toolkit/sandbox.py`;
- `tests/test_supervisor.py`.

## Perfiles

| Perfil | Timeout | Memoria | Salida | Red | Credenciales | Escritura |
| --- | ---: | ---: | ---: | --- | --- | --- |
| `trusted-pure` | 30 s | 512 MB | 2 MB | No | No | No |
| `trusted-io` | 120 s | 1 GB | 8 MB | No | No | Sí en workspace |
| `third-party` | 60 s | 512 MB | 4 MB | No | No | No |
| `untrusted` | 15 s | 256 MB | 1 MB | No | No | No |

Los perfiles son políticas de aplicación. El estado de aislamiento reportado por esta implementación es `subprocess-limited`.

## Límites aplicados

En Linux, el hijo se ejecuta en una nueva sesión y recibe límites `RLIMIT_CPU`, `RLIMIT_AS`, `RLIMIT_FSIZE`, `RLIMIT_NOFILE` y, cuando está disponible, `RLIMIT_NPROC`. El supervisor añade:

- límite de bytes de entrada antes de crear el worker;
- límite lógico de stdout/stderr;
- timeout total;
- terminación del grupo completo ante timeout;
- entorno mínimo filtrado;
- `stdin` desconectado;
- workspace temporal;
- clasificación de `script_not_found`, `input_too_large`, `timeout`, `output_too_large`, `worker_exit` e `invalid_worker_output`.

Las variables con marcadores `KEY`, `TOKEN`, `SECRET`, `PASSWORD` o `CREDENTIAL` no se heredan por defecto.

## Límite de seguridad

Este backend es aislamiento por proceso con límites de recursos. **No equivale a un contenedor, una máquina virtual ni un sandbox de kernel completo.** No garantiza por sí solo aislamiento fuerte de red, syscall, filesystem global o ataques contra el kernel. La siguiente evolución debe añadir un backend de contenedor sin privilegios o una política OS especializada para plugins no confiables.

La aplicación debe presentar este límite al seleccionar perfiles: `untrusted` reduce impacto y tiempo, pero no convierte código arbitrario en código confiable.

## Uso

```python
from pathlib import Path
from toolkit import Supervisor

execution = Supervisor(root=Path(".")).run_script(
    Path("toolkit/phase-2-datos/validacion-de-datos/run.py"),
    {"objective": "Validar datos", "content": "a,b\n1,2"},
    policy="third-party",
)

print(execution.result.to_dict())
```

La salida incluye estado, código de retorno, duración, tamaños de stdout/stderr y nivel de aislamiento. El script nunca recibe las credenciales del proceso por defecto.

## Pruebas

La suite cubre:

- worker saludable real del catálogo;
- worker defectuoso;
- JSON inválido;
- timeout y terminación;
- salida excesiva;
- entrada excesiva;
- script inexistente;
- filtrado de secretos;
- perfil desconocido.
