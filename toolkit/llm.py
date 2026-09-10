"""Optional OpenAI-compatible LLM adapter for structured tool decisions."""
from __future__ import annotations

from dataclasses import dataclass
import json
import os
from typing import Any, Mapping, Sequence
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .errors import ProviderUnavailableError
from .models import LLMProviderConfig, NormalizedRequest, ToolCandidate, ToolSelection


@dataclass(frozen=True)
class LLMCallStats:
    provider: str
    model: str
    latency_ms: float
    prompt_tokens: int | None = None
    completion_tokens: int | None = None


TOOL_SELECTION_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "selected_tool": {"type": ["string", "null"]},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "reason": {"type": "array", "items": {"type": "string"}},
        "alternatives": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "tool_id": {"type": "string"},
                    "score": {"type": "number", "minimum": 0, "maximum": 1},
                    "reason": {"type": "array", "items": {"type": "string"}},
                    "rejected_reason": {"type": ["string", "null"]},
                },
                "required": ["tool_id", "score", "reason", "rejected_reason"],
                "additionalProperties": False,
            },
        },
        "requires_confirmation": {"type": "boolean"},
    },
    "required": ["selected_tool", "confidence", "reason", "alternatives", "requires_confirmation"],
    "additionalProperties": False,
}


class StructuredLLMProvider:
    """Call an OpenAI-compatible endpoint and return a validated ToolSelection."""

    def __init__(self, config: LLMProviderConfig, *, opener=urlopen) -> None:
        self.config = config
        self._opener = opener
        self.last_stats: LLMCallStats | None = None

    def decide(self, request: NormalizedRequest, candidates: Sequence[ToolCandidate]) -> ToolSelection:
        if self.config.mode == "off":
            raise ProviderUnavailableError("El proveedor LLM está deshabilitado")
        api_key = os.environ.get(self.config.api_key_env)
        if not api_key:
            raise ProviderUnavailableError(f"Falta la credencial en {self.config.api_key_env}")
        payload = self._payload(request, candidates)
        response = self._post(payload, api_key)
        selection = self._parse_selection(response, {candidate.tool_id for candidate in candidates})
        return selection

    def _payload(self, request: NormalizedRequest, candidates: Sequence[ToolCandidate]) -> dict[str, Any]:
        candidate_text = [candidate.to_dict() for candidate in candidates]
        return {
            "model": self.config.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Selecciona una herramienta del catálogo para la petición. "
                        "Devuelve únicamente JSON conforme al esquema. No inventes tool_id. "
                        "Si la decisión es ambigua, requires_confirmation debe ser true."
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps({
                        "request": request.to_dict(),
                        "candidates": candidate_text,
                    }, ensure_ascii=False),
                },
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "tool_selection",
                    "strict": True,
                    "schema": TOOL_SELECTION_SCHEMA,
                },
            },
        }

    def _post(self, payload: Mapping[str, Any], api_key: str) -> dict[str, Any]:
        import time

        url = self.config.base_url.rstrip("/") + "/chat/completions"
        request = Request(
            url,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "User-Agent": "content-skills-framework/0.2",
            },
            method="POST",
        )
        started = time.perf_counter()
        try:
            with self._opener(request, timeout=self.config.timeout_seconds) as response:
                raw = response.read()
            value = json.loads(raw.decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
            raise ProviderUnavailableError(f"No se pudo consultar el proveedor LLM: {type(exc).__name__}") from exc
        self.last_stats = LLMCallStats(
            provider=self.config.provider,
            model=self.config.model,
            latency_ms=round((time.perf_counter() - started) * 1000, 2),
            prompt_tokens=value.get("usage", {}).get("prompt_tokens"),
            completion_tokens=value.get("usage", {}).get("completion_tokens"),
        )
        if not isinstance(value, dict):
            raise ProviderUnavailableError("La respuesta del proveedor no es un objeto JSON")
        return value

    @staticmethod
    def _parse_selection(response: Mapping[str, Any], candidate_ids: set[str]) -> ToolSelection:
        try:
            content = response["choices"][0]["message"]["content"]
            value = json.loads(content) if isinstance(content, str) else content
            selected = value.get("selected_tool")
            if selected is not None and selected not in candidate_ids:
                raise ValueError("El LLM devolvió una herramienta que no estaba entre las candidatas")
            alternatives = tuple(
                ToolCandidate(
                    tool_id=str(item["tool_id"]),
                    score=float(item["score"]),
                    reason=tuple(str(reason) for reason in item.get("reason", [])),
                    rejected_reason=item.get("rejected_reason"),
                )
                for item in value.get("alternatives", [])
                if str(item["tool_id"]) in candidate_ids
            )
            return ToolSelection(
                selected_tool=selected,
                confidence=float(value["confidence"]),
                reason=tuple(str(reason) for reason in value.get("reason", [])),
                alternatives=alternatives,
                requires_confirmation=bool(value["requires_confirmation"]),
                selector="llm",
            )
        except (KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise ProviderUnavailableError(f"Respuesta estructurada inválida del proveedor LLM: {type(exc).__name__}") from exc


__all__ = ["LLMCallStats", "StructuredLLMProvider", "TOOL_SELECTION_SCHEMA"]
