#!/usr/bin/env python3
"""Runner funcional local para Coach de oratoria."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from toolkit.skill_engine import build_result

SKILL_NAME = 'Coach de oratoria'
SKILL_SLUG = 'coach-de-oratoria'
SKILL_DESCRIPTION = 'Esta habilidad sintetiza las lecciones de oratoria de 12 invitados destacados del pódcast de Lenny en 10 marcos de trabajo prácticos, como los métodos del Arco y la Flecha y el Momento de 5 Segundos. Te ayuda a preparar charlas, perfeccionar la comunicación y transmitir ideas con confianza en cualquier escenario'


def main() -> int:
    parser = argparse.ArgumentParser(description=f"Ejecuta localmente: {SKILL_NAME}")
    parser.add_argument("-i", "--input", type=Path, help="Archivo JSON de entrada; si se omite, lee stdin")
    parser.add_argument("-o", "--output", type=Path, help="Archivo JSON de salida; si se omite, escribe stdout")
    args = parser.parse_args()
    try:
        raw = args.input.read_text(encoding="utf-8") if args.input else sys.stdin.read()
        payload = json.loads(raw or "{}")
        if not isinstance(payload, dict):
            raise ValueError("La entrada JSON debe ser un objeto")
        result = build_result(SKILL_SLUG, SKILL_NAME, SKILL_DESCRIPTION, payload)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)
    return 0 if result["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
