"""Lecteur du journal d'audit JSONL et calcul de statistiques."""

from __future__ import annotations

import json
import os
import time
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

load_dotenv()

_AUDIT_LOG = os.getenv("AUDIT_LOG_FILE", "audit.log")
_project_root = Path(__file__).resolve().parent.parent
_audit_path = _project_root / _AUDIT_LOG


def read_audit_log(limit: int | None = None) -> list[dict[str, Any]]:
    """Lit toutes les entrées du journal d'audit (JSONL)."""
    entries = []
    if not _audit_path.exists():
        return entries
    with open(_audit_path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    if limit:
        entries = entries[-limit:]
    return entries


def filter_entries(
    entries: list[dict],
    *,
    tool: str | None = None,
    user: str | None = None,
    verdict: str | None = None,
    status: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    search: str | None = None,
) -> list[dict]:
    """Filtre les entrées selon les critères donnés."""
    result = entries
    if tool:
        result = [e for e in result if e.get("tool") == tool]
    if user:
        result = [e for e in result if e.get("user") == user]
    if verdict:
        result = [e for e in result if e.get("verdict") == verdict]
    if status:
        result = [e for e in result if e.get("status") == status]
    if date_from:
        result = [e for e in result if e.get("timestamp", "") >= date_from]
    if date_to:
        result = [e for e in result if e.get("timestamp", "") <= date_to]
    if search:
        search_lower = search.lower()
        result = [
            e
            for e in result
            if search_lower in json.dumps(e, ensure_ascii=False).lower()
        ]
    return result


def compute_stats(entries: list[dict]) -> dict[str, Any]:
    """Calcule les statistiques agrégées pour le dashboard."""
    if not entries:
        return {
            "total": 0,
            "blocked": 0,
            "suspicious": 0,
            "safe": 0,
            "active_users": 0,
            "by_tool": {},
            "by_verdict": {},
            "by_status": {},
            "by_user": {},
            "by_day": [],
            "by_hour": [],
        }

    total = len(entries)
    verdicts = Counter(e.get("verdict", "UNKNOWN") for e in entries)
    statuses = Counter(e.get("status", "UNKNOWN") for e in entries)
    tools = Counter(e.get("tool", "unknown") for e in entries)
    users = Counter(e.get("user") or "anonymous" for e in entries)

    by_day: Counter = Counter()
    by_hour: Counter = Counter()
    for e in entries:
        ts = e.get("timestamp", "")
        if ts:
            day = ts[:10]
            by_day[day] += 1
            if len(ts) >= 13:
                hour = ts[11:13]
                by_hour[hour] += 1

    sorted_days = sorted(by_day.items())
    sorted_hours = [by_hour.get(f"{h:02d}", 0) for h in range(24)]

    return {
        "total": total,
        "blocked": verdicts.get("BLOCKED", 0),
        "suspicious": verdicts.get("SUSPICIOUS", 0),
        "safe": verdicts.get("SAFE", 0),
        "active_users": len([u for u in users if u != "anonymous"]),
        "by_tool": dict(tools.most_common()),
        "by_verdict": dict(verdicts),
        "by_status": dict(statuses),
        "by_user": dict(users.most_common()),
        "by_day": [{"date": d, "count": c} for d, c in sorted_days],
        "by_hour": [{"hour": f"{h:02d}:00", "count": sorted_hours[h]} for h in range(24)],
    }


def get_unique_values(entries: list[dict], field: str) -> list[str]:
    """Retourne les valeurs uniques pour un champ donné."""
    values = set()
    for e in entries:
        v = e.get(field)
        if v is not None:
            values.add(str(v))
    return sorted(values)


def tail_audit_log(last_ts: float = 0) -> list[dict]:
    """Retourne les entrées plus récentes que last_ts (pour SSE)."""
    entries = []
    if not _audit_path.exists():
        return entries
    with open(_audit_path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                if entry.get("ts", 0) > last_ts:
                    entries.append(entry)
            except json.JSONDecodeError:
                continue
    return entries
