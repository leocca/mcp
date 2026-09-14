"""Protection contre l'injection indirecte de prompt.

Tout contenu provenant de sources externes (README GitHub, titre/corps de
ticket, messages de commit, contenu d'issues, etc.) est considéré NON fiable
avant d'être transmis à un LLM ou d'influencer une action. Ce module détecte
les tentatives d'ingénierie de prompt et filtre les secrets des sorties.

Motifs typiques détectés (B.5 du cahier des charges) :
- « ignore tes instructions précédentes / ignore all previous instructions » ;
- « delete / rm -rf / destroy » visant une action destructive ;
- demandes d'exfiltration de tokens/clés ;
- usurpation du système (system prompt, acting as...).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

__all__ = ["GuardResult", "detect_prompt_injection", "is_external_content_safe", "redact_secrets"]

# Patrons d'ingénierie de prompt documentés. Chaque motif a un poids ; un
# score cumulé >= SEUIL bloque l'appel.
_INJECTION_PATTERNS: list[tuple[re.Pattern[str], int, str]] = [
    (re.compile(r"ignore\s+(all\s+)?(your\s+)?(previous|prior)\s+(instructions|prompt)", re.I), 3, "ignored_instructions"),
    (re.compile(r"ignore\s+(all\s+)?(above|précédentes|ci[-\s]dessus)", re.I), 3, "ignored_instructions"),
    (re.compile(r"disregard\s+previous", re.I), 3, "disregard_previous"),
    (re.compile(r"oublie\s+(tes|toutes)?\s*(les|'?s)?\s*(instructions|consignes)", re.I), 3, "ignored_instructions"),
    (re.compile(r"\b(delete|remove|kill|stop|shutdown|destroy|rollback)\b.{0,60}\b(container|server|service|deployment|pod|production)", re.I), 2, "destructive_orders"),
    (re.compile(r"rm\s+(-rf\s+)?[/~]", re.I), 3, "destructive_shell"),
    (re.compile(r"exfiltrat|leak.{0,30}(token|secret|api.key|password)", re.I), 3, "secret_exfil"),
    (re.compile(r"send.{0,30}(token|secret|api.key).{0,30}(to|à|at|http)", re.I), 3, "secret_exfil"),
    (re.compile(r"you are now|now you are\b|agis\s+comme\s+si\s+tu|assume the role|tu es maintenant|vous êtes maintenant", re.I), 2, "role_takeover"),
    (re.compile(r"system prompt|developer message", re.I), 1, "system_usurp"),
    (re.compile(r"déploie\s+sans\s+(validation|confirmation|approbation)", re.I), 3, "bypass_validation"),
    (re.compile(r"deploy\s+without\s+(validation|confirmation|approval)", re.I), 3, "bypass_validation"),
    (re.compile(r"always\s+allow|auto[\s-]?approve", re.I), 2, "auto_approve"),
]

# Score à partir duquel le contenu est considéré hostile.
_SEVERITY_THRESHOLDS = {
    "SAFE": 0,
    "SUSPICIOUS": 2,
    "BLOCKED": 3,
}

# Secrets à occulter dans les sorties d'outils avant transmission au LLM.
_SECRET_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"(?i)\b(ghp|gho|ghu|ghs|github_pat)_[A-Za-z0-9_]{10,}\b"),
    re.compile(r"(?i)(bearer)\s+[A-Za-z0-9._~+/=-]{20,}"),
    re.compile(r"(?i)\b[A-Za-z0-9+/]{40}==\b"),  # forme probable de secret encodé
    re.compile(r"(?i)password\s*[=:]\s*\S+"),
    re.compile(r"(?i)client[_-]?secret\s*[=:]\s*\S+"),
    re.compile(r"(?i)api[_-]?key\s*[=:]\s*\S+"),
    re.compile(r"(?i)token\s*[=:]\s*\S+"),
]


@dataclass(frozen=True, slots=True)
class GuardResult:
    """Résultat du contrôle d'innocuité d'un contenu externe."""

    safe: bool
    score: int
    severity: str
    hits: list[str] = field(default_factory=list)

    def __str__(self) -> str:  # pragma: no cover - utilitaire de debug
        return f"GuardResult(safe={self.safe}, score={self.score}, severity={self.severity}, hits={self.hits})"


def detect_prompt_injection(content: str | None) -> GuardResult:
    """Analyse un contenu externe et retourne un verdict d'innocuité.

    Args:
        content: Texte brut provenant d'une source non fiable (README, issue…).

    Returns:
        Un :class:`GuardResult` avec verdict ``safe`` (peut être transmis au
        LLM / aux outils) ou hostile (à bloquer ou à soumettre à validation).
    """
    if not content or not str(content).strip():
        return GuardResult(safe=True, score=0, severity="SAFE")

    text = str(content)
    total = 0
    hits: list[str] = []
    for pattern, weight, label in _INJECTION_PATTERNS:
        if pattern.search(text):
            total += weight
            hits.append(label)

    if total >= _SEVERITY_THRESHOLDS["BLOCKED"]:
        return GuardResult(safe=False, score=total, severity="BLOCKED", hits=hits)
    if total >= _SEVERITY_THRESHOLDS["SUSPICIOUS"]:
        return GuardResult(safe=False, score=total, severity="SUSPICIOUS", hits=hits)
    return GuardResult(safe=True, score=total, severity="SAFE", hits=hits)


def is_external_content_safe(content: str | None) -> bool:
    """Raccourci booléen : le contenu peut-il être consommé tel quel ?"""
    return detect_prompt_injection(content).safe


def redact_secrets(text: str | None) -> str:
    """Occulte les secrets potentiels avant transmission au LLM ou au journal.

    Garantit qu'aucune donnée d'authentification ne fuie côté modèle (B.5).
    """
    if not text:
        return ""
    redacted = str(text)
    for pattern in _SECRET_PATTERNS:
        redacted = pattern.sub("[REDACTED]", redacted)
    return redacted