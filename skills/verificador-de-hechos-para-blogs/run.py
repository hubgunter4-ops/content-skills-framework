#!/usr/bin/env python3
"""Runner funcional local para Verificador de hechos para blogs."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from toolkit.skill_engine import build_result

SKILL_NAME = 'Verificador de hechos para blogs'
SKILL_SLUG = 'verificador-de-hechos-para-blogs'
SKILL_DESCRIPTION = 'Esta habilidad verifica los hechos de las publicaciones de blog extrayendo automáticamente afirmaciones y declaraciones estadísticas, y visitando las URL de las fuentes citadas para verificar su exactitud. Estandariza el flujo de trabajo de verificación de contenido, ayudando a los creadores y editores a asegurar la autenticidad y fiabilidad antes de publicar, mejorando así la calidad y credibilidad del contenido'


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
