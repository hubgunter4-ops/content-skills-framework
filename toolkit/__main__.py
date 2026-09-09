from __future__ import annotations

import argparse
from pathlib import Path
from .catalog import load_skills, validate_skills

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"

def show_menu() -> None:
    print("Content Skills Toolkit")
    print("1) Listar habilidades")
    print("2) Mostrar una habilidad")
    print("3) Validar catálogo")
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
        print("Opción no válida. Usa 1, 2, 3 o q.")

def list_skills() -> None:
    for skill in load_skills(SKILLS):
        print(f"{skill.slug}\t{skill.name}")

def show_skill(slug: str) -> int:
    for skill in load_skills(SKILLS):
        if skill.slug == slug:
            print(skill.path.read_text(encoding="utf-8"))
            return 0
    print(f"No existe la habilidad: {slug}")
    return 2

def validate() -> int:
    errors = validate_skills(SKILLS)
    if errors:
        print("Catálogo inválido:")
        print("\n".join(f"- {error}" for error in errors))
        return 1
    print(f"Catálogo válido: {len(load_skills(SKILLS))} habilidades.")
    return 0

def main() -> int:
    parser = argparse.ArgumentParser(description="Descubre y valida habilidades locales.")
    parser.add_argument("command", nargs="?", choices=("list", "show", "validate"))
    parser.add_argument("slug", nargs="?")
    args = parser.parse_args()
    if not args.command:
        show_menu()
        return 0
    if args.command == "list":
        list_skills(); return 0
    if args.command == "validate":
        return validate()
    if not args.slug:
        parser.error("show requiere un slug")
    return show_skill(args.slug)

if __name__ == "__main__":
    raise SystemExit(main())
