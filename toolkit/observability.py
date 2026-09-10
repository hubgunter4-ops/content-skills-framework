"""Dependency-free metrics and redacted structured events for executions."""
from __future__ import annotations

from dataclasses import dataclass
import re
import threading
from typing import Any, Mapping

_SECRET_KEY = re.compile(r"(key|token|secret|password|credential|authorization)", re.IGNORECASE)


def redact(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): "[REDACTED]" if _SECRET_KEY.search(str(key)) else redact(item) for key, item in value.items()}
    if isinstance(value, list):
        return [redact(item) for item in value]
    if isinstance(value, tuple):
        return tuple(redact(item) for item in value)
    return value


@dataclass(frozen=True)
class MetricsSnapshot:
    count: int
    by_status: dict[str, int]
    p50_ms: float
    p95_ms: float
    p99_ms: float


class ExecutionMetrics:
    def __init__(self, *, max_samples: int = 10_000) -> None:
        if max_samples < 1:
            raise ValueError("max_samples debe ser positivo")
        self.max_samples = max_samples
        self._durations: list[float] = []
        self._statuses: dict[str, int] = {}
        self._lock = threading.Lock()

    def observe(self, duration_ms: float, status: str) -> None:
        with self._lock:
            self._durations.append(max(0.0, float(duration_ms)))
            if len(self._durations) > self.max_samples:
                self._durations.pop(0)
            self._statuses[status] = self._statuses.get(status, 0) + 1

    def snapshot(self) -> MetricsSnapshot:
        with self._lock:
            values = sorted(self._durations)
            return MetricsSnapshot(len(values), dict(self._statuses), *(self._percentile(values, rank) for rank in (0.50, 0.95, 0.99)))

    @staticmethod
    def _percentile(values: list[float], rank: float) -> float:
        if not values:
            return 0.0
        index = min(len(values) - 1, max(0, int((len(values) - 1) * rank)))
        return values[index]

    def event(self, *, tool_id: str, status: str, duration_ms: float, extra: Mapping[str, Any] | None = None) -> dict[str, Any]:
        self.observe(duration_ms, status)
        event = {"tool_id": tool_id, "status": status, "duration_ms": round(duration_ms, 3)}
        if extra:
            event.update(redact(extra))
        return event


__all__ = ["ExecutionMetrics", "MetricsSnapshot", "redact"]
