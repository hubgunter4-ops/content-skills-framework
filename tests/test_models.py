from __future__ import annotations

import unittest

from toolkit import (
    CONTRACT_VERSION,
    Capability,
    ContractError,
    ExecutionPlan,
    ExecutionRequest,
    ExecutionResult,
    ExecutionStep,
    LLMProviderConfig,
    NormalizedRequest,
    Status,
    ToolCandidate,
    ToolMetadata,
    ToolSelection,
    load_schema,
    validate_metadata_dict,
    validate_result_dict,
    validate_schema_documents,
)


class PublicModelTests(unittest.TestCase):
    def test_tool_metadata_serializes_with_script_and_capabilities(self):
        metadata = ToolMetadata(
            id="phase-2-datos/validacion-de-datos",
            version="1.0.0",
            name="Validación de datos",
            description="Controles de calidad para datos.",
            input_schema="schemas/input.schema.json",
            output_schema="schemas/output.schema.json",
            phase="phase-2-datos",
            script="toolkit/phase-2-datos/validacion-de-datos/run.py",
            capabilities=frozenset({Capability.FILESYSTEM_READ}),
            input_kinds=frozenset({"csv", "table"}),
            output_formats=frozenset({"markdown", "json"}),
            tags=frozenset({"validacion", "datos"}),
        )
        value = metadata.to_dict()
        self.assertEqual(value["contract_version"], CONTRACT_VERSION)
        self.assertEqual(value["capabilities"], [Capability.FILESYSTEM_READ])
        self.assertEqual(validate_metadata_dict(value)["id"], metadata.id)

    def test_metadata_requires_execution_reference(self):
        with self.assertRaises(ValueError):
            ToolMetadata(
                id="x/tool",
                version="1.0.0",
                name="Tool",
                description="Description",
                input_schema="input.json",
                output_schema="output.json",
            )

    def test_execution_request_rejects_non_object_payload(self):
        with self.assertRaises(ValueError):
            ExecutionRequest(payload=[], request_id="r-1", tool_id="x/tool")  # type: ignore[arg-type]

    def test_normalized_request_and_selection_are_serializable(self):
        request = NormalizedRequest(
            original_text="Valida este CSV.",
            objective="Validar CSV",
            audience="Analistas",
            content="a,b\n1,2",
            format="markdown",
            input_kind="csv",
            tags=frozenset({"validacion", "datos"}),
        )
        candidate = ToolCandidate(
            tool_id="phase-2-datos/validacion-de-datos",
            score=0.94,
            reason=("Detectó CSV", "Solicita validación"),
        )
        selection = ToolSelection(
            selected_tool=candidate.tool_id,
            confidence=candidate.score,
            reason=candidate.reason,
            alternatives=(candidate,),
        )
        self.assertEqual(request.to_dict()["input_kind"], "csv")
        self.assertEqual(selection.to_dict()["alternatives"][0]["score"], 0.94)

    def test_ambiguous_selection_requires_confirmation(self):
        selection = ToolSelection(
            selected_tool=None,
            confidence=0.41,
            reason=("Hay dos herramientas compatibles",),
            requires_confirmation=True,
        )
        self.assertTrue(selection.to_dict()["requires_confirmation"])

    def test_execution_plan_requires_consecutive_steps(self):
        plan = ExecutionPlan(
            steps=(
                ExecutionStep(1, "phase-2-datos/extractor-de-datos-de-documentos"),
                ExecutionStep(2, "phase-2-datos/validacion-de-datos", "step_1.output"),
            ),
            requires_confirmation=True,
        )
        self.assertEqual(plan.to_dict()["steps"][1]["input_from"], "step_1.output")
        with self.assertRaises(ValueError):
            ExecutionPlan(steps=(ExecutionStep(2, "x/tool"),))

    def test_result_states_and_schema_validation(self):
        result = ExecutionResult(
            status=Status.READY,
            analysis={"words": 10},
            deliverable={"format": "markdown"},
            warnings=("Revisión humana recomendada",),
            provenance={"external_calls": []},
        )
        value = validate_result_dict(result.to_dict())
        self.assertEqual(value["schema_version"], CONTRACT_VERSION)
        self.assertEqual(value["status"], Status.READY)

    def test_unknown_result_status_is_rejected(self):
        with self.assertRaises(ContractError):
            validate_result_dict({
                "status": "unknown",
                "analysis": {},
                "deliverable": {},
                "warnings": [],
                "provenance": {},
            })

    def test_llm_config_has_explicit_mode_and_secret_reference(self):
        config = LLMProviderConfig(
            provider="openai-compatible",
            model="gpt-5-mini",
            base_url="https://example.invalid/v1",
            api_key_env="FRAMEWORK_LLM_API_KEY",
            mode="suggest",
        )
        value = config.to_dict()
        self.assertEqual(value["mode"], "suggest")
        self.assertEqual(value["api_key_env"], "FRAMEWORK_LLM_API_KEY")
        self.assertNotIn("api_key", value)

    def test_all_phase1_schemas_are_present_and_2020_12(self):
        self.assertEqual(validate_schema_documents(), [])
        self.assertEqual(load_schema("execution-result.schema.json")["title"], "ExecutionResult")


if __name__ == "__main__":
    unittest.main()
