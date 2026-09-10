"""In-memory caches layered over the persistent SQLite tool index."""
from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
import json
from pathlib import Path
import threading
import time
from typing import Any, Callable, Generic, TypeVar

from .models import ToolMetadata
from .persistent_index import IndexedTool, ensure_index, list_index, lookup

T = TypeVar("T")


@dataclass(frozen=True)
class CacheStats:
    l1_hits: int
    l1_misses: int
    l2_hits: int
    l2_misses: int
    l3_hits: int
    l3_misses: int
    evictions: int
    invalidations: int
    entries_l1: int
    entries_l2: int
    entries_l3: int
    estimated_bytes: int

    @property
    def total_hits(self) -> int:
        return self.l1_hits + self.l2_hits + self.l3_hits

    @property
    def total_misses(self) -> int:
        return self.l1_misses + self.l2_misses + self.l3_misses

    @property
    def hit_rate(self) -> float:
        total = self.total_hits + self.total_misses
        return self.total_hits / total if total else 0.0


@dataclass
class _Entry(Generic[T]):
    value: T
    created_at: float
    last_access: float
    metadata_digest: str | None = None


class _LRU(Generic[T]):
    def __init__(self, capacity: int, ttl_seconds: float | None = None) -> None:
        if capacity < 1:
            raise ValueError("capacity debe ser mayor que cero")
        if ttl_seconds is not None and ttl_seconds <= 0:
            raise ValueError("ttl_seconds debe ser mayor que cero")
        self.capacity = capacity
        self.ttl_seconds = ttl_seconds
        self.items: OrderedDict[str, _Entry[T]] = OrderedDict()

    def get(self, key: str, now: float) -> tuple[T | None, bool]:
        entry = self.items.get(key)
        if entry is None:
            return None, False
        if self.ttl_seconds is not None and now - entry.created_at >= self.ttl_seconds:
            del self.items[key]
            return None, False
        entry.last_access = now
        self.items.move_to_end(key)
        return entry.value, True

    def put(self, key: str, value: T, now: float, metadata_digest: str | None = None) -> bool:
        evicted = False
        self.items[key] = _Entry(value, now, now, metadata_digest)
        self.items.move_to_end(key)
        while len(self.items) > self.capacity:
            self.items.popitem(last=False)
            evicted = True
        return evicted

    def delete(self, key: str) -> bool:
        return self.items.pop(key, None) is not None

    def clear(self) -> int:
        count = len(self.items)
        self.items.clear()
        return count


