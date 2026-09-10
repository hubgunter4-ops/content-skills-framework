"""Supervisor for running tool scripts in isolated subprocesses."""
from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
from typing import Any, Iterable

from .models import ExecutionResult, Status
from .quotas import QuotaManager, QuotaLease
from .circuit_breaker import CircuitBreakerManager, CircuitPermit
from .errors import CircuitOpenError, QuotaExceededError
from .sandbox import SandboxPolicy, get_policy, make_preexec, safe_environment


@dataclass(frozen=True)
class SupervisedExecution:
    result: ExecutionResult
    returncode: int | None
    duration_ms: float
    stdout_bytes: int
    stderr_bytes: int
    isolation: str


class Supervisor:
    def __init__(self, *, root: Path, python_executable: str | None = None, quota_manager: QuotaManager | None = None, circuit_breaker: CircuitBreakerManager | None = None) -> None:
        self.root = root
        self.python_executable = python_executable or sys.executable
        self.quota_manager = quota_manager
        self.circuit_breaker = circuit_breaker

    def run_script(
        self,
        script: Path,
        payload: dict[str, Any],
        *,
        policy: str | SandboxPolicy = "third-party",
        extra_env: dict[str, str] | None = None,
        quota_scopes: Iterable[str] = ("host", "tool"),
        circuit_key: str | None = None,
    ) -> SupervisedExecution:
        selected = get_policy(policy) if isinstance(policy, str) else policy
        if len(json.dumps(payload, ensure_ascii=False).encode("utf-8")) > selected.max_input_bytes:
            return self._failure(Status.ERROR, "input_too_large")
        script = script.resolve()
        if not script.is_file():
            return self._failure(Status.ERROR, "script_not_found")
        permit: CircuitPermit | None = None
        breaker_key = circuit_key or str(script)
        if self.circuit_breaker is not None:
            try:
                permit = self.circuit_breaker.acquire(breaker_key)
            except CircuitOpenError as exc:
                return SupervisedExecution(ExecutionResult(status=Status.CIRCUIT_OPEN, error={"code": "circuit_open", "message": str(exc)}), None, 0.0, 0, 0, "subprocess-limited")
        lease: QuotaLease | None = None
        if self.quota_manager is not None:
            try:
                lease = self.quota_manager.reserve(quota_scopes, input_bytes=len(json.dumps(payload, ensure_ascii=False).encode("utf-8")))
            except QuotaExceededError as exc:
                if permit is not None:
                    permit.cancel()
                return SupervisedExecution(ExecutionResult(status=Status.QUOTA_EXCEEDED, error={"code": "quota_exceeded", "message": str(exc)}), None, 0.0, 0, 0, "subprocess-limited")

        def finish(execution: SupervisedExecution) -> SupervisedExecution:
            if lease is not None:
                try:
                    lease.release(output_bytes=execution.stdout_bytes + execution.stderr_bytes, duration_seconds=execution.duration_ms / 1000)
                except QuotaExceededError as exc:
                    execution = SupervisedExecution(ExecutionResult(status=Status.QUOTA_EXCEEDED, error={"code": "quota_exceeded", "message": str(exc)}), execution.returncode, execution.duration_ms, execution.stdout_bytes, execution.stderr_bytes, execution.isolation)
            if permit is not None:
                if execution.result.status in {Status.ERROR, Status.TIMEOUT, Status.WORKER_CRASHED}:
                    permit.failure(execution.result.status)
                else:
                    permit.success()
            return execution
        import time
        started = time.perf_counter()
        with tempfile.TemporaryDirectory(prefix="content-skills-worker-") as directory:
            workspace = Path(directory)
            request_file = workspace / "request.json"
            request_file.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            command = [self.python_executable, str(script), "--input", str(request_file)]
            env = safe_environment(allow_credentials=selected.allow_credentials, extra=extra_env)
            stdout_file = workspace / "stdout.log"
            stderr_file = workspace / "stderr.log"
            with stdout_file.open("wb") as stdout_handle, stderr_file.open("wb") as stderr_handle:
                process = subprocess.Popen(
                    command,
                    cwd=workspace,
                    env=env,
                    stdout=stdout_handle,
                    stderr=stderr_handle,
                    stdin=subprocess.DEVNULL,
                    start_new_session=sys.platform != "linux",
                    preexec_fn=make_preexec(selected, workspace) if sys.platform == "linux" else None,
                )
                try:
                    returncode = process.wait(timeout=selected.timeout_seconds)
                except subprocess.TimeoutExpired:
                    try:
                        if sys.platform == "linux":
                            os.killpg(process.pid, signal.SIGKILL)
                        else:
                            process.kill()
                    finally:
                        process.wait()
                    duration = (time.perf_counter() - started) * 1000
                    return finish(SupervisedExecution(
                        ExecutionResult(status=Status.TIMEOUT, error={"code": "timeout", "message": "worker deadline exceeded"}),
                        None, duration, stdout_file.stat().st_size, stderr_file.stat().st_size, "subprocess-limited",
                    ))
            duration = (time.perf_counter() - started) * 1000
            stdout_size = stdout_file.stat().st_size
            stderr_size = stderr_file.stat().st_size
            if stdout_size > selected.max_output_bytes or stderr_size > selected.max_output_bytes:
                return finish(SupervisedExecution(
                    ExecutionResult(status=Status.ERROR, error={"code": "output_too_large", "message": "worker output exceeded limit"}),
                    returncode, duration, stdout_size, stderr_size, "subprocess-limited",
                ))
            stdout = stdout_file.read_bytes()
            stderr = stderr_file.read_bytes()
            if returncode != 0:
                return finish(SupervisedExecution(
                    ExecutionResult(status=Status.WORKER_CRASHED, error={"code": "worker_exit", "message": stderr.decode("utf-8", "replace")[-1000:]}),
                    returncode, duration, stdout_size, stderr_size, "subprocess-limited",
                ))
            try:
                value = json.loads(stdout.decode("utf-8"))
                if not isinstance(value, dict):
                    raise ValueError("worker output must be a JSON object")
                result = ExecutionResult(
                    status=str(value.get("status", Status.ERROR)),
                    analysis=dict(value.get("analysis", {})),
                    deliverable=dict(value.get("deliverable", {})),
                    warnings=tuple(str(item) for item in value.get("warnings", [])),
                    provenance=dict(value.get("provenance", {})),
                    error=dict(value["error"]) if value.get("error") else None,
                )
            except (UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError) as exc:
                result = ExecutionResult(status=Status.ERROR, error={"code": "invalid_worker_output", "message": str(exc)})
            return finish(SupervisedExecution(result, returncode, duration, stdout_size, stderr_size, "subprocess-limited"))

    @staticmethod
    def _failure(status: str, code: str) -> SupervisedExecution:
        return SupervisedExecution(
            ExecutionResult(status=status, error={"code": code}), None, 0.0, 0, 0, "subprocess-limited"
        )


__all__ = ["SupervisedExecution", "Supervisor"]
