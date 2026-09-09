from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from toolkit.registry import load_registry

PHASE = 'phase-6-medios'
EXPECTED = 49
REQUIRED_SECTIONS = (
    "## Propósito",
    "## Runner asociado",
    "## Flujo de trabajo",
    "## Entradas aceptadas",
    "## Salida esperada",
    "## Guardrails",
    "## Plantilla de solicitud",
    "## Lista de control",
)


def frontmatter(text):
    match = re.match(r"\A---\n(.*?)\n---\n", text, re.DOTALL)
    if not match:
        return {}
    return dict(re.findall(r"^([A-Za-z][\w-]*):\s*(.*?)\s*$", match.group(1), re.MULTILINE))


def assert_documentation(testcase, spec):
    text = spec.skill_doc.read_text(encoding="utf-8")
    metadata = frontmatter(text)
    testcase.assertEqual(set(("name", "description")), set(metadata), spec.identifier)
    testcase.assertEqual(metadata["name"], spec.slug, spec.identifier)
    testcase.assertEqual(metadata["description"], spec.description, spec.identifier)
    testcase.assertEqual(len(re.findall(r"^# (?!#).+", text, re.MULTILINE)), 1, spec.identifier)
    for section in REQUIRED_SECTIONS:
        aliases = (section, "## Entradas" if section == "## Entradas aceptadas" else "## Salida" if section == "## Salida esperada" else section)
        testcase.assertTrue(any(alias in text for alias in aliases), f"{spec.identifier}: falta {section}")
    testcase.assertIn(f"toolkit/{spec.phase}/{spec.slug}/run.py", text)
    testcase.assertIn(f"toolkit/{spec.phase}/{spec.slug}/input.example.json", text)
    testcase.assertIn(f"toolkit/{spec.phase}/{spec.slug}/output.schema.json", text)
    testcase.assertIn(f"toolkit/{spec.phase}/{spec.slug}/tests/test_smoke.py", text)
    testcase.assertTrue((spec.folder / "resources" / "README.md").is_file(), spec.identifier)
    testcase.assertTrue((spec.folder / "tests" / "test_smoke.py").is_file(), spec.identifier)
    testcase.assertNotRegex(text, r"(?i)(?:api[_ -]?key|bearer\s+[A-Za-z0-9]|sk-[A-Za-z0-9]{10,}|password\s*[:=]|token\s*[:=])")
    testcase.assertNotRegex(text, r"(?i)(?:\b\d+(?:\.\d+)?\s*(?:estrellas|stars|descargas|downloads|usuarios|usos)\b|popularidad)")
    testcase.assertNotIn("skills/content-toolkit", text)


class DocumentationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tools = [s for s in load_registry(ROOT) if s.phase == PHASE]

    def test_phase_has_expected_tools(self):
        self.assertEqual(len(self.tools), EXPECTED)

    def test_every_document_matches_contract(self):
        for spec in self.tools:
            with self.subTest(identifier=spec.identifier):
                assert_documentation(self, spec)


if __name__ == "__main__":
    unittest.main()
