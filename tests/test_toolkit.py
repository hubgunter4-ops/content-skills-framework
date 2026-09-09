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

    def test_list_contains_all_phases_and_304_entries(self):
        result = self.run_cli("list")
        self.assertEqual(result.returncode, 0, result.stderr)
        lines = [line for line in result.stdout.splitlines() if line.strip()]
        self.assertEqual(len(lines), 304)
        for phase in ("phase-1-content-toolkit", "phase-2-datos", "phase-3-programming", "phase-4-automatizacion", "phase-5-negocios", "phase-6-medios"):
            self.assertTrue(any(line.startswith(phase + "/") for line in lines), phase)

    def test_show_accepts_qualified_phase_two_slug(self):
        result = self.run_cli("show", "phase-2-datos/validacion-de-datos")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("name: validacion-de-datos", result.stdout)
        self.assertIn("toolkit/phase-2-datos/validacion-de-datos/run.py", result.stdout)

    def test_run_accepts_qualified_phase_two_slug(self):
        input_file = ROOT / "toolkit/phase-2-datos/validacion-de-datos/input.example.json"
        result = self.run_cli("run", "phase-2-datos/validacion-de-datos", "-i", str(input_file))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('"status": "ready"', result.stdout)

    def test_ambiguous_short_slug_requires_phase(self):
        result = self.run_cli("show", "investigacion-de-videos-de-youtube")
        self.assertEqual(result.returncode, 2)
        self.assertIn("Slug ambiguo", result.stdout)
        self.assertIn("phase-2-datos/investigacion-de-videos-de-youtube", result.stdout)

    def test_cli_preserves_phase_one_compatibility(self):
        result = self.run_cli("show", "academic-writing-pro")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("name: academic-writing-pro", result.stdout)

    def test_validate_does_not_load_integrations(self):
        result = self.run_cli("validate")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn("Integración solicitada", result.stdout)

    def test_integrations_lists_optional_services_without_loading_them(self):
        result = self.run_cli("integrations")
        self.assertEqual(result.returncode, 0)
        self.assertIn("youtube\tYouTube Data API v3", result.stdout)
        self.assertIn("SERP_API_KEY", result.stdout)
        self.assertIn("OPENAI_API_KEY", result.stdout)

    def test_skill_does_not_load_integration_without_explicit_request(self):
        result = self.run_cli("run", "phase-1-content-toolkit/investigacion-de-videos-de-youtube", "-i", str(ROOT / "toolkit/phase-1-content-toolkit/investigacion-de-videos-de-youtube/input.example.json"))
        self.assertEqual(result.returncode, 0)
        self.assertNotIn("Integración solicitada", result.stdout)

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
