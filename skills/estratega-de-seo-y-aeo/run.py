#!/usr/bin/env python3
"""Runner funcional local para Estratega de SEO & AEO."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from toolkit.skill_engine import build_result

SKILL_NAME = 'Estratega de SEO & AEO'
SKILL_SLUG = 'estratega-de-seo-y-aeo'
SKILL_DESCRIPTION = 'Esta guía de mejores prácticas para sitios web de contenido cubre tanto la Optimización de Motores de Búsqueda SEO tradicional como la Optimización de Motores de Respuesta AEO. Proporciona patrones accionables para ayudar a que su contenido se posicione mejor en los resultados de búsqueda estándar, al tiempo que garantiza que sea fácilmente detectable y citado con precisión por los motores de respuesta impulsados por IA'


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
