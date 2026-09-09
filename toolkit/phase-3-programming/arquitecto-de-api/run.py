#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from phase_3_engine import run_tool
SKILL = {'name': 'Arquitecto de API', 'description': 'Esta herramienta de diseño de API proporciona patrones estándar de REST y GraphQL junto con plantillas de OpenAPI para el modelado de recursos, el control de versiones y el manejo de errores. Establece una base estructurada para la arquitectura de API, ayudando a los desarrolladores a garantizar la consistencia y el cumplimiento de los estándares de la industria antes de escribir cualquier código de implementación.', 'slug': 'arquitecto-de-api'}

def main() -> int:
    parser = argparse.ArgumentParser(description=SKILL["name"])
    parser.add_argument("-i", "--input", type=Path)
    parser.add_argument("-o", "--output", type=Path)
    args = parser.parse_args()
    try:
        raw = args.input.read_text(encoding="utf-8") if args.input else sys.stdin.read()
        payload = json.loads(raw or "{}")
        if not isinstance(payload, dict): raise ValueError("La entrada debe ser un objeto JSON")
        result = run_tool(SKILL, payload)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output: args.output.write_text(rendered, encoding="utf-8")
    else: sys.stdout.write(rendered)
    return 0 if result["status"] == "ready" else 1

if __name__ == "__main__": raise SystemExit(main())
