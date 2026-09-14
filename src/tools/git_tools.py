import os
import subprocess
from typing import Optional

from github import Github
from loguru import logger

from src.security.validation import (
    InvalidInputError,
    validate_branch_name,
    validate_git_sha,
    validate_relative_path,
)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_NAME = os.getenv("TARGET_REPOSITORY")

MAX_LOGS = 20


def _run_git(args: list[str], cwd: str | None = None) -> str:
    """Exécute git avec une liste d'arguments rigide (jamais de shell)."""
    cmd = ["git", *args]
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    return result.stdout


def get_git_status(cwd: str | None = None) -> str:
    """Retourne l'état actuel du dépôt cible."""
    return _run_git(["status"], cwd=cwd)


def get_git_diff(commit_sha: str, cwd: str | None = None) -> str:
    """Retourne les changements d'un commit (ou de la zone de travail).

    Args:
        commit_sha: SHA du commit (validation stricte hexadécimale).
        cwd: Dossier de travail (défaut : répertoire courant).

    Raises:
        InvalidInputError: si le SHA est invalide.
    """
    sha = validate_git_sha(commit_sha)
    return _run_git(["show", "--stat", "--format=fuller", sha], cwd=cwd)


def get_git_log(limit: int = 10, cwd: str | None = None) -> str:
    """Retourne l'historique des commits (format oneline enrichi).

    Args:
        limit: Nombre de commits à retourner (borné à MAX_LOGS).
    """
    limit = max(1, min(int(limit), MAX_LOGS))
    return _run_git(
        ["log", f"-{limit}", "--pretty=format:%h | %an | %ad | %s", "--date=short"],
        cwd=cwd,
    )


def search_code(query: str, path: str = ".", cwd: str | None = None) -> str:
    """Recherche une chaîne dans le code local (git grep).

    Args:
        query: Chaîne recherchée.
        path: Chemin relatif restreint la recherche (validation stricte).

    Raises:
        InvalidInputError: si le chemin ou la requête sont dangereux.
    """
    rel_path = validate_relative_path(path)
    forbidden = set(";|&`$()<>\"' ")
    if not query or any(c in query for c in forbidden):
        raise InvalidInputError("Requête de recherche invalide (métacaractères interdits).")
    return _run_git(["grep", "-n", "--", query, rel_path], cwd=cwd)


def get_pr_diff(pr_id: int) -> str:
    """Récupère le contenu d'une Pull Request via l'API GitHub."""
    if int(pr_id) <= 0:
        raise InvalidInputError(f"Numéro de PR invalide : {pr_id!r}.")
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(REPO_NAME)
    pr = repo.get_pull(int(pr_id))

    files = pr.get_files()
    diff_content = ""
    for file in files:
        diff_content += f"Fichier: {file.filename}\n{file.patch}\n"
    return diff_content