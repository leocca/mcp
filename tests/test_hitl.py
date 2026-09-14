import pytest

from src.security.hitl import confirm_destructive_action

from unittest.mock import AsyncMock

from fastmcp.server.elicitation import (
    AcceptedElicitation,
    CancelledElicitation,
    DeclinedElicitation,
)


class _UnsupportedClient:
    """Client MCP sans support de l'élicitation (levee d'erreur)."""

    def __init__(self, error: Exception):
        self._error = error
        self.elicit = AsyncMock(side_effect=error)


class FakeCtx:
    def __init__(self, result):
        self.elicit = AsyncMock(return_value=result)


@pytest.mark.asyncio
async def test_approbation_explicite():
    ctx = FakeCtx(AcceptedElicitation(data="APPROVE"))
    ok = await confirm_destructive_action(
        ctx, tool="rollback", user="alice", action_description="Rollback prod"
    )
    assert ok is True


@pytest.mark.asyncio
async def test_refus_explicite():
    ctx = FakeCtx(AcceptedElicitation(data="DECLINE"))
    ok = await confirm_destructive_action(
        ctx, tool="rollback", user="alice", action_description="Rollback prod"
    )
    assert ok is False


@pytest.mark.asyncio
async def test_elicitation_declinee():
    ctx = FakeCtx(DeclinedElicitation())
    ok = await confirm_destructive_action(
        ctx, tool="rollback", user="alice", action_description="Rollback prod"
    )
    assert ok is False


@pytest.mark.asyncio
async def test_elicitation_annulee():
    ctx = FakeCtx(CancelledElicitation())
    ok = await confirm_destructive_action(
        ctx, tool="rollback", user="alice", action_description="Rollback prod"
    )
    assert ok is False


@pytest.mark.asyncio
async def test_fail_closed_sans_elicitation():
    """Si le client ne supporte pas l'élicitation, l'action est REFUSÉE."""
    ctx = _UnsupportedClient(RuntimeError("elicitation not supported"))
    ok = await confirm_destructive_action(
        ctx, tool="rollback", user="alice", action_description="Rollback prod"
    )
    assert ok is False


@pytest.mark.asyncio
async def test_approbation_autre_valeur_refusee():
    ctx = FakeCtx(AcceptedElicitation(data="MAYBE"))
    ok = await confirm_destructive_action(
        ctx, tool="rollback", user="alice", action_description="Rollback prod"
    )
    assert ok is False