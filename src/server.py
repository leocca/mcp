from fastmcp import FastMCP
from fastmcp.server.context import Context

import os

from src.auth.security import verify_keycloak_token, has_role
from src.logic.analysis import analyze_code_with_llm
from src.security.audit import audit_action
from src.security.guard import detect_prompt_injection, redact_secrets
from src.security.hitl import confirm_destructive_action
from src.tools import docker_tools, github_tools, quality_tools, doc_tools
from src.tools.git_tools import (
    get_git_status,
    get_git_diff,
    get_git_log,
    search_code,
    get_pr_diff,
)
from src.tools.security_tools import (
    run_semgrep_scan,
    run_pip_audit,
)
from src.utils.logging_config import setup_logging

setup_logging()

# Initialisation du serveur
mcp = FastMCP("DevOps-Assistant")


def _user(token: str):
    return verify_keycloak_token(token)


def _audit(tool: str, user, params=None, **kw):
    audit_action(tool, user.get("username") if user else None, params, **kw)


# ============================================================
# GROUPE A — CODE & GIT (analyse assistée par LLM)
# ============================================================

@mcp.tool()
def git_status(token: str) -> str:
    """Retourne l'état actuel du dépôt cible."""
    user = _user(token)
    if not user:
        return "Accès refusé."
    _audit("git_status", user)
    return get_git_status()


@mcp.tool()
def git_diff(token: str, commit_sha: str) -> str:
    """Récupère les changements d'un commit (analyse ciblée)."""
    user = _user(token)
    if not user:
        return "Accès refusé."
    _audit("git_diff", user, {"commit_sha": commit_sha})
    return get_git_diff(commit_sha)


@mcp.tool()
def git_log(token: str, limit: int = 10) -> str:
    """Retourne l'historique des commits récents."""
    user = _user(token)
    if not user:
        return "Accès refusé."
    _audit("git_log", user, {"limit": limit})
    return get_git_log(limit)


@mcp.tool()
def search_code(token: str, query: str, path: str = ".") -> str:
    """Recherche une chaîne dans le code local (git grep)."""
    user = _user(token)
    if not user:
        return "Accès refusé."
    _audit("search_code", user, {"query": query, "path": path})
    return search_code(query, path)


@mcp.tool()
def analyze_pr(token: str, pr_id: int) -> str:
    """(IA) Analyse les bugs logiques d'une PR GitHub."""
    user = _user(token)
    if not user:
        return "Accès refusé."
    _audit("analyze_pr", user, {"pr_id": pr_id})

    diff = get_pr_diff(pr_id)
    # Contenu GitHub traité comme NON fiable avant envoi au LLM.
    verdict = detect_prompt_injection(diff)
    if not verdict.safe:
        return (
            f"[BLOQUÉ] Contenu de la PR {pr_id} suspect : {verdict.severity} "
            f"({', '.join(verdict.hits)}). Analyse refusée."
        )
    report = analyze_code_with_llm(redact_secrets(diff))
    return f"Rapport pour {user['username']} :\n{report}"


@mcp.tool()
def suggest_review(token: str, pr_id: int) -> str:
    """(IA) Génère des commentaires de revue de code pour une PR."""
    user = _user(token)
    if not user:
        return "Accès refusé."
    _audit("suggest_review", user, {"pr_id": pr_id})
    return github_tools.suggest_review(pr_id)


# ============================================================
# GROUPE B — CI/CD & DÉPLOIEMENT (HITL obligatoire *)
# ============================================================

@mcp.tool()
def get_pipeline_status(token: str, limit: int = 3) -> str:
    """Surveille le dernier statut des workflows GitHub Actions."""
    user = _user(token)
    if not user:
        return "Accès refusé."
    _audit("get_pipeline_status", user, {"limit": limit})
    return github_tools.get_pipeline_status(limit)


@mcp.tool()
async def trigger_pipeline(
    token: str, branch: str, workflow_file: str = "", dry_run: bool = True, ctx: Context = None
) -> str:
    """*Déclenchement CI* : relance un workflow GitHub Actions.

    Validation humaine explicite (élicitation MCP) requise dès que
    ``dry_run=False``.
    """
    user = _user(token)
    if not user:
        return "Accès refusé."
    params = {"branch": branch, "workflow_file": workflow_file, "dry_run": dry_run}

    if dry_run:
        _audit("trigger_pipeline", user, params, dry_run=True, status="DRY_RUN")
        return github_tools.trigger_pipeline(branch, workflow_file, dry_run=True)

    approved = await confirm_destructive_action(
        ctx,
        tool="trigger_pipeline",
        user=user.get("username"),
        action_description=f"Déclenchement du workflow CI sur la branche {branch}.",
        parameters=params,
    )
    if not approved:
        return f"Action REFUSÉE : pipeline {branch} non approuvé."
    _audit("trigger_pipeline", user, params, dry_run=False, status="EXECUTED")
    return github_tools.trigger_pipeline(branch, workflow_file, dry_run=False)


@mcp.tool()
def get_deployment_info(token: str) -> str:
    """Liste l'état des conteneurs Docker (déploiements en cours)."""
    user = _user(token)
    if not user:
        return "Accès refusé."
    _audit("get_deployment_info", user)
    return docker_tools.get_deployment_info()


@mcp.tool()
def get_container_logs(token: str, container_id: str, tail: int = 50) -> str:
    """Journalise les logs d'un conteneur avec filtrage automatique des secrets."""
    user = _user(token)
    if not user:
        return "Accès refusé."
    _audit("get_container_logs", user, {"container_id": container_id, "tail": tail})
    return docker_tools.get_container_logs(container_id, tail)


