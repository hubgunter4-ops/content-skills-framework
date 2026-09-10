"""Public data models for the Content Skills Framework runtime.

The models are deliberately dependency-free. They provide stable serialization
boundaries; runtime policy and execution are implemented in later phases.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


CONTRACT_VERSION = "1.0"


class Status:
    READY = "ready"
    NEEDS_INPUT = "needs_input"
    NOT_LOADED = "not_loaded"
    ERROR = "error"
    TIMEOUT = "timeout"
    QUOTA_EXCEEDED = "quota_exceeded"
    CIRCUIT_OPEN = "circuit_open"
    WORKER_CRASHED = "worker_crashed"

    ALL = frozenset({
        READY,
        NEEDS_INPUT,
        NOT_LOADED,
        ERROR,
        TIMEOUT,
        QUOTA_EXCEEDED,
        CIRCUIT_OPEN,
        WORKER_CRASHED,
    })


class Capability:
    FILESYSTEM_READ = "filesystem.read"
    FILESYSTEM_WRITE = "filesystem.write"
    NETWORK = "network"
    CREDENTIALS_READ = "credentials.read"
    PROCESS_SPAWN = "process.spawn"
    PUBLISH = "publish"
    DESTRUCTIVE_ACTION = "destructive_action"

    ALL = frozenset({
        FILESYSTEM_READ,
        FILESYSTEM_WRITE,
        NETWORK,
        CREDENTIALS_READ,
        PROCESS_SPAWN,
        PUBLISH,
        DESTRUCTIVE_ACTION,
    })


def _copy_mapping(value: Mapping[str, Any]) -> dict[str, Any]:
    return dict(value)


def _require_text(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} debe ser una cadena no vacía")
    return value.strip()


def _validate_capabilities(values: frozenset[str]) -> None:
    unknown = sorted(set(values) - Capability.ALL)
    if unknown:
        raise ValueError(f"Capacidades no registradas: {', '.join(unknown)}")


@dataclass(frozen=True)
class ToolMetadata:
    id: str
    version: str
    name: str
    description: str
    input_schema: str
    output_schema: str
    contract_version: str = CONTRACT_VERSION
    phase: str | None = None
    entrypoint: str | None = None
    script: str | None = None
    capabilities: frozenset[str] = field(default_factory=frozenset)
    input_kinds: frozenset[str] = field(default_factory=frozenset)
    output_formats: frozenset[str] = field(default_factory=frozenset)
    tags: frozenset[str] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        for name in ("id", "version", "name", "description", "input_schema", "output_schema", "contract_version"):
            _require_text(getattr(self, name), name)
        _validate_capabilities(self.capabilities)
        if self.phase is not None:
            _require_text(self.phase, "phase")
        if self.entrypoint is None and self.script is None:
            raise ValueError("ToolMetadata requiere entrypoint o script")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "version": self.version,
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
            "output_schema": self.output_schema,
            "contract_version": self.contract_version,
            "phase": self.phase,
            "entrypoint": self.entrypoint,
            "script": self.script,
            "capabilities": sorted(self.capabilities),
            "input_kinds": sorted(self.input_kinds),
            "output_formats": sorted(self.output_formats),
            "tags": sorted(self.tags),
        }


@dataclass(frozen=True)
class ExecutionRequest:
    payload: dict[str, Any]
    request_id: str
    tool_id: str
    contract_version: str = CONTRACT_VERSION
    workspace: str | None = None
    deadline_seconds: float | None = None
    allowed_capabilities: frozenset[str] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        _require_text(self.request_id, "request_id")
        _require_text(self.tool_id, "tool_id")
        if not isinstance(self.payload, dict):
            raise ValueError("payload debe ser un objeto JSON")
        if self.deadline_seconds is not None and self.deadline_seconds <= 0:
            raise ValueError("deadline_seconds debe ser mayor que cero")
        _validate_capabilities(self.allowed_capabilities)

    def to_dict(self) -> dict[str, Any]:
        return {
            "payload": _copy_mapping(self.payload),
            "request_id": self.request_id,
            "tool_id": self.tool_id,
            "contract_version": self.contract_version,
            "workspace": self.workspace,
            "deadline_seconds": self.deadline_seconds,
            "allowed_capabilities": sorted(self.allowed_capabilities),
        }


@dataclass(frozen=True)
class NormalizedRequest:
    original_text: str
    objective: str
    audience: str
    content: str
    format: str
    language: str = "es"
    input_kind: str = "text"
    constraints: dict[str, Any] = field(default_factory=dict)
    tags: frozenset[str] = field(default_factory=frozenset)
    user_selected_tool: str | None = None

    def __post_init__(self) -> None:
        for name in ("original_text", "objective", "audience", "content", "format", "language", "input_kind"):
            _require_text(getattr(self, name), name)
        if self.user_selected_tool is not None:
            _require_text(self.user_selected_tool, "user_selected_tool")

    def to_dict(self) -> dict[str, Any]:
        return {
            "original_text": self.original_text,
            "objective": self.objective,
            "audience": self.audience,
            "content": self.content,
            "format": self.format,
            "language": self.language,
            "input_kind": self.input_kind,
            "constraints": _copy_mapping(self.constraints),
            "tags": sorted(self.tags),
            "user_selected_tool": self.user_selected_tool,
        }


@dataclass(frozen=True)
class ToolCandidate:
    tool_id: str
    score: float
    reason: tuple[str, ...] = ()
    rejected_reason: str | None = None

    def __post_init__(self) -> None:
        _require_text(self.tool_id, "tool_id")
        if not 0 <= self.score <= 1:
            raise ValueError("score debe estar entre 0 y 1")

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool_id": self.tool_id,
            "score": self.score,
            "reason": list(self.reason),
            "rejected_reason": self.rejected_reason,
        }


@dataclass(frozen=True)
class ToolSelection:
    selected_tool: str | None
    confidence: float
    reason: tuple[str, ...] = ()
    alternatives: tuple[ToolCandidate, ...] = ()
    requires_confirmation: bool = False
    selector: str = "deterministic"

    def __post_init__(self) -> None:
        if self.selected_tool is not None:
            _require_text(self.selected_tool, "selected_tool")
        if not 0 <= self.confidence <= 1:
            raise ValueError("confidence debe estar entre 0 y 1")
        _require_text(self.selector, "selector")
        if self.selected_tool is None and not self.requires_confirmation:
            raise ValueError("Una selección sin herramienta requiere confirmación")

    def to_dict(self) -> dict[str, Any]:
        return {
            "selected_tool": self.selected_tool,
            "confidence": self.confidence,
            "reason": list(self.reason),
            "alternatives": [candidate.to_dict() for candidate in self.alternatives],
            "requires_confirmation": self.requires_confirmation,
            "selector": self.selector,
        }


@dataclass(frozen=True)
class ExecutionStep:
    order: int
    tool_id: str
    input_from: str = "request"

    def __post_init__(self) -> None:
        if self.order < 1:
            raise ValueError("order debe comenzar en 1")
        _require_text(self.tool_id, "tool_id")
        _require_text(self.input_from, "input_from")

    def to_dict(self) -> dict[str, Any]:
        return {"order": self.order, "tool_id": self.tool_id, "input_from": self.input_from}


@dataclass(frozen=True)
class ExecutionPlan:
    steps: tuple[ExecutionStep, ...]
    requires_confirmation: bool = False
    plan_id: str | None = None

    def __post_init__(self) -> None:
        if not self.steps:
            raise ValueError("ExecutionPlan requiere al menos un paso")
        expected = list(range(1, len(self.steps) + 1))
        actual = [step.order for step in self.steps]
        if actual != expected:
            raise ValueError("Los pasos deben tener órdenes consecutivos")

    def to_dict(self) -> dict[str, Any]:
        return {
            "steps": [step.to_dict() for step in self.steps],
            "requires_confirmation": self.requires_confirmation,
            "plan_id": self.plan_id,
        }


@dataclass(frozen=True)
class LLMProviderConfig:
    provider: str
    model: str
    base_url: str
    api_key_env: str
    mode: str = "suggest"
    timeout_seconds: float = 30.0
    max_input_tokens: int | None = None
    max_output_tokens: int | None = None
    data_policy: str = "no_payload_logging"

    def __post_init__(self) -> None:
        for name in ("provider", "model", "base_url", "api_key_env", "mode", "data_policy"):
            _require_text(getattr(self, name), name)
        if self.mode not in {"off", "suggest", "required"}:
            raise ValueError("mode debe ser off, suggest o required")
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds debe ser mayor que cero")
        for name in ("max_input_tokens", "max_output_tokens"):
            value = getattr(self, name)
            if value is not None and value <= 0:
                raise ValueError(f"{name} debe ser mayor que cero")

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "model": self.model,
            "base_url": self.base_url,
            "api_key_env": self.api_key_env,
            "mode": self.mode,
            "timeout_seconds": self.timeout_seconds,
            "max_input_tokens": self.max_input_tokens,
            "max_output_tokens": self.max_output_tokens,
            "data_policy": self.data_policy,
        }


@dataclass(frozen=True)
class ExecutionResult:
    status: str
    analysis: dict[str, Any] = field(default_factory=dict)
    deliverable: dict[str, Any] = field(default_factory=dict)
    warnings: tuple[str, ...] = ()
    provenance: dict[str, Any] = field(default_factory=dict)
    error: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if self.status not in Status.ALL:
            raise ValueError(f"Estado no registrado: {self.status}")
        if self.error is not None and not isinstance(self.error, dict):
            raise ValueError("error debe ser un objeto JSON")

    def to_dict(self) -> dict[str, Any]:
        value: dict[str, Any] = {
            "schema_version": CONTRACT_VERSION,
            "status": self.status,
            "analysis": _copy_mapping(self.analysis),
            "deliverable": _copy_mapping(self.deliverable),
            "warnings": list(self.warnings),
            "provenance": _copy_mapping(self.provenance),
        }
        if self.error is not None:
            value["error"] = _copy_mapping(self.error)
        return value
