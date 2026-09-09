from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]


class RunnerTests(unittest.TestCase):
    def run_runner(self, slug, payload=None):
        folder = ROOT / "toolkit" / "phase-1-content-toolkit" / slug
        example = folder / "input.example.json"
        payload = payload or json.loads(example.read_text(encoding="utf-8"))
        return subprocess.run(
            [sys.executable, str(folder / "run.py")],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
        )

    def test_every_skill_has_runner_contract(self):
        folders = sorted(path for path in (ROOT / "toolkit" / "phase-1-content-toolkit").iterdir() if path.is_dir() and path.name != 'tests')
        self.assertEqual(len(folders), 52)
        for folder in folders:
            with self.subTest(skill=folder.name):
                runner = folder / "run.py"
                example = folder / "input.example.json"
                schema = folder / "output.schema.json"
                self.assertTrue(runner.is_file())
                self.assertTrue(example.is_file())
                self.assertTrue(schema.is_file())
                payload = json.loads(example.read_text(encoding="utf-8"))
                result = subprocess.run([sys.executable, str(runner)], input=json.dumps(payload), text=True, capture_output=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                output = json.loads(result.stdout)
                self.assertEqual(output["status"], "ready")
                self.assertEqual(output["skill"]["slug"], folder.name)
                self.assertEqual(output["analysis"]["assumptions"][-1], f"Se aplicó el adaptador funcional de {folder.name}.")
                contract = json.loads(schema.read_text(encoding="utf-8"))
                self.assertEqual(contract["title"], "Resultado de ejecución de habilidad")
                self.assertNotEqual(output["deliverable"]["content"], payload["content"])

    def test_runner_reports_missing_input(self):
        runner = next((ROOT / "toolkit" / "phase-1-content-toolkit").glob("*/run.py"))
        result = subprocess.run([sys.executable, str(runner)], input=json.dumps({"objective": "x"}), text=True, capture_output=True)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(json.loads(result.stdout)["status"], "needs_input")

    def test_markdown_runner_converts_to_html(self):
        result = self.run_runner("markdown-a-html", {
            "objective": "Documento",
            "audience": "Web",
            "content": "# Hola\n\n**Mundo**",
            "format": "html",
        })
        self.assertEqual(result.returncode, 0)
        content = json.loads(result.stdout)["deliverable"]["content"]
        self.assertIn("<h1>Hola</h1>", content)
        self.assertIn("<strong>Mundo</strong>", content)

    def test_keyword_runner_generates_structured_research(self):
        result = self.run_runner("investigacion-de-palabras-clave", {
            "objective": "Café orgánico",
            "audience": "SEO",
            "content": "café orgánico y café sostenible para consumidores",
            "format": "markdown",
        })
        self.assertEqual(result.returncode, 0)
        content = json.loads(result.stdout)["deliverable"]["content"]
        self.assertIn("Libro de investigación de palabras clave", content)
        self.assertIn("Pestañas propuestas", content)
        self.assertIn("Grupos de temas", content)

    def test_canvas_runner_returns_json_canvas(self):
        result = self.run_runner("creador-de-obsidian-canvas")
        self.assertEqual(result.returncode, 0)
        content = json.loads(result.stdout)["deliverable"]["content"]
        canvas = json.loads(content)
        self.assertIn("nodes", canvas)
        self.assertIn("edges", canvas)
        self.assertGreaterEqual(len(canvas["nodes"]), 2)

    def test_skill_adapters_produce_different_formats(self):
        payload = {
            "objective": "Prueba",
            "audience": "Equipo",
            "content": "# Texto de prueba",
            "format": "markdown",
        }
        html = json.loads(self.run_runner("markdown-a-html", payload).stdout)["deliverable"]["content"]
        typst = json.loads(self.run_runner("creador-de-pdf-typst", payload).stdout)["deliverable"]["content"]
        marp = json.loads(self.run_runner("generador-de-diapositivas-marp", payload).stdout)["deliverable"]["content"]
        self.assertIn("<html", html)
        self.assertIn("#set page", typst)
        self.assertIn("marp: true", marp)
        self.assertNotEqual(html, typst)
        self.assertNotEqual(typst, marp)


if __name__ == "__main__":
    unittest.main()
