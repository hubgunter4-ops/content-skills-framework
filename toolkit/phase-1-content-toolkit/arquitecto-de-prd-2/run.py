#!/usr/bin/env python3
"""Runner funcional local para Arquitecto de PRD."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from toolkit.skill_engine import build_result

SKILL_NAME = 'Arquitecto de PRD'
SKILL_SLUG = 'arquitecto-de-prd-2'
SKILL_DESCRIPTION = 'Esta Skill es un asistente estructurado para redactar Documentos de Requisitos del Producto PRD, incorporando conocimientos de expertos en productos. Te guía desde la definición del problema hasta los criterios de éxito, haciendo que la planificación del producto sea más clara y ejecutable para los equipos de ingeniería'


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
