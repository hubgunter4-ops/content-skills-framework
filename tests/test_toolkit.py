from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]

class ToolkitTests(unittest.TestCase):
    def run_cli(self, *args, input_text=None):
        return subprocess.run([sys.executable, "-m", "toolkit", *args], cwd=ROOT, text=True, input=input_text, capture_output=True)

    def test_catalog_validates(self):
        result = self.run_cli("validate")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("habilidades", result.stdout)

    def test_list_contains_known_skill(self):
        result = self.run_cli("list")
        self.assertEqual(result.returncode, 0)
        self.assertIn("investigacion-de-videos-de-youtube", result.stdout)

    def test_invalid_show_is_visible(self):
        result = self.run_cli("show", "no-existe")
        self.assertEqual(result.returncode, 2)
        self.assertIn("No existe", result.stdout)

    def test_menu_invalid_then_cancel(self):
        result = self.run_cli(input_text="x\nq\n")
        self.assertEqual(result.returncode, 0)
        self.assertIn("Opción no válida", result.stdout)
        self.assertIn("Cancelado", result.stdout)

    def test_menu_eof(self):
        result = self.run_cli(input_text="")
        self.assertEqual(result.returncode, 0)
        self.assertIn("Cancelado", result.stdout)

if __name__ == "__main__":
    unittest.main()
