#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from phase_2_engine import run_tool
SKILL = {'name': 'Risk Metrics Pro', 'description': 'Herramienta de cálculo de riesgo de cartera que computa métricas principales como VaR, CVaR, ratio de Sharpe, ratio de Sortino y el drawdown máximo. Proporciona metodologías detalladas y mejores prácticas, ayudando a inversores cuantitativos y gestores de riesgos a medir con precisión el riesgo de la cartera, implementar límites y construir sistemas de monitoreo robustos.', 'slug': 'risk-metrics-pro'}

def main() -> int:
    parser = argparse.ArgumentParser(description=SKILL["name"])
    parser.add_argument("-i", "--input", type=Path)
    parser.add_argument("-o", "--output", type=Path)
    args = parser.parse_args()
    try:
        payload = json.loads(args.input.read_text(encoding="utf-8") if args.input else sys.stdin.read() or "{}")
        if not isinstance(payload, dict):
            raise ValueError("La entrada debe ser un objeto JSON")
        result = run_tool(SKILL, payload)
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
