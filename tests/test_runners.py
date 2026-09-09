from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]

class RunnerTests(unittest.TestCase):
    def test_every_skill_has_runner_contract(self):
        folders = sorted(path for path in (ROOT / "skills").iterdir() if path.is_dir())
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
                contract = json.loads(schema.read_text(encoding="utf-8"))
                self.assertEqual(contract["title"], "Resultado de ejecución de habilidad")

    def test_runner_reports_missing_input(self):
        runner = next((ROOT / "skills").glob("*/run.py"))
        result = subprocess.run([sys.executable, str(runner)], input=json.dumps({"objective": "x"}), text=True, capture_output=True)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(json.loads(result.stdout)["status"], "needs_input")

if __name__ == "__main__":
    unittest.main()
