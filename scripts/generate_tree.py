"""Generador de árbol de proyecto para el repositorio CommunityGuard.

Modo de uso (one-shot):

python scripts\generate_tree.py --root . --output docs\project_tree.md

Opciones:
    --root PATH     Carpeta raíz a escanear (por defecto: carpeta padre del script)
    --output PATH   Archivo Markdown de salida (por defecto: docs/project_tree.md)
    --insert        Si se pasa, intenta reemplazar la sección entre
                                    <!-- PROJECT-TREE:START --> y <!-- PROJECT-TREE:END --> en README.md
    --ignore NAME   Patron/archivo o carpeta a ignorar; puede repetirse

El script no hace commits automáticos. Es seguro para ejecución manual y CI.
"""

from __future__ import annotations
import os
import argparse
from pathlib import Path
from typing import List

IGNORE_DEFAULT = {".venv", "__pycache__", ".git", ".gitignore", "node_modules"}


def build_tree_lines(root: Path, ignore: List[str] | None = None) -> List[str]:
    ignore_set = set(IGNORE_DEFAULT)
    if ignore:
        ignore_set.update(ignore)

    lines: List[str] = []
    root = root.resolve()
    prefix = ""

    def walk(dir_path: Path, indent: str = ""):
        try:
            entries = sorted([p for p in dir_path.iterdir()], key=lambda p: (p.is_file(), p.name.lower()))
        except PermissionError:
            return
        for i, p in enumerate(entries):
            name = p.name
            if name in ignore_set:
                continue
            connector = "└── " if i == len(entries) - 1 else "├── "
            if p.is_dir():
                lines.append(f"{indent}{connector}{name}/")
                walk(p, indent + ("    " if i == len(entries) - 1 else "│   "))
            else:
                lines.append(f"{indent}{connector}{name}")

    lines.append(f"{root.name}/")
    walk(root)
    return lines


def write_markdown(lines: List[str], out_path: Path, header: str = "Project tree") -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(f"## {header}\n\n")
        f.write("```")
        f.write("\n")
        for l in lines:
            f.write(l + "\n")
        f.write("```\n")
    return out_path


def insert_into_readme(readme_path: Path, lines: List[str]) -> bool:
    start_marker = "<!-- PROJECT-TREE:START -->"
    end_marker = "<!-- PROJECT-TREE:END -->"
    if not readme_path.exists():
        return False
    content = readme_path.read_text(encoding="utf-8")
    if start_marker not in content or end_marker not in content:
        return False
    before, rest = content.split(start_marker, 1)
    _, after = rest.split(end_marker, 1)
    new_block = start_marker + "\n```\n"
    for l in lines:
        new_block += l + "\n"
    new_block += "```\n" + end_marker
    updated = before + new_block + after
    readme_path.write_text(updated, encoding="utf-8")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", "-r", default=None, help="Path root to scan (default: parent of script)")
    parser.add_argument("--output", "-o", default="docs/project_tree.md", help="Markdown output path")
    parser.add_argument("--insert", action="store_true", help="Insert into README.md between markers")
    parser.add_argument("--ignore", action="append", help="Names to ignore (may be repeated)")
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    root = Path(args.root).resolve() if args.root else script_dir.parent
    out_path = Path(args.output)

    lines = build_tree_lines(root, args.ignore)
    write_markdown(lines, out_path, header=f"Estructura de {root.name}")
    print(f"Wrote tree to {out_path}")

    if args.insert:
        readme = root / "README.md"
        ok = insert_into_readme(readme, lines)
        if ok:
            print(f"Inserted tree into {readme} between markers")
        else:
            print(f"Markers not found or README.md missing: {readme}")
