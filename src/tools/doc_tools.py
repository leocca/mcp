import ast
import os
from dataclasses import dataclass, field
from typing import Iterable

from src.logic.analysis import analyze_code_with_llm

SOURCE_ROOT = os.getenv("SOURCE_ROOT", "src")


@dataclass
class ModuleDoc:
    module: str
    docstring: str | None = None
    functions: list[tuple[str, str | None]] = field(default_factory=list)


def _iter_py_files(root: str) -> Iterable[str]:
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in {"__pycache__", "venv"}]
        for name in filenames:
            if name.endswith(".py") and not name.startswith("__init__"):
                yield os.path.join(dirpath, name)


def _parse_docstrings(path: str) -> ModuleDoc:
    rel_module = path.replace("/", ".").removesuffix(".py")
    with open(path, "r", encoding="utf-8") as fh:
        tree = ast.parse(fh.read())

    doc = ModuleDoc(module=rel_module, docstring=ast.get_docstring(tree))
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith(
            ("git_", "get_", "run_", "scan_", "analyze_", "suggest_", "create_", "list_", "check_", "rollback_", "trigger_", "search_", "generate_")
        ):
            doc.functions.append((node.name, ast.get_docstring(node)))
    return doc


def _render_markdown(docs: list[ModuleDoc]) -> str:
    lines = ["# Documentation Générée — DevOps Assistant", ""]
    for doc in docs:
        lines.append(f"## Module `{doc.module}`")
        lines.append("")
        lines.append(doc.docstring.split("\n\n")[0] if doc.docstring else "_Aucune description._")
        lines.append("")
        if doc.functions:
            lines.append("| Fonction | Description |")
            lines.append("|---|---|")
            for name, ds in doc.functions:
                summary = (ds.split("\n\n")[0].split("\n")[0][:80] if ds else "-")
                lines.append(f"| `{name}` | {summary} |")
            lines.append("")
    return "\n".join(lines)


def generate_doc() -> str:
    """(IA) Analyse les docstrings du projet et génère une doc Markdown.

    Extraie la structure des modules, puis fait synthétiser par le LLM local
    un Markdown plus lisible à partir du rendu brut.
    """
    if not os.path.isdir(SOURCE_ROOT):
        return f"Erreur : dossier source {SOURCE_ROOT} introuvable."

    docs = [_parse_docstrings(p) for p in _iter_py_files(SOURCE_ROOT)]
    raw = _render_markdown(docs)

    prompt = (
        "Voici une documentation technique brute extraite d'un projet MCP "
        "DevOps. Réécris-la en Markdown propre et structuré (intro, sections, "
        "liste des outils avec leur rôle et niveau de danger) sans inventer "
        "d'information. 4 sections max, ton neutre.\n\n"
        f"{raw}"
    )
    refined = analyze_code_with_llm(prompt)
    return refined