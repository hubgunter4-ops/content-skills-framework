#!/usr/bin/env python3
"""Skill busqueda-de-conocimiento-en-git — formato content-skills-framework.
Envoltorio de hybrid.retrieve: busca en git público local y devuelve
fragmentos con procedencia. Solo lectura, stdlib.
Uso: echo '{"query":"extract video id from url","k":3}' | python3 run.py
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
# La skill puede vivir en el repo de Frijol o copiada dentro del framework;
# busca hybrid.py en el repo de Frijol por ruta o por variable de entorno.
import os
_candidates = [HERE.parents[1], Path(os.environ.get("FRIJOL_HOME", "")),
               Path.home() / "workspace" / "ops" / "code-model-hybrid"]
BASE = next((p for p in _candidates if p and (p / "hybrid.py").exists()), HERE.parents[1])
sys.path.insert(0, str(BASE))
from hybrid import retrieve  # noqa: E402

SKILL = "busqueda-de-conocimiento-en-git"

def main() -> int:
    parser = argparse.ArgumentParser(description=SKILL)
    parser.add_argument("-i", "--input", type=Path)
    parser.add_argument("-o", "--output", type=Path)
    args = parser.parse_args()
    try:
        raw = args.input.read_text(encoding="utf-8") if args.input else sys.stdin.read()
        payload = json.loads(raw or "{}")
        query = str(payload.get("query") or payload.get("content") or "").strip()
        k = int(payload.get("k", 3))
        if not query:
            raise ValueError("falta 'query'")
        k = max(1, min(10, k))
        snippets = retrieve(query, k=k)
        deliverable = [{
            "repo": s["repo"], "file": s["file"], "start_line": s["start_line"],
            "license": s["license"], "url": s.get("path", ""),
            "code": s["text"],
        } for s in snippets]
        result = {
            "skill": SKILL, "status": "ready",
            "analysis": f"{len(deliverable)} fragmento(s) de registros públicos de git para: {query}",
            "deliverable": deliverable,
            "warnings": [] if deliverable else ["sin coincidencias en el índice local; amplía el corpus o reformula la consulta"],
        }
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
