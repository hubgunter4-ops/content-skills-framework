"""Thread-safe circuit breakers for tools and providers."""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from enum import StrEnum
import threading
import time
from typing import Iterable

from .errors import CircuitOpenError


class CircuitState(StrEnum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass(frozen=True)
class CircuitPolicy:
    failure_threshold: int = 3
    failure_window_seconds: float = 60.0
    cooldown_seconds: float = 10.0
    max_backoff_seconds: float = 300.0
    count_statuses: frozenset[str] = frozenset({"error", "timeout", "worker_crashed"})

    def __post_init__(self) -> None:
        if self.failure_threshold < 1 or self.failure_window_seconds <= 0 or self.cooldown_seconds <= 0 or self.max_backoff_seconds <= 0:
            raise ValueError("los umbrales y ventanas del circuit breaker deben ser positivos")


@dataclass(frozen=True)
class CircuitSnapshot:
    key: str
    state: CircuitState
    failures_in_window: int
    opened_count: int
    transitions: int
    probe_in_flight: bool
    next_probe_at: float | None


@dataclass
class _Circuit:
    state: CircuitState = CircuitState.CLOSED
    failures: deque[float] = None  # type: ignore[assignment]
    opened_at: float | None = None
    opened_count: int = 0
    transitions: int = 0
    probe_in_flight: bool = False

    def __post_init__(self) -> None:
        if self.failures is None:
            self.failures = deque()


class CircuitPermit:
    def __init__(self, manager: "CircuitBreakerManager", key: str, probe: bool) -> None:
        self.manager = manager
        self.key = key
        self.probe = probe
        self._finished = False

    def success(self) -> None:
        if not self._finished:
            self._finished = True
            self.manager.record_success(self.key, probe=self.probe)

    def failure(self, status: str) -> None:
        if not self._finished:
            self._finished = True
            self.manager.record_failure(self.key, status, probe=self.probe)

    def cancel(self) -> None:
        if not self._finished:
            self._finished = True
            self.manager.cancel(self.key, probe=self.probe)

    def __enter__(self) -> "CircuitPermit":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if exc_type:
            self.failure("error")
        else:
            self.success()


class CircuitBreakerManager:
    def __init__(self, policy: CircuitPolicy | None = None, policies: dict[str, CircuitPolicy] | None = None) -> None:
        self.default_policy = policy or CircuitPolicy()
        self.policies = dict(policies or {})
        self._circuits: dict[str, _Circuit] = {}
        self._lock = threading.RLock()

    def _policy(self, key: str) -> CircuitPolicy:
        return self.policies.get(key, self.default_policy)

    def _circuit(self, key: str) -> _Circuit:
        return self._circuits.setdefault(key, _Circuit())

    def acquire(self, key: str) -> CircuitPermit:
        now = time.monotonic()
        with self._lock:
            circuit = self._circuit(key)
            policy = self._policy(key)
            self._prune(circuit, policy, now)
            if circuit.state == CircuitState.OPEN:
                backoff = min(policy.max_backoff_seconds, policy.cooldown_seconds * (2 ** max(0, circuit.opened_count - 1)))
                if circuit.opened_at is None:
                    raise CircuitOpenError(f"circuit open for {key}; missing opening timestamp")
                next_probe = circuit.opened_at + backoff
                if now < next_probe:
                    raise CircuitOpenError(f"circuit open for {key}; retry after {next_probe - now:.3f}s")
                circuit.state = CircuitState.HALF_OPEN
                circuit.transitions += 1
            if circuit.state == CircuitState.HALF_OPEN:
                if circuit.probe_in_flight:
                    raise CircuitOpenError(f"half_open probe already running for {key}")
                circuit.probe_in_flight = True
                return CircuitPermit(self, key, probe=True)
            return CircuitPermit(self, key, probe=False)

    def record_success(self, key: str, *, probe: bool = False) -> None:
        with self._lock:
            circuit = self._circuit(key)
            if probe or circuit.state == CircuitState.HALF_OPEN:
                circuit.state = CircuitState.CLOSED
                circuit.failures.clear()
                circuit.opened_at = None
                circuit.probe_in_flight = False
                circuit.transitions += 1
            else:
                circuit.failures.clear()

    def record_failure(self, key: str, status: str, *, probe: bool = False) -> None:
        with self._lock:
            circuit = self._circuit(key)
            policy = self._policy(key)
            now = time.monotonic()
            if probe or circuit.state == CircuitState.HALF_OPEN:
                circuit.probe_in_flight = False
                circuit.state = CircuitState.OPEN
                circuit.opened_at = now
                circuit.opened_count += 1
                circuit.transitions += 1
                return
            if status not in policy.count_statuses:
                return
            self._prune(circuit, policy, now)
            circuit.failures.append(now)
            if len(circuit.failures) >= policy.failure_threshold:
                circuit.state = CircuitState.OPEN
                circuit.opened_at = now
                circuit.opened_count += 1
                circuit.transitions += 1

    def cancel(self, key: str, *, probe: bool = False) -> None:
        if not probe:
            return
        with self._lock:
            circuit = self._circuit(key)
            circuit.probe_in_flight = False
            if circuit.state == CircuitState.HALF_OPEN:
                circuit.state = CircuitState.OPEN

    @staticmethod
    def _prune(circuit: _Circuit, policy: CircuitPolicy, now: float) -> None:
        cutoff = now - policy.failure_window_seconds
        while circuit.failures and circuit.failures[0] < cutoff:
            circuit.failures.popleft()

    def snapshot(self, key: str) -> CircuitSnapshot:
        with self._lock:
            circuit = self._circuit(key)
            policy = self._policy(key)
            now = time.monotonic()
            self._prune(circuit, policy, now)
            next_probe = None
            if circuit.state == CircuitState.OPEN and circuit.opened_at is not None:
                next_probe = circuit.opened_at + min(policy.max_backoff_seconds, policy.cooldown_seconds * (2 ** max(0, circuit.opened_count - 1)))
            return CircuitSnapshot(key, circuit.state, len(circuit.failures), circuit.opened_count, circuit.transitions, circuit.probe_in_flight, next_probe)

    def snapshots(self, keys: Iterable[str] | None = None) -> tuple[CircuitSnapshot, ...]:
        selected = keys if keys is not None else tuple(self._circuits)
        return tuple(self.snapshot(key) for key in selected)


__all__ = ["CircuitBreakerManager", "CircuitPermit", "CircuitPolicy", "CircuitSnapshot", "CircuitState"]
