"""Deterministic request normalization and tool routing."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any, Mapping

from .cache import ToolCache
from .models import ExecutionPlan, ExecutionStep, NormalizedRequest, ToolCandidate, ToolSelection
from .phases import tools_for_phase

_TOKEN_RE = re.compile(r"[\wáéíóúüñ-]+", re.IGNORECASE)


@dataclass(frozen=True)
class RouteDecision:
    request: NormalizedRequest
    selection: ToolSelection
    plan: ExecutionPlan | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "request": self.request.to_dict(),
            "selection": self.selection.to_dict(),
            "plan": self.plan.to_dict() if self.plan else None,
        }


class RequestNormalizer:
    """Normalize UI/CLI mappings without using a model or external service."""

    def normalize(self, value: Mapping[str, Any] | str) -> NormalizedRequest:
        if isinstance(value, str):
            value = {"original_text": value}
        if not isinstance(value, Mapping):
            raise ValueError("La petición debe ser texto u objeto JSON")
        original = str(value.get("original_text") or value.get("objective") or value.get("content") or "").strip()
        if not original:
            raise ValueError("La petición requiere original_text, objective o content")
        objective = str(value.get("objective") or original).strip()
        content = str(value.get("content") or original).strip()
        audience = str(value.get("audience") or "usuario").strip()
        output_format = str(value.get("format") or value.get("output_format") or "markdown").strip().lower()
        input_kind = str(value.get("input_kind") or self._infer_input_kind(value, content)).strip().lower()
        constraints = dict(value.get("constraints") or {})
        for key in ("no_network", "no_file_write", "requires_confirmation"):
            if key in value:
                constraints[key] = bool(value[key])
        tags = frozenset(str(item).strip().lower() for item in (value.get("tags") or ()) if str(item).strip())
        selected = value.get("tool_id") or value.get("user_selected_tool")
        return NormalizedRequest(
            original_text=original,
            objective=objective,
            audience=audience,
            content=content,
            format=output_format,
            language=str(value.get("language") or "es"),
            input_kind=input_kind,
            constraints=constraints,
            tags=tags,
            user_selected_tool=str(selected) if selected else None,
        )

    @staticmethod
    def _infer_input_kind(value: Mapping[str, Any], content: str) -> str:
        file_name = str(value.get("file_name") or value.get("filename") or "").lower()
        if file_name.endswith(".csv") or ".csv" in content.lower():
            return "csv"
        if file_name.endswith((".json", ".jsonl")):
            return "json"
        if file_name.endswith((".md", ".markdown")):
            return "markdown"
        if file_name.endswith((".png", ".jpg", ".jpeg", ".webp")):
            return "image"
        if file_name.endswith((".mp3", ".wav", ".mp4", ".webm")):
            return "audio_video"
        return "text"


class DeterministicRouter:
    """Rank indexed tools using metadata terms and explicit constraints."""

    def __init__(self, root: Path, cache: ToolCache) -> None:
        self.root = root
        self.cache = cache
        self.normalizer = RequestNormalizer()

    def route(self, value: Mapping[str, Any] | str, *, phase: str | None = None, alternative_limit: int = 3) -> RouteDecision:
        request = self.normalizer.normalize(value)
        if request.user_selected_tool:
            record = self.cache.resolve(request.user_selected_tool)
            if record is None or (phase and record.phase != phase):
                selection = ToolSelection(
                    selected_tool=None,
                    confidence=0.0,
                    reason=("La herramienta seleccionada no está disponible en el registro o fase solicitada",),
                    requires_confirmation=True,
                    selector="manual-validation",
                )
                return RouteDecision(request, selection, None)
            selection = ToolSelection(
                selected_tool=record.tool_id,
                confidence=1.0,
                reason=("Herramienta seleccionada explícitamente por el usuario",),
                requires_confirmation=False,
                selector="manual",
            )
            return RouteDecision(request, selection, ExecutionPlan((ExecutionStep(1, record.tool_id),)))

        records = [record for record in self._records(phase) if record.status == "available"]
        candidates = sorted((self._score(record, request) for record in records), key=lambda candidate: (-candidate.score, candidate.tool_id))
        if not candidates or candidates[0].score < 0.10:
            selection = ToolSelection(
                selected_tool=None,
                confidence=candidates[0].score if candidates else 0.0,
                reason=("No hay coincidencia suficiente; se requiere más información",),
                alternatives=tuple(candidates[:alternative_limit]),
                requires_confirmation=True,
                selector="deterministic",
            )
            return RouteDecision(request, selection, None)
        best = candidates[0]
        ambiguous = len(candidates) > 1 and best.score - candidates[1].score < 0.08
        selection = ToolSelection(
            selected_tool=best.tool_id,
            confidence=best.score,
            reason=best.reason,
            alternatives=tuple(candidates[1:alternative_limit]),
            requires_confirmation=ambiguous or bool(request.constraints.get("requires_confirmation")),
            selector="deterministic",
        )
        plan = None if selection.requires_confirmation else ExecutionPlan((ExecutionStep(1, best.tool_id),))
        return RouteDecision(request, selection, plan)

    def _records(self, phase: str | None):
        self.cache.refresh()
        if phase is None:
            from .persistent_index import list_index
            return list_index(self.cache.index_path)
        return [self.cache.resolve(spec.identifier) for spec in tools_for_phase(self.root, phase)]

    def _score(self, record, request: NormalizedRequest) -> ToolCandidate:
        query_tokens = set(_TOKEN_RE.findall(" ".join((request.original_text, request.objective, *request.tags)).lower()))
        metadata_text = " ".join((record.tool_id, record.name, record.description, *record.tags)).lower()
        metadata_tokens = set(_TOKEN_RE.findall(metadata_text))
        overlap = query_tokens & metadata_tokens
        score = min(0.92, 0.12 + 0.10 * len(overlap))
        reasons = []
        if overlap:
            reasons.append("Coincidencia de intención y metadatos: " + ", ".join(sorted(overlap)[:5]))
        if request.input_kind in record.input_kinds:
            score += 0.18
            reasons.append(f"Entrada {request.input_kind} compatible")
        if request.format in record.output_formats:
            score += 0.15
            reasons.append(f"Salida {request.format} compatible")
        if record.phase in request.tags:
            score += 0.10
            reasons.append(f"Fase solicitada: {record.phase}")
        if not reasons:
            reasons.append("Coincidencia de catálogo de baja especificidad")
        return ToolCandidate(tool_id=record.tool_id, score=min(score, 1.0), reason=tuple(reasons))


__all__ = ["DeterministicRouter", "RequestNormalizer", "RouteDecision"]
