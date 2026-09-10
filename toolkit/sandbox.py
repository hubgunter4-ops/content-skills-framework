"""Best-effort process sandbox primitives for Linux workers."""
from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import resource
from typing import Callable


@dataclass(frozen=True)
class SandboxPolicy:
    name: str
    timeout_seconds: float
    cpu_seconds: int
    memory_mb: int
    max_output_bytes: int
    max_input_bytes: int
    max_processes: int
    max_open_files: int
    allow_network: bool = False
    allow_credentials: bool = False
    allow_file_write: bool = False


POLICIES = {
    "trusted-pure": SandboxPolicy("trusted-pure", 30, 30, 512, 2_000_000, 2_000_000, 8, 64),
    "trusted-io": SandboxPolicy("trusted-io", 120, 120, 1024, 8_000_000, 8_000_000, 16, 128, allow_file_write=True),
    "third-party": SandboxPolicy("third-party", 60, 60, 512, 4_000_000, 4_000_000, 4, 64),
    "untrusted": SandboxPolicy("untrusted", 15, 15, 256, 1_000_000, 1_000_000, 2, 32),
}


def get_policy(name: str) -> SandboxPolicy:
    try:
        return POLICIES[name]
    except KeyError as exc:
        raise ValueError(f"Perfil de sandbox no registrado: {name}") from exc


def safe_environment(*, allow_credentials: bool = False, extra: dict[str, str] | None = None) -> dict[str, str]:
    allowed = {key: value for key, value in os.environ.items() if key in {"PATH", "LANG", "LC_ALL", "TZ", "PYTHONPATH"}}
    allowed["PYTHONUNBUFFERED"] = "1"
    if not allow_credentials:
        for key in list(allowed):
            if any(marker in key.upper() for marker in ("KEY", "TOKEN", "SECRET", "PASSWORD", "CREDENTIAL")):
                allowed.pop(key, None)
    if extra:
        for key, value in extra.items():
            key = str(key)
            if not allow_credentials and any(marker in key.upper() for marker in ("KEY", "TOKEN", "SECRET", "PASSWORD", "CREDENTIAL")):
                continue
            allowed[key] = str(value)
    return allowed


def make_preexec(policy: SandboxPolicy, workspace: Path) -> Callable[[], None]:
    def limit_child() -> None:
        os.setsid()
        os.chdir(workspace)
        limits = [
            (resource.RLIMIT_CPU, policy.cpu_seconds, policy.cpu_seconds),
            (resource.RLIMIT_AS, policy.memory_mb * 1024 * 1024, policy.memory_mb * 1024 * 1024),
            # Keep a hard file ceiling above the logical output quota so the
            # supervisor can classify an oversized response instead of the
            # kernel terminating the worker before inspection.
            (resource.RLIMIT_FSIZE, max(policy.max_output_bytes * 2, 8 * 1024 * 1024), max(policy.max_output_bytes * 2, 8 * 1024 * 1024)),
            (resource.RLIMIT_NOFILE, policy.max_open_files, policy.max_open_files),
        ]
        if hasattr(resource, "RLIMIT_NPROC"):
            limits.append((resource.RLIMIT_NPROC, policy.max_processes, policy.max_processes))
        for kind, soft, hard in limits:
            try:
                resource.setrlimit(kind, (soft, hard))
            except (ValueError, OSError):
                continue
    return limit_child


__all__ = ["POLICIES", "SandboxPolicy", "get_policy", "make_preexec", "safe_environment"]
