"""Phase modularization and phase entry point discovery."""
from __future__ import annotations

from dataclasses import dataclass
from importlib import metadata as importlib_metadata
from pathlib import Path
from typing import Any

from .registry import load_registry

PHASE_ENTRY_POINT_GROUP = "content_skills_toolkit.phases"


@dataclass(frozen=True)
class ResourceProfile:
    cpu_seconds: float
    memory_mb: int
    max_concurrency: int
    network: bool = False


@dataclass(frozen=True)
class PhaseDescriptor:
    phase_id: str
    name: str
    description: str
    package: str
    tool_count: int
    resource_profile: ResourceProfile
    contract_min: str = "1.0"

    def to_dict(self) -> dict[str, Any]:
        return {
            "phase_id": self.phase_id,
            "name": self.name,
            "description": self.description,
            "package": self.package,
            "tool_count": self.tool_count,
            "resource_profile": {
                "cpu_seconds": self.resource_profile.cpu_seconds,
                "memory_mb": self.resource_profile.memory_mb,
                "max_concurrency": self.resource_profile.max_concurrency,
                "network": self.resource_profile.network,
            },
            "contract_min": self.contract_min,
        }


PHASE_DESCRIPTORS = {
    "phase-1-content-toolkit": PhaseDescriptor(
        "phase-1-content-toolkit", "Content Toolkit", "Herramientas generales de contenido y documentación.", "toolkit.phase_1_content_toolkit", 52, ResourceProfile(60, 512, 4)
    ),
    "phase-2-datos": PhaseDescriptor(
        "phase-2-datos", "Datos", "Herramientas de validación, análisis y transformación de datos.", "toolkit.phase_2_datos", 57, ResourceProfile(120, 1024, 4)
    ),
    "phase-3-programming": PhaseDescriptor(
        "phase-3-programming", "Programming", "Herramientas de programación, revisión y generación técnica.", "toolkit.phase_3_programming", 89, ResourceProfile(180, 1024, 4)
    ),
    "phase-4-automatizacion": PhaseDescriptor(
        "phase-4-automatizacion", "Automatización", "Herramientas de automatización y flujos operativos.", "toolkit.phase_4_automatizacion", 23, ResourceProfile(180, 1024, 2)
    ),
    "phase-5-negocios": PhaseDescriptor(
        "phase-5-negocios", "Negocios", "Herramientas de estrategia, producto y operaciones de negocio.", "toolkit.phase_5_negocios", 34, ResourceProfile(120, 768, 4)
    ),
    "phase-6-medios": PhaseDescriptor(
        "phase-6-medios", "Medios", "Herramientas de imagen, audio y vídeo.", "toolkit.phase_6_medios", 49, ResourceProfile(300, 2048, 2)
    ),
}


def discover_phase_entry_points(group: str = PHASE_ENTRY_POINT_GROUP) -> list[dict[str, str]]:
    selected = importlib_metadata.entry_points()
    if hasattr(selected, "select"):
        entries = list(selected.select(group=group))
    else:
        entries = list(selected.get(group, ()))
    result = []
    for entry in entries:
        dist = getattr(entry, "dist", None)
        result.append({
            "name": str(entry.name),
            "value": str(entry.value),
            "distribution": str(dist.metadata.get("Name", "unknown")) if dist else "unknown",
            "version": str(getattr(dist, "version", "unknown")) if dist else "unknown",
        })
    return sorted(result, key=lambda item: (item["name"], item["distribution"]))


def list_phases() -> list[PhaseDescriptor]:
    return [PHASE_DESCRIPTORS[key] for key in sorted(PHASE_DESCRIPTORS)]


def get_phase(phase_id: str) -> PhaseDescriptor:
    try:
        return PHASE_DESCRIPTORS[phase_id]
    except KeyError as exc:
        raise KeyError(f"No existe la fase: {phase_id}") from exc


def tools_for_phase(root: Path, phase_id: str | None = None) -> list[Any]:
    registry = load_registry(root)
    if phase_id is None:
        return registry
    get_phase(phase_id)
    return [spec for spec in registry if spec.phase == phase_id]


__all__ = [
    "PHASE_DESCRIPTORS",
    "PHASE_ENTRY_POINT_GROUP",
    "PhaseDescriptor",
    "ResourceProfile",
    "discover_phase_entry_points",
    "get_phase",
    "list_phases",
    "tools_for_phase",
]