@mcp.tool()
async def rollback_deployment(
    token: str, image_tag: str, dry_run: bool = True, ctx: Context = None
) -> str:
    """*Retour arrière* : repositionne le déploiement sur une image antérieure.

    Validation humaine explicite requise dès que ``dry_run=False``.
    """
    user = _user(token)
    if not user:
        return "Accès refusé."
    if not has_role(user, "admin"):
        return "Erreur : Droits ADMIN requis pour un rollback."
    params = {"image_tag": image_tag, "dry_run": dry_run}

    if dry_run:
        _audit("rollback_deployment", user, params, dry_run=True, status="DRY_RUN")
        return docker_tools.rollback_deployment(image_tag, dry_run=True)

    approved = await confirm_destructive_action(
        ctx,
        tool="rollback_deployment",
        user=user.get("username"),
        action_description=f"Rollback du déploiement sur l'image {image_tag}.",
        parameters=params,
    )
    if not approved:
        return f"Action REFUSÉE : rollback vers {image_tag} non approuvé."
    _audit("rollback_deployment", user, params, dry_run=False, status="EXECUTED")
    return docker_tools.rollback_deployment(image_tag, dry_run=False)


@mcp.tool()
async def delete_docker_container(
    token: str, container_id: str, dry_run: bool = True, ctx: Context = None
) -> str:
    """*Action destructive* : supprime un conteneur Docker (rôle ADMIN + HITL).

    Args:
        token: Jeton d'accès Keycloak (OIDC).
        container_id: Identifiant ou nom du conteneur.
        dry_run: Si True (défaut), simule l'action sans effet système.
    """
    user = _user(token)
    if not user:
        _audit("delete_docker_container", None, {"container_id": container_id}, dry_run=dry_run, status="DENIED")
        return "Accès refusé."
    if not has_role(user, "admin"):
        _audit("delete_docker_container", user, {"container_id": container_id}, dry_run=dry_run, status="DENIED")
        return "Erreur : Droits ADMIN requis."
    params = {"container_id": container_id, "dry_run": dry_run}

    if dry_run:
        _audit("delete_docker_container", user, params, dry_run=True, status="DRY_RUN")
        return (
            f"[DRY-RUN] L'utilisateur {user['username']} supprimerait le "
            f"conteneur {container_id}."
        )

    approved = await confirm_destructive_action(
        ctx,
        tool="delete_docker_container",
        user=user.get("username"),
        action_description=f"Suppression du conteneur Docker {container_id}.",
        parameters=params,
    )
    if not approved:
        return f"Action REFUSÉE : suppression de {container_id} non approuvée."
    _audit("delete_docker_container", user, params, dry_run=False, status="EXECUTED")
    return docker_tools.delete_container(container_id)


# ============================================================
# GROUPE C — QUALITÉ & SÉCURITÉ
# ============================================================

@mcp.tool()
def run_tests(token: str, path: str = "tests") -> str:
    """Exécute la suite pytest et retourne le rapport succès/échec."""
    user = _user(token)
    if not user:
        return "Accès refusé."
    _audit("run_tests", user, {"path": path})
    return quality_tools.run_tests(path)


@mcp.tool()
def get_coverage(token: str, path: str = "tests") -> str:
    """Mesure le taux de couverture de code (pytest --cov)."""
    user = _user(token)
    if not user:
        return "Accès refusé."
    _audit("get_coverage", user, {"path": path})
    return quality_tools.get_coverage(path)


@mcp.tool()
def scan_vulnerabilities(token: str) -> str:
    """Lance un scan SAST Semgrep (critiques filtrées)."""
    user = _user(token)
    if not user:
        return "Accès refusé."
    _audit("scan_vulnerabilities", user)
    return run_semgrep_scan()


@mcp.tool()
def check_dependencies(token: str) -> str:
    """Audite les dépendances (pip-audit) et remonte les CVE."""
    user = _user(token)
    if not user:
        return "Accès refusé."
    _audit("check_dependencies", user)
    return run_pip_audit()


# ============================================================
# GROUPE D — GESTION DE PROJET & DOCUMENTATION
# ============================================================

@mcp.tool()
def list_issues(token: str, state: str = "open") -> str:
    """Liste les tickets (issues) du dépôt cible."""
    user = _user(token)
    if not user:
        return "Accès refusé."
    if state not in {"open", "closed", "all"}:
        return "Erreur : état invalide (open/closed/all)."
    _audit("list_issues", user, {"state": state})
    return github_tools.list_issues(state)


@mcp.tool()
def create_issue(token: str, title: str, body: str = "") -> str:
    """Crée un ticket sur le dépôt cible."""
    user = _user(token)
    if not user:
        return "Accès refusé."
    _audit("create_issue", user, {"title": title})
    return github_tools.create_issue(title, body)


@mcp.tool()
def generate_doc(token: str) -> str:
    """(IA) Génère une documentation Markdown depuis les docstrings."""
    user = _user(token)
    if not user:
        return "Accès refusé."
    _audit("generate_doc", user)
    return doc_tools.generate_doc()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="DevOps MCP Server (FastMCP 3.x)")
    parser.add_argument(
        "--transport",
        choices=["stdio", "http", "sse"],
        default=os.getenv("MCP_TRANSPORT", "stdio"),
        help="Transport MCP — stdio (défaut local) ou http (Streamable HTTP).",
    )
    parser.add_argument(
        "--host",
        default=os.getenv("FASTMCP_HOST", "127.0.0.1"),
        help="Hôte HTTP (défaut : 127.0.0.1).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("FASTMCP_PORT", "3000")),
        help="Port HTTP (défaut : 3000).",
    )
    args = parser.parse_args()

    if args.transport == "http":
        mcp.run(transport="http", host=args.host, port=args.port)
    else:
        mcp.run(transport=args.transport)