#!/usr/bin/env python3
"""Local, deterministic runner for the Arquitecto de PRD skill."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SKILL_NAME = 'Arquitecto de PRD'
SKILL_SLUG = 'arquitecto-de-prd'
SKILL_DESCRIPTION = 'Esta herramienta proporciona una plantilla profesional con 8 módulos principales para ayudar a los gerentes de producto a generar rápidamente Documentos de Requisitos del Producto PRD claros y estructurados. Estandariza el proceso de documentación desde la definición del problema hasta el lanzamiento, mejorando la eficiencia de la comunicación en todo el equipo'
REQUIRED_INPUTS = ("objective", "audience", "content", "format")


def build_result(payload: dict) -> dict:
    missing = [key for key in REQUIRED_INPUTS if not str(payload.get(key, "")).strip()]
    content = str(payload.get("content", "")).strip()
    objective = str(payload.get("objective", "")).strip()
    audience = str(payload.get("audience", "")).strip()
    output_format = str(payload.get("format", "markdown")).strip()
    status = "ready" if not missing else "needs_input"
    return {
        "skill": {"name": SKILL_NAME, "slug": SKILL_SLUG, "description": SKILL_DESCRIPTION},
        "status": status,
        "request": {"objective": objective, "audience": audience, "format": output_format},
        "analysis": {
            "input_characters": len(content),
            "input_words": len(content.split()),
            "missing_fields": missing,
            "assumptions": ["La ejecución es local y no consulta fuentes externas."]
        },
        "deliverable": {
            "title": f"{SKILL_NAME} — {objective or 'Solicitud sin objetivo'}",
            "format": output_format,
            "content": content,
            "next_steps": [
                "Revisar exactitud y fuentes antes de publicar.",
                "Confirmar que el resultado cumple la audiencia y el formato solicitados."
            ] if status == "ready" else ["Completar los campos indicados en missing_fields."]
        },
        "warnings": (["Faltan entradas obligatorias: " + ", ".join(missing)] if missing else [])
    }


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
        result = build_result(payload)
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
