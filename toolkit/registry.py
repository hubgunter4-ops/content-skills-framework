from __future__ import annotations

"""Read-only registry for skills and their executable tools."""

from dataclasses import dataclass
import json
from pathlib import Path
import re

from .catalog import REQUIRED_SECTIONS, Skill, load_skills


PHASE_CATALOGS = {
    "phase-2-datos": ("phase_2_engine", "toolkit/phase-2-datos/catalog.json"),
    "phase-3-programming": ("phase_3_engine", "toolkit/phase-3-programming/catalog.json"),
    "phase-4-automatizacion": ("phase_4_engine", "toolkit/phase-4-automatizacion/catalog.json"),
    "phase-5-negocios": ("phase_5_engine", "toolkit/phase-5-negocios/catalog.json"),
    "phase-6-medios": ("phase_6_engine", "toolkit/phase-6-medios/catalog.json"),
}

DOCUMENT_SECTION_ALIASES = {
    "## Entradas aceptadas": ("## Entradas aceptadas", "## Entradas"),
    "## Salida esperada": ("## Salida esperada", "## Salida"),
}


class RegistryError(ValueError):
    """Raised when a registry identifier is missing or ambiguous."""


@dataclass(frozen=True)
class ToolSpec:
    """Identity metadata for one skill and its executable tool."""

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

    @property
    def skill_identifier(self) -> str:
        """Qualified skill identifier exposed to selection and discovery flows."""
        return self.identifier

    @property
    def tool_path(self) -> Path:
        """Executable tool associated with this skill."""
        return self.runner


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


def validate_registry(root: Path) -> list[str]:
    """Validate all phase identities and local tool contracts without executing runners."""
    errors: list[str] = []
    registry = load_registry(root)
    identifiers = [spec.identifier for spec in registry]
    for duplicate in sorted({item for item in identifiers if identifiers.count(item) > 1}):
        errors.append(f"identificador duplicado: {duplicate}")

    expected_counts = {
        "phase-1-content-toolkit": 52,
        "phase-2-datos": 57,
        "phase-3-programming": 89,
        "phase-4-automatizacion": 23,
        "phase-5-negocios": 34,
        "phase-6-medios": 49,
    }
    for phase, expected in expected_counts.items():
        actual = sum(spec.phase == phase for spec in registry)
        if actual != expected:
            errors.append(f"{phase}: se esperaban {expected} herramientas, se encontraron {actual}")

    for spec in registry:
        label = spec.identifier
        if not spec.folder.is_dir():
            errors.append(f"{label}: falta la carpeta de la herramienta")
            continue
        for relative in ("run.py", "input.example.json", "output.schema.json", "resources/README.md", "tests/test_smoke.py"):
            if not (spec.folder / relative).is_file():
                errors.append(f"{label}: falta {relative}")
        if spec.skill_doc is None or not spec.skill_doc.is_file():
            errors.append(f"{label}: falta SKILL.md")
            continue
        text = spec.skill_doc.read_text(encoding="utf-8")
        name_match = re.search(r"^name:\s*(.+)$", text, re.MULTILINE)
        description_match = re.search(r"^description:\s*(.+)$", text, re.MULTILINE)
        if not name_match or name_match.group(1).strip() != spec.slug:
            errors.append(f"{label}: name no coincide con el slug")
        if not description_match or description_match.group(1).strip() != spec.description:
            errors.append(f"{label}: description no coincide con el catálogo")
        for section in REQUIRED_SECTIONS:
            aliases = DOCUMENT_SECTION_ALIASES.get(section, (section,))
            if not any(alias in text for alias in aliases):
                errors.append(f"{label}: falta {section}")
        association_values = (
            f"toolkit/{spec.phase}/{spec.slug}/run.py",
            f"toolkit/{spec.phase}/{spec.slug}/input.example.json",
            f"toolkit/{spec.phase}/{spec.slug}/output.schema.json",
            f"toolkit/{spec.phase}/{spec.slug}/tests/test_smoke.py",
        )
        for value in association_values:
            if value not in text:
                errors.append(f"{label}: falta asociación {value}")
    return errors
