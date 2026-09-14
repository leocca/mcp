"""Validation stricte des entrées fournies par le LLM ou les clients.

Empêche les injections d'arguments de commande (branches ``; rm -rf /``) et
les contournements de chemin (``../../etc/passwd``) avant tout appel système.
Toutes les fonctions lèvent :class:`InvalidInputError` en cas de donnée
invalide — jamais ``None`` ni valeur partielle.
"""

from __future__ import annotations

import re

__all__ = ["InvalidInputError", "validate_branch_name", "validate_git_sha", "validate_image_tag", "validate_relative_path"]


class InvalidInputError(ValueError):
    """Entrée rejetée car potentiellement dangereuse ou malformée."""


# Une branche git ne peut contenir que : lettres, chiffres, et [._/-]. Elle ne
# doit ni commencer ni finir par "/" chez la plupart des forges, ni contenir
# "..", "~^:?*[\\]", espaces ou caractères de contrôle / shell.
_BRANCH_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]{0,254}$")

# SHA-1 (40 hex) ou SHA-256 (64 hex), ou abréviation courte ≥ 7 hex.
_SHA_PATTERN = re.compile(r"^[0-9a-fA-F]{7,64}$")

# Tag Docker : [A-Za-z0-9_][A-Za-z0-9._-]{0,127}
_TAG_PATTERN = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9._-]{0,127}$")

# Chemin relatif sûr : segments alphanumériques/de base, sans "..", sans
# séparateur absolu, sans caractères réservés au shell.
_PATH_PATTERN = re.compile(r"^[A-Za-z0-9._/-]+$")

_FORBIDDEN_IN_PATH = ("..", "~", ":") + tuple(";|&`$<>(){}[]*?\"'\\ ")


def validate_branch_name(branch: str) -> str:
    """Valide un nom de branche git.

    Args:
        branch: Nom de branche soumis par l'utilisateur ou le LLM.

    Returns:
        Le nom de branche normalisé (sans espaces de bord).

    Raises:
        InvalidInputError: si le nom contient des caractères dangereux ou une
            structure invalide (traversée de chemin, début/fin par ``/``, etc.).
    """
    if not isinstance(branch, str) or not branch.strip():
        raise InvalidInputError("Nom de branche vide.")
    branch = branch.strip()
    if ".." in branch:
        raise InvalidInputError(f"Nom de branche invalide (contient '..') : {branch!r}.")
    if branch.startswith(("-", "/")) or branch.endswith("/"):
        raise InvalidInputError(f"Nom de branche invalide : {branch!r}.")
    if not _BRANCH_PATTERN.fullmatch(branch):
        raise InvalidInputError(
            f"Nom de branche invalide : {branch!r} (caractères autorisés : Alnum,_./-)."
        )
    return branch


def validate_git_sha(sha: str) -> str:
    """Valide un identifiant de commit git (abréviation ou complet)."""
    if not isinstance(sha, str) or not sha.strip():
        raise InvalidInputError("SHA de commit vide.")
    sha = sha.strip()
    if not _SHA_PATTERN.fullmatch(sha):
        raise InvalidInputError(f"SHA de commit invalide : {sha!r} (hexadécimal attendu).")
    return sha


def validate_image_tag(tag: str) -> str:
    """Valide un tag d'image Docker."""
    if not isinstance(tag, str) or not tag.strip():
        raise InvalidInputError("Tag d'image vide.")
    tag = tag.strip()
    if tag.startswith("-"):
        raise InvalidInputError(f"Tag d'image invalide (option) : {tag!r}.")
    if not _TAG_PATTERN.fullmatch(tag):
        raise InvalidInputError(f"Tag d'image Docker invalide : {tag!r}.")
    return tag


def validate_relative_path(path: str) -> str:
    """Valide un chemin relatif sûr (fichier ou dossier).

    Rejette toute forme de traversée de chemin (``..``), de chemin absolu et
    les métacaractères shell afin d'être utilisable sans ``shell=True`` ou
    dans des constructions de chemin.
    """
    if not isinstance(path, str) or not path.strip():
        raise InvalidInputError("Chemin vide.")
    path = path.strip()
    if path.startswith("/") or "://" in path:
        raise InvalidInputError(f"Chemin absolu interdit : {path!r}.")
    if any(seg == ".." for seg in path.split("/")):
        raise InvalidInputError(f"Traversée de chemin interdite : {path!r}.")
    if any(c in path for c in _FORBIDDEN_IN_PATH):
        raise InvalidInputError(f"Caractère interdit dans le chemin : {path!r}.")
    if not _PATH_PATTERN.fullmatch(path):
        raise InvalidInputError(f"Chemin invalide : {path!r}.")
    return path