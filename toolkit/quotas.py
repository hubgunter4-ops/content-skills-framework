"""Composable quotas for host, phase, tool and tenant execution scopes."""
from __future__ import annotations

from dataclasses import dataclass
import threading
import time
from typing import Iterable

from .errors import QuotaExceededError


@dataclass(frozen=True)
class QuotaPolicy:
    name: str
    max_concurrent: int = 1
    rate_per_second: float = 1.0
    burst: int = 1
    max_input_bytes: int = 2_000_000
    max_output_bytes: int = 8_000_000
    max_duration_seconds: float = 120.0

    def __post_init__(self) -> None:
        if self.max_concurrent < 1 or self.rate_per_second <= 0 or self.burst < 1:
            raise ValueError("concurrencia, rate y burst deben ser positivos")
        if self.max_input_bytes < 1 or self.max_output_bytes < 1 or self.max_duration_seconds <= 0:
            raise ValueError("los límites de bytes y duración deben ser positivos")


@dataclass(frozen=True)
class QuotaSnapshot:
    scope: str
    active: int
    tokens: float
    accepted: int
    rejected: int
    released: int


@dataclass
class _Bucket:
    tokens: float
    updated_at: float
    active: int = 0
    accepted: int = 0
    rejected: int = 0
    released: int = 0


class QuotaLease:
    def __init__(self, manager: "QuotaManager", scopes: tuple[str, ...], policies: tuple[QuotaPolicy, ...], started_at: float) -> None:
        self._manager = manager
        self.scopes = scopes
        self.policies = policies
        self.started_at = started_at
        self._released = False

    @property
    def max_output_bytes(self) -> int:
        return min(policy.max_output_bytes for policy in self.policies)

    @property
    def max_duration_seconds(self) -> float:
        return min(policy.max_duration_seconds for policy in self.policies)

    def release(self, *, output_bytes: int = 0, duration_seconds: float | None = None) -> None:
        if self._released:
            return
        self._released = True
        elapsed = duration_seconds if duration_seconds is not None else time.monotonic() - self.started_at
        self._manager._release(self, output_bytes=output_bytes, duration_seconds=elapsed)

    def __enter__(self) -> "QuotaLease":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.release()


class QuotaManager:
    """Reserve every applicable scope; the most restrictive limit wins."""

    def __init__(self, policies: dict[str, QuotaPolicy] | None = None) -> None:
        self.policies = dict(policies or {"default": QuotaPolicy("default", max_concurrent=4, burst=60, rate_per_second=10)})
        self._buckets: dict[str, _Bucket] = {
            name: _Bucket(tokens=policy.burst, updated_at=time.monotonic())
            for name, policy in self.policies.items()
        }
        self._lock = threading.RLock()

    def reserve(self, scopes: Iterable[str], *, input_bytes: int = 0) -> QuotaLease:
        scope_tuple = tuple(dict.fromkeys(str(scope) for scope in scopes))
        if not scope_tuple:
            scope_tuple = ("default",)
        with self._lock:
            policies = tuple(self._policy_for(scope) for scope in scope_tuple)
            now = time.monotonic()
            failures: list[str] = []
            for scope, policy in zip(scope_tuple, policies):
                bucket = self._buckets.setdefault(scope, _Bucket(policy.burst, now))
                self._refill(bucket, policy, now)
                if input_bytes > policy.max_input_bytes:
                    failures.append(f"{scope}: input_bytes")
                if bucket.active >= policy.max_concurrent:
                    failures.append(f"{scope}: concurrency")
                if bucket.tokens < 1:
                    failures.append(f"{scope}: rate")
            if failures:
                for scope in scope_tuple:
                    self._buckets[scope].rejected += 1
                raise QuotaExceededError("; ".join(failures))
            for scope, policy in zip(scope_tuple, policies):
                bucket = self._buckets[scope]
                bucket.tokens -= 1
                bucket.active += 1
                bucket.accepted += 1
            return QuotaLease(self, scope_tuple, policies, now)

    def _policy_for(self, scope: str) -> QuotaPolicy:
        return self.policies.get(scope, self.policies.get("default", QuotaPolicy("default")))

    @staticmethod
    def _refill(bucket: _Bucket, policy: QuotaPolicy, now: float) -> None:
        elapsed = max(0.0, now - bucket.updated_at)
        bucket.tokens = min(float(policy.burst), bucket.tokens + elapsed * policy.rate_per_second)
        bucket.updated_at = now

    def _release(self, lease: QuotaLease, *, output_bytes: int, duration_seconds: float) -> None:
        with self._lock:
            failures: list[str] = []
            for scope, policy in zip(lease.scopes, lease.policies):
                if output_bytes > policy.max_output_bytes:
                    failures.append(f"{scope}: output_bytes")
                if duration_seconds > policy.max_duration_seconds:
                    failures.append(f"{scope}: duration")
            for scope in lease.scopes:
                bucket = self._buckets[scope]
                bucket.active = max(0, bucket.active - 1)
                bucket.released += 1
            if failures:
                raise QuotaExceededError("; ".join(failures))

    def snapshot(self) -> tuple[QuotaSnapshot, ...]:
        with self._lock:
            now = time.monotonic()
            values = []
            for scope, policy in self.policies.items():
                bucket = self._buckets.setdefault(scope, _Bucket(policy.burst, now))
                self._refill(bucket, policy, now)
                values.append(QuotaSnapshot(scope, bucket.active, bucket.tokens, bucket.accepted, bucket.rejected, bucket.released))
            return tuple(values)


__all__ = ["QuotaLease", "QuotaManager", "QuotaPolicy", "QuotaSnapshot"]
