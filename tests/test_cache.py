from __future__ import annotations

from pathlib import Path
import tempfile
import time
import unittest

from toolkit import ToolCache

ROOT = Path(__file__).resolve().parents[1]


class CacheTests(unittest.TestCase):
    def make_cache(self, directory: str, **kwargs) -> ToolCache:
        return ToolCache(ROOT, Path(directory) / "index.sqlite3", **kwargs)

    def test_l1_resolution_and_l2_metadata_hits(self):
        with tempfile.TemporaryDirectory() as directory:
            cache = self.make_cache(directory)
            first = cache.resolve("phase-2-datos/validacion-de-datos")
            second = cache.resolve("phase-2-datos/validacion-de-datos")
            self.assertIsNotNone(first)
            self.assertIsNotNone(second)
            metadata_first = cache.metadata("phase-2-datos/validacion-de-datos")
            metadata_second = cache.metadata("phase-2-datos/validacion-de-datos")
            self.assertEqual(metadata_first.id, metadata_second.id)
            stats = cache.stats()
            self.assertGreaterEqual(stats.l1_hits, 1)
            self.assertGreaterEqual(stats.l2_hits, 1)
            self.assertGreater(stats.hit_rate, 0)

    def test_short_slug_requires_unambiguous_resolution(self):
        with tempfile.TemporaryDirectory() as directory:
            cache = self.make_cache(directory)
            record = cache.resolve("validacion-de-datos")
            self.assertIsNotNone(record)
            self.assertIsNone(cache.resolve("no-existe"))

    def test_schema_is_loaded_once_in_l2(self):
        with tempfile.TemporaryDirectory() as directory:
            cache = self.make_cache(directory)
            first = cache.schema("phase-2-datos/validacion-de-datos")
            second = cache.schema("phase-2-datos/validacion-de-datos")
            self.assertEqual(first, second)
            self.assertGreaterEqual(cache.stats().l2_hits, 1)

    def test_l3_loader_is_explicit_and_cached(self):
        with tempfile.TemporaryDirectory() as directory:
            cache = self.make_cache(directory)
            calls: list[str] = []

            def loader(record):
                calls.append(record.tool_id)
                return {"runner": record.script}

            first = cache.factory("phase-2-datos/validacion-de-datos", loader)
            second = cache.factory("phase-2-datos/validacion-de-datos", loader)
            self.assertEqual(first, second)
            self.assertEqual(calls, ["phase-2-datos/validacion-de-datos"])
            self.assertEqual(cache.stats().l3_hits, 1)

    def test_lru_eviction_is_counted(self):
        with tempfile.TemporaryDirectory() as directory:
            cache = self.make_cache(directory, l1_capacity=1, l2_capacity=1, l3_capacity=1)
            cache.resolve("phase-2-datos/validacion-de-datos")
            cache.resolve("phase-2-datos/agent-reach")
            self.assertGreaterEqual(cache.stats().evictions, 1)
            self.assertEqual(cache.stats().entries_l1, 1)

    def test_ttl_expiration_causes_miss(self):
        with tempfile.TemporaryDirectory() as directory:
            cache = self.make_cache(directory, ttl_seconds=0.01)
            cache.resolve("phase-2-datos/validacion-de-datos")
            time.sleep(0.03)
            cache.resolve("phase-2-datos/validacion-de-datos")
            self.assertGreaterEqual(cache.stats().l1_misses, 2)

    def test_manual_invalidation_clears_related_layers(self):
        with tempfile.TemporaryDirectory() as directory:
            cache = self.make_cache(directory)
            cache.metadata("phase-2-datos/validacion-de-datos")
            cache.schema("phase-2-datos/validacion-de-datos")
            cache.factory("phase-2-datos/validacion-de-datos", lambda record: record.script)
            cache.invalidate("phase-2-datos/validacion-de-datos")
            stats = cache.stats()
            self.assertEqual(stats.entries_l1, 0)
            self.assertEqual(stats.entries_l2, 0)
            self.assertEqual(stats.entries_l3, 0)
            self.assertGreaterEqual(stats.invalidations, 1)

    def test_metadata_digest_is_in_cache_key(self):
        with tempfile.TemporaryDirectory() as directory:
            cache = self.make_cache(directory)
            metadata = cache.metadata("phase-2-datos/validacion-de-datos")
            record = cache.resolve("phase-2-datos/validacion-de-datos")
            assert record is not None
            self.assertEqual(metadata.id, record.tool_id)
            self.assertTrue(record.metadata_digest)
            self.assertEqual(cache.stats().entries_l2, 1)

    def test_close_rejects_future_access(self):
        with tempfile.TemporaryDirectory() as directory:
            cache = self.make_cache(directory)
            cache.close()
            with self.assertRaises(RuntimeError):
                cache.resolve("phase-2-datos/validacion-de-datos")


if __name__ == "__main__":
    unittest.main()
