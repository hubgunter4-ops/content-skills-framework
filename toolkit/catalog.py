from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

REQUIRED_SECTIONS = ("## Propósito", "## Flujo de trabajo", "## Entradas aceptadas", "## Salida esperada", "## Guardrails", "## Plantilla de solicitud", "## Lista de control")

@dataclass(frozen=True)
class Skill:
    name: str
    slug: str
    description: str
    path: Path

def load_skills(root: Path) -> list[Skill]:
    result = []
    for path in sorted(root.glob("*/SKILL.md")):
        text = path.read_text(encoding="utf-8")
        match = re.search(r"^name:\s*(.+)$", text, re.MULTILINE)
        desc = re.search(r"^description:\s*(.+)$", text, re.MULTILINE)
        if not match or not desc:
            continue
        result.append(Skill(match.group(1).strip(), path.parent.name, desc.group(1).strip(), path))
    return result

def validate_skills(root: Path) -> list[str]:
    errors = []
    for skill in load_skills(root):
        text = skill.path.read_text(encoding="utf-8")
        for section in REQUIRED_SECTIONS:
            if section not in text:
                errors.append(f"{skill.slug}: falta {section}")
        if re.search(r"\b(?:estrellas|usos)\b", text, re.IGNORECASE):
            errors.append(f"{skill.slug}: contiene una métrica excluida")
    return errors
