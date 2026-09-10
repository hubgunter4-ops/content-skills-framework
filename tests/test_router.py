from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from toolkit import (
    DeterministicRouter,
    RequestNormalizer,
    ToolCache,
    get_phase,
    list_phases,
    tools_for_phase,
)

ROOT = Path(__file__).resolve().parents[1]


class RouterTests(unittest.TestCase):
    def make_router(self, directory: str) -> DeterministicRouter:
        cache = ToolCache(ROOT, Path(directory) / "index.sqlite3")
        return DeterministicRouter(ROOT, cache)

    def test_phase_descriptors_and_filter_are_modular(self):
        phases = list_phases()
        self.assertEqual(len(phases), 6)
        self.assertEqual(get_phase("phase-2-datos").resource_profile.memory_mb, 1024)
        self.assertEqual(len(tools_for_phase(ROOT, "phase-2-datos")), 57)
        with self.assertRaises(KeyError):
            get_phase("phase-unknown")

    def test_normalizer_infers_csv_and_preserves_constraints(self):
        request = RequestNormalizer().normalize({
            "objective": "Valida este CSV",
            "audience": "Analistas",
            "file_name": "dataset.csv",
            "format": "Markdown",
            "no_network": True,
            "tags": ["datos"],
        })
        self.assertEqual(request.input_kind, "csv")
        self.assertEqual(request.format, "markdown")
        self.assertTrue(request.constraints["no_network"])
        self.assertIn("datos", request.tags)

    def test_manual_tool_selection_creates_execution_plan(self):
        with tempfile.TemporaryDirectory() as directory:
            decision = self.make_router(directory).route({
                "objective": "Validar datos",
                "tool_id": "phase-2-datos/validacion-de-datos",
            })
        self.assertEqual(decision.selection.selector, "manual")
        self.assertFalse(decision.selection.requires_confirmation)
        self.assertIsNotNone(decision.plan)
        assert decision.plan is not None
        self.assertEqual(decision.plan.steps[0].tool_id, "phase-2-datos/validacion-de-datos")

    def test_invalid_manual_tool_requires_confirmation_and_does_not_plan(self):
        with tempfile.TemporaryDirectory() as directory:
            decision = self.make_router(directory).route({
                "objective": "Ejecutar algo",
                "tool_id": "phase-9-no-existe/tool",
            })
        self.assertTrue(decision.selection.requires_confirmation)
        self.assertIsNone(decision.plan)

    def test_deterministic_route_returns_explanation_and_plan_or_confirmation(self):
        with tempfile.TemporaryDirectory() as directory:
            decision = self.make_router(directory).route(
                "Convierte este documento Markdown a HTML para el equipo editorial"
            )
        self.assertEqual(decision.selection.selector, "deterministic")
        self.assertTrue(decision.selection.reason)
        self.assertIsNotNone(decision.selection.selected_tool)
        self.assertTrue(decision.selection.alternatives or decision.plan)
        self.assertIn("request", decision.to_dict())

    def test_phase_constraint_is_applied(self):
        with tempfile.TemporaryDirectory() as directory:
            decision = self.make_router(directory).route(
                "Analiza y valida los datos", phase="phase-2-datos"
            )
        if decision.selection.selected_tool:
            self.assertTrue(decision.selection.selected_tool.startswith("phase-2-datos/"))


if __name__ == "__main__":
    unittest.main()
