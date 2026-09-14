"""Socle Human-In-The-Loop (HITL) et validation humaine explicite.

Exigence A.6 / B.4 : toute action à impact direct (marquée d'un astérisque)
exige une validation humaine explicite, et le ``destructiveHint`` seul ne
constitue pas une barrière suffisante.

Mécanique :
1. Un outil destructif est appelé avec ``dry_run=True`` par défaut : il
   SIMULE l'action et la journalise, sans aucun effet système.
2. Pour passer en mode réel, l'appelant fournit ``dry_run=False`` et le
   serveur déclenche une **élicitation** MCP : l'hôte interroge l'utilisateur
   (saisie directe) via ``ctx.elicit()``.
3. Verdict « fail-closed » : si la confirmation est refusée, annulée, ou si
   le client ne supporte pas l'élicitation, l'action est REFUSÉE et journalisée.
"""

from __future__ import annotations

from typing import Any

from fastmcp.server.context import Context
from fastmcp.server.elicitation import AcceptedElicitation, CancelledElicitation, DeclinedElicitation

from src.security.audit import audit_action

__all__ = ["CONSENT_OPTIONS", "confirm_destructive_action", "human_decision_from_elicit"]

# Réponse unique de l'utilisateur — pas de réponses libres qui pourraient
# elles-mêmes être instrumentées.
CONSENT_OPTIONS: list[str] = ["APPROVE", "DECLINE"]


async def confirm_destructive_action(
    ctx: Context,
    *,
    tool: str,
    user: str | None,
    action_description: str,
    parameters: dict[str, Any] | None = None,
) -> bool:
    """Demande et vérifie l'approbation humaine avant une action destructive.

    Args:
        ctx: Contexte FastMCP de l'appel (fournit l'élicitation).
        tool: Nom de l'outil appelé (pour l'audit).
        user: Utilisateur authentifié (pour l'audit).
        action_description: Description claire de l'action demandée.
        parameters: Arguments de l'action (pour l'audit, secrets occultés).

    Returns:
        ``True`` uniquement si l'utilisateur a explicitement approuvé via
        l'interface d'élicitation. Tous les autres cas (refus, annulation,
        client sans élicitation, erreur) retournent ``False``.
    """
    message = (
        f"[HITL - ACTION DESTRUCTIVE] L'action suivante va être exécutée en "
        f"mode RÉEL (dry_run désactivé) :\n{action_description}\n"
        f"Veuillez confirmer explicitement."
    )
    try:
        result = await ctx.elicit(
            message,
            CONSENT_OPTIONS,
            response_title="Validation humaine",
            response_description="APPROVE pour lancer l'action, DECLINE pour l'interdire.",
        )
    except Exception as exc:  # élicitation non supportée => fail-closed
        audit_action(
            tool, user, parameters,
            dry_run=False, verdict="SUSPICIOUS", status="BLOCKED",
            detail=f"Élicitation indisponible - action refusée ({type(exc).__name__})",
        )
        return False

    if isinstance(result, AcceptedElicitation):
        decision = result.data
        if decision == "APPROVE":
            audit_action(
                tool, user, parameters,
                dry_run=False, verdict="SAFE", status="APPROVED",
                detail=action_description,
            )
            return True
        audit_action(
            tool, user, parameters,
            dry_run=False, verdict="SAFE", status="DECLINED",
            detail=action_description,
        )
        return False

    if isinstance(result, CancelledElicitation):
        audit_action(
            tool, user, parameters,
            dry_run=False, verdict="SAFE", status="CANCELLED",
            detail=action_description,
        )
        return False

    if isinstance(result, DeclinedElicitation):
        audit_action(
            tool, user, parameters,
            dry_run=False, verdict="SAFE", status="DECLINED",
            detail=action_description,
        )
        return False

    audit_action(
        tool, user, parameters,
        dry_run=False, verdict="SUSPICIOUS", status="BLOCKED",
        detail="Réponse d'élicitation inattendue - action refusée",
    )
    return False


async def human_decision_from_elicit(
    ctx: Context,
    message: str,
    response_title: str | None = None,
) -> bool:
    """Abstraction générique : transforme une élicitation en oui/non.

    Prévu pour réutiliser l'élicitation sur d'autres points de décision
    (validation d'un déploiement, approbation d'un merge, etc.) sans
    réécrire la logique de gestion des résultats.
    """
    decision = await confirm_destructive_action(
        ctx,
        tool="generic",
        user=None,
        action_description=message,
        parameters={"message": message},
    )
    return decision