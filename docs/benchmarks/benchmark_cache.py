from __future__ import annotations

import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from toolkit.cache import _LRU  # noqa: E402


def benchmark(size: int, lookups: int = 5000) -> dict[str, float | int]:
    cache = _LRU[dict[str, str]](capacity=size)
    now = time.monotonic()
    for index in range(size):
        cache.put(f"phase-synthetic/tool-{index}", {"id": str(index)}, now)
    started = time.perf_counter()
    for index in range(lookups):
        cache.get(f"phase-synthetic/tool-{index % size}", time.monotonic())
    elapsed_ms = (time.perf_counter() - started) * 1000
    return {
        "tools": size,
        "lookups": lookups,
        "elapsed_ms": round(elapsed_ms, 3),
        "lookups_per_second": round(lookups / (elapsed_ms / 1000), 2) if elapsed_ms else 0,
        "entries": len(cache.items),
    }


def main() -> int:
    results = [benchmark(size) for size in (304, 1000, 5000, 10000)]
    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
