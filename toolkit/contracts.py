"""Contract loading and lightweight JSON validation for the public models."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from .errors import ContractError
from .models import CONTRACT_VERSION, ExecutionResult, ToolMetadata


SCHEMA_ROOT = Path(__file__).resolve().parent / "schemas"


def load_schema(name: str) -> dict[str, Any]:
    path = SCHEMA_ROOT / name
    if not path.is_file():
        raise ContractError(f"No existe el esquema: {name}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ContractError(f"JSON inválido en el esquema {name}: {exc}") from exc
    if not isinstance(value, dict):
        raise ContractError(f"El esquema {name} debe ser un objeto")
    return value


def _require_keys(value: Mapping[str, Any], keys: tuple[str, ...], label: str) -> None:
    missing = [key for key in keys if key not in value]
    if missing:
        raise ContractError(f"{label}: faltan campos: {', '.join(missing)}")


def validate_metadata_dict(value: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ContractError("ToolMetadata debe ser un objeto")
    _require_keys(value, ("id", "version", "name", "description", "input_schema", "output_schema", "contract_version"), "ToolMetadata")
    capabilities = frozenset(value.get("capabilities", ()))
    entrypoint = value.get("entrypoint")
    script = value.get("script")
    try:
        metadata = ToolMetadata(
            id=str(value["id"]),
            version=str(value["version"]),
            name=str(value["name"]),
            description=str(value["description"]),
            input_schema=str(value["input_schema"]),
            output_schema=str(value["output_schema"]),
            contract_version=str(value["contract_version"]),
            phase=value.get("phase"),
            entrypoint=entrypoint,
            script=script,
            capabilities=capabilities,
            input_kinds=frozenset(value.get("input_kinds", ())),
            output_formats=frozenset(value.get("output_formats", ())),
            tags=frozenset(value.get("tags", ())),
        )
    except (TypeError, ValueError) as exc:
        raise ContractError(str(exc)) from exc
    return metadata.to_dict()


def validate_result_dict(value: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ContractError("ExecutionResult debe ser un objeto")
    _require_keys(value, ("status", "analysis", "deliverable", "warnings", "provenance"), "ExecutionResult")
    if value.get("schema_version", CONTRACT_VERSION) != CONTRACT_VERSION:
        raise ContractError("ExecutionResult usa una versión de contrato incompatible")
    try:
        result = ExecutionResult(
            status=str(value["status"]),
            analysis=dict(value["analysis"]),
            deliverable=dict(value["deliverable"]),
            warnings=tuple(str(item) for item in value["warnings"]),
            provenance=dict(value["provenance"]),
            error=dict(value["error"]) if value.get("error") is not None else None,
        )
    except (TypeError, ValueError) as exc:
        raise ContractError(str(exc)) from exc
    return result.to_dict()


def validate_schema_documents() -> list[str]:
    errors: list[str] = []
    for name in ("tool-metadata.schema.json", "execution-request.schema.json", "normalized-request.schema.json", "tool-selection.schema.json", "execution-plan.schema.json", "execution-result.schema.json", "llm-provider-config.schema.json"):
        try:
            schema = load_schema(name)
            if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
                errors.append(f"{name}: falta el dialecto JSON Schema 2020-12")
            if schema.get("type") != "object":
                errors.append(f"{name}: el tipo raíz debe ser object")
        except ContractError as exc:
            errors.append(str(exc))
    return errors
