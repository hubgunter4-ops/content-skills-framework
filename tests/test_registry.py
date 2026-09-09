from pathlib import Path
import unittest

from toolkit.registry import PHASE_CATALOGS, load_registry

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_COUNTS = {
    "phase-1-content-toolkit": 52,
    "phase-2-datos": 57,
    "phase-3-programming": 89,
    "phase-4-automatizacion": 23,
    "phase-5-negocios": 34,
    "phase-6-medios": 49,
}


class RegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = load_registry(ROOT)

    def test_registry_contains_304_tools(self):
        self.assertEqual(len(self.registry), 304)

    def test_phase_counts(self):
        counts = {phase: sum(spec.phase == phase for spec in self.registry) for phase in EXPECTED_COUNTS}
        self.assertEqual(counts, EXPECTED_COUNTS)

    def test_every_tool_has_runner_skill_document_engine_and_catalog(self):
        for spec in self.registry:
            with self.subTest(identifier=spec.identifier):
                self.assertTrue(spec.runner.is_file(), f"runner ausente: {spec.runner}")
                self.assertEqual(spec.runner.suffix, ".py")
                self.assertIsNotNone(spec.skill_doc)
                self.assertTrue(spec.skill_doc.is_file(), f"SKILL.md ausente: {spec.skill_doc}")
                self.assertTrue(spec.engine, f"motor ausente: {spec.identifier}")
                if spec.phase == "phase-1-content-toolkit":
                    self.assertEqual(spec.engine, "skill_engine")
                    self.assertIsNone(spec.catalog)
                else:
                    self.assertIn(spec.phase, PHASE_CATALOGS)
                    self.assertTrue(spec.catalog.is_file(), f"catálogo ausente: {spec.catalog}")

    def test_identifiers_are_qualified_and_unique(self):
        identifiers = [spec.identifier for spec in self.registry]
        self.assertEqual(len(identifiers), len(set(identifiers)))
        self.assertTrue(all("/" in identifier for identifier in identifiers))


if __name__ == "__main__":
    unittest.main()
