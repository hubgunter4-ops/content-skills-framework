from __future__ import annotations

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from toolkit import (
    ENTRY_POINT_GROUP,
    discover_external_entry_points,
    ensure_index,
    index_is_current,
    list_index,
    lookup,
    rebuild_index,
)

ROOT = Path(__file__).resolve().parents[1]


class FakeDistribution:
    version = "2.4.1"
    metadata = {"Name": "content-skills-example"}

    def locate_file(self, value: str) -> Path:
        return Path("/tmp/content-skills-example")


class FakeEntryPoint:
    name = "phase-7-example/lectura"
    value = "example_plugin:factory"
    dist = FakeDistribution()


class FakeEntryPoints:
    def select(self, *, group: str):
        self.group = group
        return [FakeEntryPoint()] if group == ENTRY_POINT_GROUP else []


class PersistentIndexTests(unittest.TestCase):
    def test_rebuild_indexes_builtin_catalog_without_loading_runners(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "registry.sqlite3"
            count = rebuild_index(ROOT, path)
            self.assertGreaterEqual(count, 304)
            records = list_index(path)
            builtins = [record for record in records if record.distribution == "content-skills-framework-builtin"]
            self.assertEqual(len(builtins), 304)
            record = lookup(path, "phase-2-datos/validacion-de-datos")
            self.assertIsNotNone(record)
            assert record is not None
            self.assertEqual(record.status, "available")
            self.assertTrue(record.script.endswith("/run.py"))
            self.assertEqual(record.to_metadata().id, record.tool_id)

    def test_index_is_current_and_ensure_rebuilds_only_when_needed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "registry.sqlite3"
            self.assertFalse(index_is_current(ROOT, path))
            _, rebuilt = ensure_index(ROOT, path)
            self.assertTrue(rebuilt)
            self.assertTrue(index_is_current(ROOT, path))
            _, rebuilt_again = ensure_index(ROOT, path)
            self.assertFalse(rebuilt_again)

    def test_phase_filter_and_unknown_lookup(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "registry.sqlite3"
            rebuild_index(ROOT, path)
            phase_records = list_index(path, phase="phase-2-datos")
            self.assertEqual(len(phase_records), 57)
            self.assertIsNone(lookup(path, "does-not-exist"))

    def test_entry_point_discovery_reads_declarations_without_loading_objects(self):
        with patch("toolkit.persistent_index.importlib_metadata.entry_points", return_value=FakeEntryPoints()):
            entries = discover_external_entry_points()
        self.assertEqual(entries[0]["name"], "phase-7-example/lectura")
        self.assertEqual(entries[0]["value"], "example_plugin:factory")
        self.assertEqual(entries[0]["distribution"], "content-skills-example")

    def test_external_entry_point_is_indexed_as_discovered_until_metadata_is_loaded(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "registry.sqlite3"
            with patch("toolkit.persistent_index.importlib_metadata.entry_points", return_value=FakeEntryPoints()):
                rebuild_index(ROOT, path)
            record = lookup(path, "phase-7-example/lectura")
            self.assertIsNotNone(record)
            assert record is not None
            self.assertEqual(record.status, "discovered")
            self.assertEqual(record.object_ref, "example_plugin:factory")
            with self.assertRaises(ValueError):
                record.to_metadata()


if __name__ == "__main__":
    unittest.main()
