from __future__ import annotations

"""Read-only registry for base skills and phase tools."""

from dataclasses import dataclass
import json
from pathlib import Path

from .catalog import Skill, load_skills


PHASE_CATALOGS = {
    "phase-2-datos": ("phase_2_engine", "toolkit/phase-2-datos/catalog.json"),
    "phase-3-programming": ("phase_3_engine", "toolkit/phase-3-programming/catalog.json"),
    "phase-4-automatizacion": ("phase_4_engine", "toolkit/phase-4-automatizacion/catalog.json"),
    "phase-5-negocios": ("phase_5_engine", "toolkit/phase-5-negocios/catalog.json"),
    "phase-6-medios": ("phase_6_engine", "toolkit/phase-6-medios/catalog.json"),
}


class RegistryError(ValueError):
    """Raised when a registry identifier is missing or ambiguous."""


@dataclass(frozen=True)
class ToolSpec:
    """Location and identity metadata for one executable tool."""

    phase: str
    slug: str
    name: str
    description: str
    folder: Path
    runner: Path
    skill_doc: Path | None
    engine: str
    catalog: Path | None

    @property
    def identifier(self) -> str:
        return f"{self.phase}/{self.slug}"


def _base_specs(root: Path) -> list[ToolSpec]:
    skills_root = root / "toolkit" / "phase-1-content-toolkit"
    return [
        ToolSpec(
            phase="phase-1-content-toolkit",
            slug=skill.slug,
            name=skill.name,
            description=skill.description,
            folder=skill.path.parent,
            runner=skill.path.parent / "run.py",
            skill_doc=skill.path,
            engine="skill_engine",
            catalog=None,
        )
        for skill in load_skills(skills_root)
    ]


def _phase_specs(root: Path, phase: str, engine: str, catalog_path: str) -> list[ToolSpec]:
    catalog = root / catalog_path
    entries = json.loads(catalog.read_text(encoding="utf-8"))
    phase_root = root / "toolkit" / phase
    return [
        ToolSpec(
            phase=phase,
            slug=str(entry["slug"]),
            name=str(entry["name"]),
            description=str(entry["description"]),
            folder=phase_root / str(entry["slug"]),
            runner=phase_root / str(entry["slug"]) / "run.py",
            skill_doc=phase_root / str(entry["slug"]) / "SKILL.md",
            engine=engine,
            catalog=catalog,
        )
        for entry in entries
    ]


def load_registry(root: Path) -> list[ToolSpec]:
    """Load all base and phase tools without importing or executing runners."""
    specs = _base_specs(root)
    for phase, (engine, catalog_path) in PHASE_CATALOGS.items():
        specs.extend(_phase_specs(root, phase, engine, catalog_path))
    return sorted(specs, key=lambda spec: (spec.phase, spec.slug))


def resolve_tool(registry: list[ToolSpec], identifier: str) -> ToolSpec:
    """Resolve a qualified phase/slug or an unambiguous short slug."""
    requested = identifier.strip().strip("/")
    qualified = [spec for spec in registry if spec.identifier == requested]
    if qualified:
        return qualified[0]
    matches = [spec for spec in registry if spec.slug == requested]
    if not matches:
        raise RegistryError(f"No existe la herramienta: {identifier}")
    if len(matches) > 1:
        options = ", ".join(spec.identifier for spec in matches)
        raise RegistryError(f"Slug ambiguo: {identifier}. Usa uno de: {options}")
    return matches[0]
