from __future__ import annotations

import argparse
import json
import subprocess  # nosec B404
import sys
from pathlib import Path

from .catalog import load_skills, validate_skills
from .integrations import catalog as integration_catalog
from .persistent_index import ensure_index, list_index, lookup
from .registry import RegistryError, load_registry, resolve_tool, validate_registry
from .cache import ToolCache
from .router import DeterministicRouter

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "toolkit" / "phase-1-content-toolkit"
DEFAULT_INDEX = ROOT / ".content-skills-index.sqlite3"


def show_menu() -> None:
    print("Content Skills Toolkit")
    print("1) Listar habilidades")
    print("2) Mostrar una habilidad")
    print("3) Validar catálogo")
    print("4) Listar integraciones opcionales")
    print("q) Cancelar")
    while True:
        try:
            choice = input("Selecciona una opción: ").strip().lower()
        except EOFError:
            print("\nCancelado.")
            return
        if choice in {"q", "quit", "salir", "0"}:
            print("Cancelado.")
            return
        if choice == "1":
            list_skills()
            return
        if choice == "2":
            slug = input("Slug de la habilidad (o q para cancelar): ").strip()
            if slug.lower() == "q":
                print("Cancelado.")
                return
            show_skill(slug)
            return
        if choice == "3":
            validate()
            return
        if choice == "4":
            list_integrations()
            return
        print("Opción no válida. Usa 1, 2, 3, 4 o q.")


def list_skills() -> int:
    for spec in load_registry(ROOT):
        print(f"{spec.identifier}\t{spec.name}")
    return 0


def _resolve(identifier: str):
    try:
        return resolve_tool(load_registry(ROOT), identifier)
    except RegistryError as exc:
        print(str(exc))
        return None


def show_skill(identifier: str) -> int:
    spec = _resolve(identifier)
    if spec is None:
        return 2
    print(spec.skill_doc.read_text(encoding="utf-8"))
    return 0


def validate() -> int:
    errors = validate_skills(SKILLS)
    errors.extend(validate_registry(ROOT))
    if errors:
        print("Catálogo inválido:")
        print("\n".join(f"- {error}" for error in errors))
        return 1
    print(f"Catálogo y contratos válidos: {len(load_registry(ROOT))} habilidades con herramienta asociada.")
    return 0


def list_integrations() -> int:
    for integration in integration_catalog():
        credentials = ", ".join(integration["credential_env"]) or "sin credencial obligatoria"
        print(f"{integration['name']}\t{integration['service']}\tcredencial: {credentials}")
        print(f"  {integration['description']}")
        print(f"  skills: {', '.join(integration['skills'])}")
    return 0


def index_tools(identifier: str | None, phase: str | None, db_path: str | None) -> int:
    """Build the persistent index and optionally display a record."""
    path = Path(db_path) if db_path else DEFAULT_INDEX
    _, rebuilt = ensure_index(ROOT, path)
    state = "reconstruido" if rebuilt else "vigente"
    if identifier:
        record = lookup(path, identifier)
        if record is None:
            print(f"No existe en el índice: {identifier}")
            return 2
        print(json.dumps(record.__dict__, ensure_ascii=False, indent=2, default=list))
        return 0
    records = list_index(path, phase=phase)
    print(f"Índice {state}: {len(records)} herramientas en {path}")
    for record in records:
        print(f"{record.tool_id}\t{record.status}\t{record.distribution}")
    return 0


def run_tool(identifier: str, input_file: str | None) -> int:
    spec = _resolve(identifier)
    if spec is None:
        return 2
    command = [sys.executable, str(spec.runner)]
    if input_file:
        command.extend(["--input", input_file])
    completed = subprocess.run(command, cwd=ROOT)  # nosec B603
    return completed.returncode


def route_request(request_text: str | None, input_file: str | None, phase: str | None, db_path: str | None) -> int:
    if input_file:
        request: object = json.loads(Path(input_file).read_text(encoding="utf-8"))
    elif request_text:
        request = request_text
    else:
        print("route requiere texto o -i/--input con JSON")
        return 2
    cache = ToolCache(ROOT, Path(db_path) if db_path else DEFAULT_INDEX)
    decision = DeterministicRouter(ROOT, cache).route(request, phase=phase)
    print(json.dumps(decision.to_dict(), ensure_ascii=False, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Descubre y valida habilidades locales.")
    parser.add_argument("command", nargs="?", choices=("list", "show", "run", "validate", "integrations", "index", "route"))
    parser.add_argument("slug", nargs="?")
    parser.add_argument("-i", "--input", dest="input_file")
    parser.add_argument("--phase", dest="phase")
    parser.add_argument("--db", dest="db_path")
    args = parser.parse_args()
    if not args.command:
        show_menu()
        return 0
    if args.command == "list":
        return list_skills()
    if args.command == "validate":
        return validate()
    if args.command == "integrations":
        return list_integrations()
    if args.command == "index":
        return index_tools(args.slug, args.phase, args.db_path)
    if args.command == "route":
        return route_request(args.slug, args.input_file, args.phase, args.db_path)
    if not args.slug:
        parser.error(f"{args.command} requiere un slug")
    if args.command == "run":
        return run_tool(args.slug, args.input_file)
    return show_skill(args.slug)


if __name__ == "__main__":
    raise SystemExit(main())
