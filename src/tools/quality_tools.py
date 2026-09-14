import os
import subprocess
import sys

from src.security.validation import InvalidInputError, validate_relative_path

TEST_TIMEOUT = int(os.getenv("TEST_TIMEOUT", "180"))


def _run_cli(args: list[str], timeout: int) -> subprocess.CompletedProcess:
    """Exécute un binaire ou module Python (pytest) sans shell."""
    if args[0] == "pytest":
        args = [sys.executable, "-m"] + args
    return subprocess.run(
        args,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def run_tests(path: str = "tests") -> str:
    """Exécute la suite de tests pytest et retourne un rapport de synthèse.

    Args:
        path: Chemin relatif des tests (validation stricte).
    """
    rel_path = validate_relative_path(path)
    try:
        result = _run_cli(["pytest", "-q", rel_path], TEST_TIMEOUT)
    except subprocess.TimeoutExpired:
        return f"ÉCHEC : tests dépassés après {TEST_TIMEOUT}s sur {rel_path}."

    output = result.stdout + result.stderr
    if result.returncode == 0:
        return f"SUCCÈS : tous les tests passent.\n{output}"
    return f"ÉCHEC ({result.returncode}) : tests en erreur.\n{output}"


def get_coverage(path: str = "tests") -> str:
    """Mesure la couverture de code (pytest --cov) et retourne le ratio.

    Args:
        path: Chemin relatif des tests à exécuter.
    """
    rel_path = validate_relative_path(path)
    try:
        result = _run_cli(
            ["pytest", "--cov", "--cov-report=term-missing", "-q", rel_path],
            TEST_TIMEOUT,
        )
    except subprocess.TimeoutExpired:
        return f"ÉCHEC : couverture non mesurée (timeout {TEST_TIMEOUT}s)."

    output = result.stdout + result.stderr
    if result.returncode == 0:
        return f"Couverture mesurée avec succès.\n{output}"
    return f"Couverture interrompue (code {result.returncode}).\n{output}"


def check_dependencies() -> str:
    """Audite les dépendances Python via pip-audit (CVE)."""
    try:
        result = _run_cli(["pip-audit"], 120)
    except subprocess.TimeoutExpired:
        return "ÉCHEC : audit pip-audit dépassé après 120s."
    if result.returncode == 0:
        return "✅ Aucun CVE détecté dans les dépendances."
    return "❌ Vulnérabilités détectées par pip-audit :\n" + result.stdout