from __future__ import annotations

from pathlib import Path
import json
import os
import tempfile
import unittest
from unittest.mock import patch

from toolkit import (
    DeterministicRouter,
    LLMProviderConfig,
    ProviderUnavailableError,
    StructuredLLMProvider,
    ToolCache,
    ToolCandidate,
    ToolSelection,
)

ROOT = Path(__file__).resolve().parents[1]


class FakeResponse:
    def __init__(self, value):
        self.value = value

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return json.dumps(self.value).encode("utf-8")


class FakeProvider:
    class Config:
        mode = "suggest"

    config = Config()

    def __init__(self, selection):
        self.selection = selection
        self.calls = 0

    def decide(self, request, candidates):
        self.calls += 1
        return self.selection


class LLMTests(unittest.TestCase):
    def config(self):
        return LLMProviderConfig(
            provider="test",
            model="test-model",
            base_url="https://llm.example.invalid/v1",
            api_key_env="FRAMEWORK_TEST_LLM_KEY",
            mode="suggest",
            timeout_seconds=2,
        )

    def test_provider_uses_structured_output_and_does_not_log_secret(self):
        response = {
            "choices": [{"message": {"content": json.dumps({
                "selected_tool": "phase-2-datos/validacion-de-datos",
                "confidence": 0.91,
                "reason": ["CSV", "validación"],
                "alternatives": [],
                "requires_confirmation": False,
            })}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5},
        }
        requests = []

        def opener(request, timeout):
            requests.append((request, timeout))
            return FakeResponse(response)

        provider = StructuredLLMProvider(self.config(), opener=opener)
        candidate = ToolCandidate("phase-2-datos/validacion-de-datos", 0.8, ("candidate",))
        with patch.dict(os.environ, {"FRAMEWORK_TEST_LLM_KEY": "secret-value"}):
            selection = provider.decide(
                __import__("toolkit").NormalizedRequest(
                    original_text="Valida CSV", objective="Validar", audience="equipo", content="a,b", format="markdown"
                ),
                [candidate],
            )
        self.assertEqual(selection.selector, "llm")
        self.assertEqual(selection.selected_tool, candidate.tool_id)
        body = requests[0][0].data.decode("utf-8")
        self.assertNotIn("secret-value", body)
        self.assertEqual(provider.last_stats.prompt_tokens, 10)

    def test_provider_rejects_tool_not_in_candidate_set(self):
        response = {"choices": [{"message": {"content": json.dumps({
            "selected_tool": "invented/tool",
            "confidence": 1,
            "reason": [],
            "alternatives": [],
            "requires_confirmation": False,
        })}}]}
        provider = StructuredLLMProvider(self.config(), opener=lambda request, timeout: FakeResponse(response))
        candidate = ToolCandidate("phase-2-datos/validacion-de-datos", 0.8)
        with patch.dict(os.environ, {"FRAMEWORK_TEST_LLM_KEY": "secret"}):
            with self.assertRaises(ProviderUnavailableError):
                provider.decide(
                    __import__("toolkit").NormalizedRequest(
                        original_text="Valida", objective="Validar", audience="equipo", content="datos", format="markdown"
                    ),
                    [candidate],
                )

    def test_missing_key_is_explicit_and_does_not_call_network(self):
        provider = StructuredLLMProvider(self.config(), opener=lambda request, timeout: self.fail("network call"))
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ProviderUnavailableError):
                provider.decide(
                    __import__("toolkit").NormalizedRequest(
                        original_text="Valida", objective="Validar", audience="equipo", content="datos", format="markdown"
                    ),
                    [],
                )

    def test_router_uses_llm_selection_when_provider_is_available(self):
        selection = ToolSelection(
            selected_tool="phase-2-datos/validacion-de-datos",
            confidence=0.95,
            reason=("LLM estructuró la intención",),
            requires_confirmation=False,
            selector="llm",
        )
        provider = FakeProvider(selection)
        with tempfile.TemporaryDirectory() as directory:
            router = DeterministicRouter(ROOT, ToolCache(ROOT, Path(directory) / "index.sqlite3"), provider)  # type: ignore[arg-type]
            decision = router.route("Valida este CSV")
        self.assertEqual(decision.selection.selector, "llm")
        self.assertEqual(provider.calls, 1)
        self.assertIsNotNone(decision.plan)

    def test_router_falls_back_when_llm_provider_is_unavailable(self):
        class FailingProvider(FakeProvider):
            def decide(self, request, candidates):
                self.calls += 1
                raise ProviderUnavailableError("offline")

        provider = FailingProvider(None)
        with tempfile.TemporaryDirectory() as directory:
            router = DeterministicRouter(ROOT, ToolCache(ROOT, Path(directory) / "index.sqlite3"), provider)  # type: ignore[arg-type]
            decision = router.route("Valida este CSV")
        self.assertEqual(decision.selection.selector, "deterministic")
        self.assertEqual(provider.calls, 1)


if __name__ == "__main__":
    unittest.main()
