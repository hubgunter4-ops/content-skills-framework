from __future__ import annotations

import json
import platform
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "phase0-baseline.json"


def run(label: str, command: list[str]) -> dict[str, object]:
    started = time.perf_counter()
    completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
    return {
        "label": label,
        "command": command,
        "returncode": completed.returncode,
        "elapsed_ms": elapsed_ms,
        "stdout_tail": completed.stdout[-2000:],
        "stderr_tail": completed.stderr[-2000:],
    }


def main() -> int:
    git_head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    git_status = subprocess.check_output(
        ["git", "-c", "color.ui=false", "status", "--short", "--branch"],
        cwd=ROOT,
        text=True,
    )
    checks = [
        run("unit_tests", [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"]),
        run("compileall", [sys.executable, "-m", "compileall", "-q", "toolkit"]),
        run("catalog_validate", [sys.executable, "-m", "toolkit", "validate"]),
        run("list", [sys.executable, "-m", "toolkit", "list"]),
        run("show", [sys.executable, "-m", "toolkit", "show", "phase-2-datos/validacion-de-datos"]),
        run("sample_run", [
            sys.executable,
            "-m",
            "toolkit",
            "run",
            "phase-2-datos/validacion-de-datos",
            "-i",
            "toolkit/phase-2-datos/validacion-de-datos/input.example.json",
        ]),
    ]
    payload = {
        "repository": "content-skills-framework",
        "source_repository": "content-skills-toolkit",
        "head": git_head,
        "python": sys.version,
        "platform": platform.platform(),
        "git_status": git_status,
        "checks": checks,
        "all_passed": all(item["returncode"] == 0 for item in checks),
        "notes": [
            "La ejecución se realizó localmente sin activar integraciones externas.",
            "La compatibilidad del CLI existente se conserva como criterio de Fase 0.",
            "Los archivos de diseño previos se incorporarán en un commit separado de documentación.",
        ],
    }
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(OUTPUT), "all_passed": payload["all_passed"]}, ensure_ascii=False))
    return 0 if payload["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
