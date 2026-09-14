"""Journal d'audit structuré (JSON) de toutes les exécutions d'outils.

Exigence A.6 du cahier des charges : « toutes les actions alimentent un
journal d'audit ». Chaque invocation d'outil est tracée avec l'acteur, les
paramètres (secrets occultés), le verdict sécurité et le résultat.
"""

from __future__ import annotations

import json
import os
import time
from typing import Any

from loguru import logger

from src.security.guard import redact_secrets

__all__ = ["audit_action", "get_audit_logger"]

_AUDIT_SINK = os.getenv("AUDIT_LOG_FILE", "audit.log")


def get_audit_logger():
    """Retourne le logger Loguru configuré pour l'audit (format JSON)."""
    audit = logger.bind(audit=True)
    return audit


def audit_action(
    tool: str,
    user: str | None,
    parameters: dict[str, Any] | None,
    *,
    dry_run: bool = True,
    verdict: str = "SAFE",
    status: str = "OK",
    detail: str | None = None,
) -> None:
    """Trace une exécution d'outil dans le journal d'audit.

    Args:
        tool: Nom de l'outil MCP exécuté.
        user: Identifiant de l'utilisateur authentifié (``None`` si anonyme).
        parameters: Arguments reçus par l'outil (secrets occultés avant trace).
        dry_run: ``True`` si l'action a été simulée (aucun effet système).
        verdict: Verdict du contrôle de sécurité (SAFE / SUSPICIOUS / BLOCKED).
        status: Résultat (OK / BLOCKED / DECLINED / CANCELLED / ERROR).
        detail: Informations complémentaires (ex. motif de blocage).
    """
    record = {
        "ts": time.time(),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "tool": tool,
        "user": user,
        "params": redact_secrets(json.dumps(parameters, ensure_ascii=False, default=str))
        if parameters
        else None,
        "dry_run": dry_run,
        "verdict": verdict,
        "status": status,
        "detail": detail,
    }
    try:
        get_audit_logger().info("audit", extra={"audit": record})
        with open(_AUDIT_SINK, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception:  # pragma: no cover - l'audit ne doit jamais faire tomber l'outil
        logger.opt(exception=True).error("Échec de l'écriture du journal d'audit")