class ToolCache:
    """L1 identifier cache, L2 metadata/schema cache and L3 factory cache.

    The cache never scans plugin code. L3 accepts an explicit loader callback;
    therefore importing a plugin is an opt-in operation performed by the
    future supervisor, not by lookup or metadata resolution.
    """

    def __init__(
        self,
        root: Path,
        index_path: Path,
        *,
        l1_capacity: int = 512,
        l2_capacity: int = 512,
        l3_capacity: int = 64,
        ttl_seconds: float | None = 900.0,
    ) -> None:
        self.root = root
        self.index_path = index_path
        self._lock = threading.RLock()
        self._l1: _LRU[IndexedTool] = _LRU(l1_capacity, ttl_seconds)
        self._l2: _LRU[object] = _LRU(l2_capacity, ttl_seconds)
        self._l3: _LRU[Any] = _LRU(l3_capacity, ttl_seconds)
        self._l1_hits = self._l1_misses = 0
        self._l2_hits = self._l2_misses = 0
        self._l3_hits = self._l3_misses = 0
        self._evictions = self._invalidations = 0
        self._estimated_bytes = 0
        self._closed = False

    def _refresh(self) -> None:
        if self._closed:
            raise RuntimeError("ToolCache está cerrada")
        _, rebuilt = ensure_index(self.root, self.index_path)
        if rebuilt:
            self.clear()
            self._invalidations += 1

    def refresh(self) -> None:
        """Ensure the SQLite source is current before bulk candidate queries."""
        with self._lock:
            self._refresh()

    def _record(self, tool_id: str) -> IndexedTool | None:
        self._refresh()
        now = time.monotonic()
        record, hit = self._l1.get(tool_id, now)
        if hit:
            self._l1_hits += 1
            return record
        self._l1_misses += 1
        record = lookup(self.index_path, tool_id)
        if record is not None and self._l1.put(tool_id, record, now, record.metadata_digest):
            self._evictions += 1
        return record

    def resolve(self, identifier: str) -> IndexedTool | None:
        """Resolve a qualified id or unambiguous short slug through L1/L2 source."""
        requested = identifier.strip().strip("/")
        direct = self._record(requested)
        if direct is not None:
            return direct
        candidates = [item for item in list_index(self.index_path) if item.tool_id.rsplit("/", 1)[-1] == requested]
        if len(candidates) == 1:
            return self._record(candidates[0].tool_id)
        return None

    def metadata(self, identifier: str) -> ToolMetadata:
        record = self.resolve(identifier)
        if record is None:
            raise KeyError(f"No existe la herramienta: {identifier}")
        key = f"metadata:{record.tool_id}:{record.metadata_digest}"
        now = time.monotonic()
        with self._lock:
            value, hit = self._l2.get(key, now)
            if hit:
                self._l2_hits += 1
                return value  # type: ignore[return-value]
            self._l2_misses += 1
            value = record.to_metadata()
            if self._l2.put(key, value, now, record.metadata_digest):
                self._evictions += 1
            self._estimated_bytes += len(json.dumps(value.to_dict(), ensure_ascii=False))
            return value

    def schema(self, identifier: str, *, output: bool = True) -> dict[str, Any]:
        record = self.resolve(identifier)
        if record is None:
            raise KeyError(f"No existe la herramienta: {identifier}")
        path_value = record.output_schema if output else record.input_schema
        if not path_value:
            raise ValueError(f"{record.tool_id} no tiene esquema cargado")
        key = f"schema:{record.tool_id}:{record.metadata_digest}:{'out' if output else 'in'}"
        now = time.monotonic()
        with self._lock:
            value, hit = self._l2.get(key, now)
            if hit:
                self._l2_hits += 1
                return value  # type: ignore[return-value]
            self._l2_misses += 1
            path = Path(path_value)
            value = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(value, dict):
                raise ValueError(f"El esquema no es un objeto: {path}")
            if self._l2.put(key, value, now, record.metadata_digest):
                self._evictions += 1
            self._estimated_bytes += len(json.dumps(value, ensure_ascii=False))
            return value

    def factory(self, identifier: str, loader: Callable[[IndexedTool], T]) -> T:
        """Load and cache a factory only when the caller explicitly asks."""
        record = self.resolve(identifier)
        if record is None:
            raise KeyError(f"No existe la herramienta: {identifier}")
        key = f"factory:{record.tool_id}:{record.metadata_digest}"
        now = time.monotonic()
        with self._lock:
            value, hit = self._l3.get(key, now)
            if hit:
                self._l3_hits += 1
                return value  # type: ignore[return-value]
            self._l3_misses += 1
            value = loader(record)
            if self._l3.put(key, value, now, record.metadata_digest):
                self._evictions += 1
            return value

    def invalidate(self, identifier: str | None = None) -> None:
        with self._lock:
            if identifier is None:
                removed = self.clear()
                self._invalidations += removed
                return
            record = self._record(identifier)
            tool_id = record.tool_id if record else identifier.strip().strip("/")
            for cache in (self._l1, self._l2, self._l3):
                for key in list(cache.items):
                    if tool_id in key:
                        cache.delete(key)
            self._invalidations += 1

    def clear(self) -> int:
        with self._lock:
            count = self._l1.clear() + self._l2.clear() + self._l3.clear()
            self._estimated_bytes = 0
            return count

    def stats(self) -> CacheStats:
        with self._lock:
            return CacheStats(
                l1_hits=self._l1_hits,
                l1_misses=self._l1_misses,
                l2_hits=self._l2_hits,
                l2_misses=self._l2_misses,
                l3_hits=self._l3_hits,
                l3_misses=self._l3_misses,
                evictions=self._evictions,
                invalidations=self._invalidations,
                entries_l1=len(self._l1.items),
                entries_l2=len(self._l2.items),
                entries_l3=len(self._l3.items),
                estimated_bytes=self._estimated_bytes,
            )

    def close(self) -> None:
        with self._lock:
            self.clear()
            self._closed = True


__all__ = ["CacheStats", "ToolCache"]
