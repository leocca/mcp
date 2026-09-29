"""Client MCP léger pour le dashboard — protocole Streamable HTTP (POST-only).

Étant donné un bug de compatibilité entre mcp 1.29.0 et FastMCP 3.4.7 sur le
transport streamable HTTP, ce module implémente le protocole MCP brut via httpx.
"""

from __future__ import annotations

import json
import os
import threading
import time
from typing import Any

import httpx

MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:3000/mcp")

_HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
    "MCP-Protocol-Version": "2025-11-25",
}

_pending_elicitations: dict[str, str] = {}
_elicit_lock = threading.Lock()


def pre_approve_elicitation(call_id: str, decision: str = "APPROVE") -> None:
    with _elicit_lock:
        _pending_elicitations[call_id] = decision


def pop_elicitation(call_id: str) -> str | None:
    with _elicit_lock:
        return _pending_elicitations.pop(call_id, None)


def _parse_sse_events(text: str) -> list[dict]:
    events: list[dict] = []
    for line in text.splitlines():
        if line.startswith("data: "):
            payload = line[6:]
            if payload.strip():
                try:
                    events.append(json.loads(payload))
                except json.JSONDecodeError:
                    pass
    return events


def _parse_event_stream(raw: str) -> tuple[list[dict], dict | None]:
    events = []
    elicitation_request = None
    for event in _parse_sse_events(raw):
        method = event.get("method")
        if method == "elicitation/create":
            elicitation_request = event
        elif "result" in event or "error" in event:
            events.append(event)
    return events, elicitation_request


def _post(
    client: httpx.Client,
    body: dict,
    session_id: str | None = None,
    auth_header: str | None = None,
) -> httpx.Response:
    headers = dict(_HEADERS)
    if session_id:
        headers["Mcp-Session-Id"] = session_id
    if auth_header:
        headers["Authorization"] = auth_header
    return client.post(MCP_SERVER_URL, json=body, headers=headers, timeout=30)


def _post_auth(
    client: httpx.Client,
    body: dict,
    access_token: str,
    session_id: str | None = None,
) -> httpx.Response:
    return _post(client, body, session_id=session_id, auth_header=f"Bearer {access_token}")


def _init_session(client: httpx.Client, access_token: str) -> str | None:
    body = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-11-25",
            "capabilities": {},
            "clientInfo": {"name": "dashboard", "version": "1.0.0"},
        },
    }
    r = _post_auth(client, body, access_token)
    if r.status_code != 200:
        raise ConnectionError(f"Initialize failed: {r.status_code} {r.text[:200]}")
    session_id = r.headers.get("mcp-session-id")
    notif = {"jsonrpc": "2.0", "method": "notifications/initialized"}
    _post_auth(client, notif, access_token, session_id=session_id)
    return session_id


def list_tools(access_token: str) -> list[dict]:
    """Récupère la liste des outils MCP exposés par le serveur."""
    with httpx.Client() as client:
        sid = _init_session(client, access_token)
        body = {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}
        r = _post_auth(client, body, access_token, session_id=sid)
        if r.status_code != 200:
            raise RuntimeError(f"tools/list failed: {r.status_code}")
        events, _ = _parse_event_stream(r.text)
        if not events:
            raise RuntimeError("No response from tools/list")
        result = events[0].get("result", {})
        return result.get("tools", [])


def call_tool(
    access_token: str,
    tool_name: str,
    arguments: dict[str, Any],
    call_id: str | None = None,
) -> dict[str, Any]:
    """Exécute un outil MCP et retourne le résultat.

    Le POST ``tools/call`` est lu en STREAM : lorsqu'une élicitation
    (``elicitation/create``) arrive dans le flux SSE, on y répond
    immédiatement (un autre POST portant le ``id`` de la requête), puis on
    continue de lire le même flux pour obtenir le résultat final.
    """
    cid = call_id or f"{tool_name}-{int(time.time())}"
    with httpx.Client() as client:
        sid = _init_session(client, access_token)
        body: dict[str, Any] = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": arguments},
        }
        events: list[dict] = []
        with client.stream(
            "POST", MCP_SERVER_URL, json=body,
            headers={
                **_HEADERS,
                "Mcp-Session-Id": sid,
                "Authorization": f"Bearer {access_token}",
            },
            timeout=60,
        ) as r:
            if r.status_code not in (200, 202):
                raise RuntimeError(f"tools/call failed: {r.status_code}")
            if r.status_code == 202:
                for text in r.iter_text():
                    events.extend(_parse_sse_events(text))
                return {
                    "isError": True,
                    "content": [{"type": "text", "text": "Accepted (async) — polling needed."}],
                }
            for line in r.iter_lines():
                if not line.startswith("data: "):
                    continue
                payload = line[6:].strip()
                if not payload:
                    continue
                try:
                    event = json.loads(payload)
                except json.JSONDecodeError:
                    continue
                method = event.get("method")
                if method == "elicitation/create":
                    decision: str = pop_elicitation(cid) or "DECLINE"
                    action = "accept" if decision == "APPROVE" else "decline"
                    _post_auth(
                        client,
                        {
                            "jsonrpc": "2.0",
                            "id": event.get("id", 0),
                            "result": {
                                "action": action,
                                "content": {"value": decision},
                            },
                        },
                        access_token,
                        session_id=sid,
                    )
                elif "result" in event or "error" in event:
                    events.append(event)
                    break
        if not events:
            return {
                "isError": True,
                "content": [{"type": "text", "text": "No response from server."}],
            }
        return events[0].get("result", {})
