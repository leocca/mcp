#!/usr/bin/env python3
"""Generate Word report for MCP DevOps Assistant project."""

from docx import Document
from docx.shared import Inches, Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.section import WD_ORIENT
from docx.oxml.ns import qn, nsdecls
from docx.oxml import parse_xml
import datetime


def set_cell_shading(cell, color):
    """Set cell background color."""
    shading_elm = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color}"/>')
    cell._tc.get_or_add_tcPr().append(shading_elm)


def add_styled_table(doc, headers, rows, col_widths=None):
    """Add a table with styled header."""
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER

    # Header
    for i, header in enumerate(headers):
        cell = table.rows[0].cells[i]
        cell.text = header
        set_cell_shading(cell, "1B4F72")
        for paragraph in cell.paragraphs:
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for run in paragraph.runs:
                run.font.color.rgb = RGBColor(255, 255, 255)
                run.font.bold = True
                run.font.size = Pt(10)

    # Data rows
    for row_idx, row_data in enumerate(rows):
        for col_idx, cell_text in enumerate(row_data):
            cell = table.rows[row_idx + 1].cells[col_idx]
            cell.text = str(cell_text)
            if row_idx % 2 == 0:
                set_cell_shading(cell, "EBF5FB")
            for paragraph in cell.paragraphs:
                for run in paragraph.runs:
                    run.font.size = Pt(9)

    if col_widths:
        for row in table.rows:
            for idx, width in enumerate(col_widths):
                row.cells[idx].width = Cm(width)

    return table


def add_code_block(doc, code, language=""):
    """Add a styled code block."""
    if language:
        p = doc.add_paragraph()
        run = p.add_run(f"  {language}")
        run.font.size = Pt(8)
        run.font.color.rgb = RGBColor(127, 127, 127)
        run.font.italic = True

    for line in code.strip().split("\n"):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.left_indent = Cm(1)
        run = p.add_run(line)
        run.font.name = "Courier New"
        run.font.size = Pt(8)
        run.font.color.rgb = RGBColor(44, 62, 80)


def create_report():
    doc = Document()

    # ── Styles ──────────────────────────────────────────────────────
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(11)
    style.paragraph_format.space_after = Pt(6)

    for level in range(1, 4):
        h_style = doc.styles[f"Heading {level}"]
        h_style.font.color.rgb = RGBColor(27, 79, 114)

    # ── PAGE DE GARDE ───────────────────────────────────────────────
    for _ in range(6):
        doc.add_paragraph()

    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title.add_run("DevOps Assistant")
    run.font.size = Pt(36)
    run.font.bold = True
    run.font.color.rgb = RGBColor(27, 79, 114)

    subtitle = doc.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = subtitle.add_run("Serveur MCP pour le DevOps")
    run.font.size = Pt(20)
    run.font.color.rgb = RGBColor(52, 152, 219)

    doc.add_paragraph()

    line = doc.add_paragraph()
    line.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = line.add_run("─" * 50)
    run.font.color.rgb = RGBColor(189, 195, 199)

    doc.add_paragraph()

    details = [
        ("Groupe 5", "Leonel, Djaffar, Junior, Aboubakry, Dieu Merci"),
        ("École", "Centrale des Logiciels Libres et de Télécommunications"),
        ("Date", "Septembre 2026"),
        ("Soutenance", "21 – 26 Septembre 2026"),
    ]

    for label, value in details:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(f"{label} : ")
        run.font.bold = True
        run.font.size = Pt(12)
        run = p.add_run(value)
        run.font.size = Pt(12)

    doc.add_page_break()

    # ── SOMMAIRE ────────────────────────────────────────────────────
    doc.add_heading("Sommaire", level=1)
    toc_items = [
        "1. Introduction",
        "2. Architecture Générale",
        "3. Stack Technique",
        "4. Les 19 Outils MCP",
        "5. Sécurité",
        "6. Ressources & Prompts",
        "7. Déploiement",
        "8. Tests",
        "9. Démonstration",
        "10. Dashboard Monitoring",
        "11. Conclusion",
    ]
    for item in toc_items:
        p = doc.add_paragraph(item)
        p.paragraph_format.space_before = Pt(4)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.left_indent = Cm(1)
        for run in p.runs:
            run.font.size = Pt(12)

    doc.add_page_break()

    # ── 1. INTRODUCTION ─────────────────────────────────────────────
    doc.add_heading("1. Introduction", level=1)

    doc.add_heading("1.1 Contexte", level=2)
    doc.add_paragraph(
        "Dans le domaine du DevOps, les équipes de développement manipulent quotidiennement "
        "un écosystème complexe d'outils : contrôle de version (Git), pipelines CI/CD (GitHub Actions), "
        "conteneurisation (Docker), analyse de sécurité (Semgrep), et gestion de la qualité du code "
        "(pytest). Cette fragmentation des outils engendre une perte de productivité et des risques "
        "de sécurité, notamment lors de la gestion manuelle des déploiements."
    )

    doc.add_heading("1.2 Problématique", level=2)
    doc.add_paragraph(
        "Comment concevoir un assistant intelligent capable d'orchestrer l'ensemble du cycle "
        "de vie DevOps — du code à la production — tout en intégrant des mécanismes de sécurité "
        "robustes contre les attaques par injection de prompts et en garantissant la validation "
        "humaine pour les actions destructrices ?"
    )

    doc.add_heading("1.3 Objectifs", level=2)
    objectives = [
        "Fournir un serveur MCP (Model Context Protocol) exposant 19 outils documentés pour le DevOps",
        "Sécuriser chaque interaction par validation stricte des entrées (anti-injection, RBAC)",
        "Implémenter un mécanisme HITL (Human-In-The-Loop) pour les actions destructrices",
        "Intégrer un LLM local (Ollama / Qwen 2.5) pour l'analyse intelligente du code",
        "Assurer la traçabilité complète via un journal d'audit structuré (JSON)",
        "Fournir un démonstrateur complet simulant un scénario DevOps réel",
    ]
    for obj in objectives:
        doc.add_paragraph(obj, style="List Bullet")

    doc.add_page_break()

    # ── 2. ARCHITECTURE GÉNÉRALE ───────────────────────────────────
    doc.add_heading("2. Architecture Générale", level=1)

    doc.add_paragraph(
        "L'application suit une architecture client-serveur basée sur le protocole MCP "
        "(Model Context Protocol) utilisant JSON-RPC 2.0. Le serveur expose ses capacités "
        "via un transport stdio (local) ou HTTP (distant)."
    )

    doc.add_heading("2.1 Schéma d'architecture", level=2)

    add_code_block(doc, """
┌─────────────────────┐   JSON-RPC 2.0   ┌──────────────────────────────┐   ┌─────────────────────┐
│   Client MCP        │ ◄──────────────► │      Serveur MCP             │──►│ GitHub REST/Actions │
│   • Ollama (LLM)    │   stdio / HTTP   │  FastMCP 3.x (Python 3.10+) │──►│ Docker Engine (SDK) │
│   • MCP Inspector   │                  │  19 outils, 7 ressources    │──►│ Semgrep, pip-audit  │
│   • Open WebUI      │                  │  RBAC + HITL + Audit        │──►│ pytest / coverage   │
└─────────────────────┘                  └──────────────────────────────┘   └─────────────────────┘
""")

    doc.add_heading("2.2 Composants principaux", level=2)
    components = [
        ("Transport", "stdio (local par défaut) ou Streamable HTTP pour l'accès distant"),
        ("Protocole", "JSON-RPC 2.0 — MCP spec Novembre 2025, noyau stateless"),
        ("Sécurité", "RBAC via Keycloak (JWT/OIDC), HITL (elicitation MCP), anti-injection"),
        ("Intelligence", "Ollama avec modèle Qwen 2.5 pour l'analyse de code"),
        ("Audit", "Journal structuré JSON avec traçabilité complète"),
    ]
    add_styled_table(doc, ["Composant", "Description"], components, [4, 12])

    doc.add_page_break()

    # ── 3. STACK TECHNIQUE ─────────────────────────────────────────
    doc.add_heading("3. Stack Technique", level=1)

    doc.add_heading("3.1 Technologies utilisées", level=2)
    stack = [
        ("Langage", "Python", "3.10+"),
        ("Framework MCP", "FastMCP", "3.4.7"),
        ("Protocole MCP", "mcp", "1.29.0"),
        ("Authentification", "Keycloak (OIDC)", "Latest"),
        ("Client Keycloak", "python-keycloak", "7.1.1"),
        ("VCS / CI", "PyGithub", "2.9.1"),
        ("Conteneurs", "Docker SDK", "7.2.0"),
        ("LLM Local", "Ollama", "0.6.2"),
        ("Modèle IA", "Qwen 2.5", "—"),
        ("SAST", "Semgrep", "1.173.0"),
        ("Audit Dépendances", "pip-audit", "2.10.1"),
        ("Tests", "pytest + pytest-cov", "9.1.1 / 7.1.0"),
        ("Logging", "Loguru", "0.7.3"),
        ("Base de données", "PostgreSQL", "15"),
        ("Dashboard Backend", "Flask", "3.0+"),
        ("OIDC Dashboard", "Authlib", "1.3+"),
        ("CSS Framework", "Bootstrap", "5.3.3"),
        ("Icônes", "Bootstrap Icons", "1.11.3"),
        ("Graphiques", "Chart.js", "4.4.4"),
        ("Temps Réel", "SSE (EventSource)", "—"),
        ("Templating", "Jinja2 (Flask)", "—"),
    ]
    add_styled_table(doc, ["Domaine", "Technologie", "Version"], stack, [4, 5, 3])

    doc.add_heading("3.2 Environnement de développement", level=2)
    dev_env = [
        ("Système d'exploitation", "Linux"),
        ("Gestionnaire de paquets", "pip + venv"),
        ("Conteneurisation", "Docker + Docker Compose v3.8"),
        ("Éditeur recommandé", "VS Code"),
    ]
    add_styled_table(doc, ["Outil", "Détail"], dev_env, [5, 8])

    doc.add_page_break()

    # ── 4. LES 19 OUTILS MCP ──────────────────────────────────────
    doc.add_heading("4. Les 19 Outils MCP", level=1)

    doc.add_paragraph(
        "Le serveur expose 19 outils regroupés en 4 catégories fonctionnelles. "
        "Chaque outil est documenté via un schéma JSON exportable."
    )

    doc.add_heading("4.1 Code & Git (6 outils)", level=2)
    git_tools = [
        ("git_status", "État actuel du dépôt cible", "—"),
        ("git_diff", "Différences d'un commit (SHA validé)", "—"),
        ("git_log", "Historique des commits récents", "—"),
        ("search_code", "Recherche locale dans le code (git grep)", "—"),
        ("analyze_pr", "Analyse LLM des bugs logiques dans une PR", "—"),
        ("suggest_review", "Recommandations de code review (LLM)", "—"),
    ]
    add_styled_table(doc, ["Outil", "Description", "HITL"], git_tools, [4, 9, 2])

    doc.add_heading("4.2 CI/CD & Déploiement (6 outils)", level=2)
    cicd_tools = [
        ("get_pipeline_status", "Statut des workflows GitHub Actions", "—"),
        ("trigger_pipeline", "Déclencher un workflow CI", "OUI"),
        ("get_deployment_info", "État des conteneurs Docker", "—"),
        ("get_container_logs", "Logs de conteneurs (secrets filtrés)", "—"),
        ("rollback_deployment", "Rollback vers une image précédente", "OUI + ADMIN"),
        ("delete_docker_container", "Supprimer un conteneur", "OUI + ADMIN"),
    ]
    add_styled_table(doc, ["Outil", "Description", "HITL"], cicd_tools, [4, 9, 3])

    doc.add_heading("4.3 Qualité & Sécurité (4 outils)", level=2)
    quality_tools = [
        ("run_tests", "Exécuter la suite pytest", "—"),
        ("get_coverage", "Taux de couverture du code", "—"),
        ("scan_vulnerabilities", "Scan SAST avec Semgrep", "—"),
        ("check_dependencies", "Vérification CVE avec pip-audit", "—"),
    ]
    add_styled_table(doc, ["Outil", "Description", "HITL"], quality_tools, [4, 9, 2])

    doc.add_heading("4.4 Projet & Documentation (3 outils)", level=2)
    project_tools = [
        ("list_issues", "Lister les tickets GitHub", "—"),
        ("create_issue", "Créer un ticket", "—"),
        ("generate_doc", "Génération de doc Markdown (IA)", "—"),
    ]
    add_styled_table(doc, ["Outil", "Description", "HITL"], project_tools, [4, 9, 2])

    doc.add_paragraph()
    p = doc.add_paragraph()
    run = p.add_run("Note : ")
    run.font.bold = True
    run = p.add_run(
        "Toutes les actions destructrices (marquées *) sont systématiquement soumises "
        "à une validation humaine explicite (MCP elicitation) précédée d'un dry_run. "
        "L'autorisation « toujours autoriser » est interdite (fail-closed)."
    )
    run.font.italic = True

    doc.add_page_break()

    # ── 5. SÉCURITÉ ────────────────────────────────────────────────
    doc.add_heading("5. Sécurité", level=1)

    doc.add_paragraph(
        "La sécurité est au cœur de l'architecture, avec 6 couches de protection complémentaires."
    )

    doc.add_heading("5.1 Human-In-The-Loop (HITL)", level=2)
    doc.add_paragraph(
        "Chaque outil destructeur interroge l'utilisateur via l'élicitation MCP "
        "(APPROVE / DECLINE). Si le client ne supporte pas l'élicitation, l'action est "
        "refusée (fail-closed)."
    )
    hitl_steps = [
        "1. L'outil destructeur est appelé avec dry_run=True par défaut",
        "2. En mode réel, le serveur déclenche une élicitation : ctx.elicit()",
        "3. L'utilisateur reçoit une demande de confirmation unique",
        "4. Verdict fail-closed : refus, annulation ou client sans élicitation → action REFUSÉE",
        "5. Les options de consentement sont uniquement ['APPROVE', 'DECLINE'] — pas de réponses libres",
    ]
    for step in hitl_steps:
        doc.add_paragraph(step, style="List Bullet")

    doc.add_heading("5.2 Anti-Injection de Prompts", level=2)
    doc.add_paragraph(
        "Le module guard.py analyse 11 familles de patterns (EN/FR) avant que tout contenu "
        "externe n'atteigne le LLM."
    )
    patterns = [
        ("ignored_instructions", "3", "\"ignore previous instructions\" EN/FR"),
        ("disregard_previous", "3", "\"disregard previous\" EN/FR"),
        ("destructive_orders", "2", "delete/remove/rollback ciblant containers/servers"),
        ("destructive_shell", "3", "rm -rf et commandes destructrices"),
        ("secret_exfil", "3", "Exfiltration de tokens/secrets"),
        ("role_takeover", "2", "\"you are now\", \"assume the role\""),
        ("system_usurp", "1", "\"system prompt\""),
        ("bypass_validation", "3", "\"deploy without validation\""),
        ("auto_approve", "2", "\"always allow\""),
    ]
    add_styled_table(doc, ["Pattern", "Poids", "Description"], patterns, [4, 2, 10])

    doc.add_paragraph()
    doc.add_paragraph("Seuils de sévérité : SAFE (score 0) / SUSPICIOUS (score 2) / BLOCKED (score ≥ 3)")

    doc.add_heading("5.3 Validation Stricte des Entrées", level=2)
    doc.add_paragraph(
        "Le module validation.py empêche l'injection de commandes et les parcours de répertoires."
    )
    validators = [
        ("validate_branch_name()", "Alphanumérique + ._- uniquement"),
        ("validate_git_sha()", "Hexadécimal, 7-64 caractères"),
        ("validate_image_tag()", "Format Docker tag"),
        ("validate_relative_path()", "Pas de .., pas de chemins absolus, pas de métacaractères shell"),
    ]
    add_styled_table(doc, ["Validateur", "Règle"], validators, [5, 11])

    doc.add_heading("5.4 RBAC — Contrôle d'Accès Basé sur les Rôles", level=2)
    doc.add_paragraph(
        "Vérification des tokens JWT via l'endpoint OIDC de Keycloak. "
        "Les outils sensibles (rollback, suppression) requièrent le rôle ADMIN."
    )

    doc.add_heading("5.5 Filtrage des Secrets", level=2)
    doc.add_paragraph("Patterns détectés et remplacés par [REDACTED] :")
    secret_patterns = [
        "GitHub PAT (ghp_, gho_, ghu_, ghs_, github_pat_)",
        "Bearer tokens",
        "Tokens Base64 encodés",
        "Motifs password=, client_secret=, api_key=, token=",
    ]
    for pattern in secret_patterns:
        doc.add_paragraph(pattern, style="List Bullet")

    doc.add_heading("5.6 Journal d'Audit", level=2)
    doc.add_paragraph(
        "Chaque exécution est tracée dans audit.log (JSON) avec : timestamp, outil, utilisateur, "
        "paramètres (filtrés), dry_run, verdict, statut, détail."
    )

    doc.add_page_break()

    # ── 6. RESSOURCES & PROMPTS ────────────────────────────────────
    doc.add_heading("6. Ressources & Prompts", level=1)

    doc.add_heading("6.1 Les 7 Ressources (lecture seule)", level=2)
    resources = [
        ("devops://git/status", "État actuel du dépôt cible"),
        ("devops://git/log", "Historique des commits récents"),
        ("devops://pipeline/latest", "Derniers workflows GitHub Actions"),
        ("devops://containers", "État des conteneurs Docker"),
        ("devops://security/findings", "Dernières vulnérabilités Semgrep"),
        ("devops://git/diff/{commit_sha}", "Différences d'un commit (template, SHA validé)"),
        ("devops://repo/file/{path}", "Contenu d'un fichier (template, path validé)"),
    ]
    add_styled_table(doc, ["URI", "Description"], resources, [6, 10])

    doc.add_heading("6.2 Les 4 Prompts (templates)", level=2)
    prompts = [
        ("review_pr(pr_id)", "Code review d'une PR du dépôt cible"),
        ("audit_predeploy()", "Checklist de sécurité avant déploiement"),
        ("incident_triage(branch)", "Triage d'incident CI/CD"),
        ("generate_documentation()", "Génération de documentation depuis les docstrings"),
    ]
    add_styled_table(doc, ["Prompt", "Usage"], prompts, [5, 11])

    doc.add_page_break()

    # ── 7. DÉPLOIEMENT ─────────────────────────────────────────────
    doc.add_heading("7. Déploiement", level=1)

    doc.add_heading("7.1 Dockerfile", level=2)
    doc.add_paragraph(
        "Deux images Docker : le serveur MCP (Python 3.10-slim, utilisateur non-root 'mcp') "
        "et le dashboard (Python 3.10-slim, utilisateur non-root 'dash')."
    )
    add_code_block(doc, """
# Serveur MCP
FROM python:3.10-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends git
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ src/
ENV PYTHONPATH=/app
RUN groupadd -r mcp && useradd -r -g mcp mcp
USER mcp
EXPOSE 3000
ENTRYPOINT ["python", "-m", "src.server"]

# Dashboard
FROM python:3.10-slim
WORKDIR /app
COPY dashboard/requirements.txt ./dashboard/requirements.txt
RUN pip install --no-cache-dir -r dashboard/requirements.txt
COPY dashboard/ dashboard/
COPY audit.log /data/audit.log
ENV PYTHONPATH=/app
ENV AUDIT_LOG_FILE=/data/audit.log
RUN groupadd -r dash && useradd -r -g dash dash
USER dash
EXPOSE 5000
CMD ["python", "-m", "dashboard.app"]
""", "Dockerfile / Dockerfile.dashboard")

    doc.add_heading("7.2 Docker Compose", level=2)
    doc.add_paragraph("Stack de 4 services avec ordre de démarrage explicite :")
    services = [
        ("postgres", "PostgreSQL 15", "Aucune dépendance"),
        ("keycloak", "Keycloak (OIDC)", "Dépend de postgres"),
        ("mcp-server", "Serveur MCP (ce dépôt)", "Dépend de keycloak"),
        ("dashboard", "Flask Dashboard", "Dépend de keycloak"),
    ]
    add_styled_table(doc, ["Service", "Image", "Dépendances"], services, [3, 5, 5])

    doc.add_heading("7.3 Variables d'environnement", level=2)
    env_vars = [
        ("KEYCLOAK_URL", "URL du serveur Keycloak"),
        ("KEYCLOAK_REALM", "Realm OIDC"),
        ("KEYCLOAK_CLIENT_ID", "ID client MCP server"),
        ("KEYCLOAK_CLIENT_SECRET", "Secret client"),
        ("JWT_SECRET", "Secret de signature JWT"),
        ("GITHUB_TOKEN", "PAT GitHub (repo + workflow)"),
        ("TARGET_REPOSITORY", "Slug du dépôt (owner/repo)"),
        ("LLM_MODEL", "Modèle Ollama (qwen2.5)"),
        ("MCP_TRANSPORT", "Mode transport (stdio/http)"),
        ("FASTMCP_HOST / PORT", "Adresse d'écoute HTTP"),
        ("FLASK_APP", "Point d'entrée Flask (dashboard/app.py)"),
        ("FLASK_SECRET_KEY", "Clé secrète Flask (32 caractères)"),
        ("DASHBOARD_CLIENT_ID", "ID client Keycloak du dashboard"),
        ("DASHBOARD_CLIENT_SECRET", "Secret client du dashboard"),
        ("DASHBOARD_REDIRECT_URI", "URI de callback OIDC du dashboard"),
        ("DASHBOARD_PORT", "Port du dashboard (5000)"),
        ("AUDIT_LOG_FILE", "Chemin vers le fichier audit.log"),
    ]
    add_styled_table(doc, ["Variable", "Description"], env_vars, [5, 11])

    doc.add_heading("7.4 Ordre de démarrage", level=2)
    add_code_block(doc, """
# 1. Infrastructure
docker compose up -d postgres keycloak
sleep 10

# 2. LLM local
ollama pull qwen2.5
ollama serve &

# 3. Serveur MCP
python -m src.server --transport http --port 3000

# 4. Dashboard
python -m dashboard.app   # Port 5000

# 5. Tests
python -m pytest tests/ -v
""", "Shell")

    doc.add_page_break()

    # ── 8. TESTS ────────────────────────────────────────────────────
    doc.add_heading("8. Tests", level=1)

    doc.add_paragraph(
        "La suite de tests comprend 53 tests répartis en 5 fichiers, couvrant tous les "
        "modules de l'application."
    )

    doc.add_heading("8.1 Structure des tests", level=2)
    test_files = [
        ("tests/test_tools.py", "13", "Git, GitHub, Docker, Qualité"),
        ("tests/test_guard.py", "12", "Détection injection, filtrage secrets"),
        ("tests/test_validation.py", "12", "Validation SHA, branche, chemin, tag"),
        ("tests/test_primitives.py", "8", "Ressources + prompts (async)"),
        ("tests/test_hitl.py", "7", "Élicitation HITL (async)"),
    ]
    add_styled_table(doc, ["Fichier", "Nb Tests", "Couverture"], test_files, [5, 3, 8])

    doc.add_heading("8.2 Exécution", level=2)
    add_code_block(doc, """
# Tests unitaires
python -m pytest tests/ -v

# Tests avec couverture
python -m pytest --cov --cov-report=term-missing -q tests/

# Tests individuels (debug)
python src/test_auth.py      # Vérifie Keycloak
python src/test_ai.py        # Vérifie Ollama
""", "Shell")

    doc.add_heading("8.3 Catégories de tests", level=2)
    test_categories = [
        ("Outils Git", "Appels git_diff, rejet SHA invalide, injection search, recherche valide"),
        ("Suggest Review", "PR propre analysée, PR empoisonnée bloquée"),
        ("Pipeline", "Simulation dry_run, rejet branche invalide"),
        ("Qualité", "Exécution tests, vérification dépendances, rejet chemin invalide"),
        ("Docker", "Aucun conteneur, filtrage logs, rollback dry_run"),
        ("Guard", "8 tests injection EN/FR, détection exfiltration, bypass validation"),
        ("Redaction", "Token GitHub, Bearer, clé=valeur, texte brut"),
        ("Validation", "Branche valide/invalide, SHA valide/invalide, tag, chemin"),
        ("Ressources", "Enregistrement, lecture, templates, rejet SHA invalide"),
        ("Prompts", "Enregistrement, rendu audit_predeploy, review_pr, incident_triage"),
        ("HITL", "Approbation, déclin, fail-closed sans élicitation"),
    ]
    add_styled_table(doc, ["Catégorie", "Tests"], test_categories, [4, 12])

    doc.add_page_break()

    # ── 9. DÉMONSTRATION ───────────────────────────────────────────
    doc.add_heading("9. Démonstration", level=1)

    doc.add_paragraph(
        "Le script scripts/demo_live.py implémente un scénario complet en 7 phases, "
        "démontrant toutes les capacités du serveur."
    )

    doc.add_heading("9.1 Les 7 phases du démo", level=2)
    phases = [
        ("Phase 0", "Setup", "Création du mini-projet buggé (calculateur de panier Flask)"),
        ("Phase 1", "Échec CI", "run_tests() retourne RED — le test échoue"),
        ("Phase 2", "Analyse", "git_log() + git_diff() isolent le bug (au lieu de +, c'est -)"),
        ("Phase 3", "Correction", "Commit du code corrigé, tests GREEN + couverture mesurée"),
        ("Phase 4", "Audit sécurité", "Scan Semgrep + vérification pip-audit des dépendances"),
        ("Phase 5", "Déploiement", "get_deployment_info() + trigger_pipeline() avec HITL APPROVE"),
        ("Phase 6", "Rollback", "HITL DECLINE démontrant le comportement fail-closed"),
        ("Phase 7", "Attaque simulée", "Ticket empoisonné attrapé par guard.py → BLOCKED"),
    ]
    add_styled_table(doc, ["Phase", "Étape", "Description"], phases, [2, 4, 10])

    doc.add_heading("9.2 Lancement", level=2)
    add_code_block(doc, """
# Mode interactif (pour présentation)
python scripts/demo_live.py

# Mode automatique (pour CI / vérification rapide)
python scripts/demo_live.py --auto

# Serveur HTTP + MCP Inspector (navigateur)
bash scripts/demo_http.sh
""", "Shell")

    doc.add_heading("9.3 Entrée d'audit (exemple)", level=2)
    add_code_block(doc, """{
  "timestamp": "2026-09-14T10:44:59+0000",
  "tool": "delete_docker_container",
  "user": "alice",
  "params": "{\\"container_id\\": \\"web01\\", \\"dry_run\\": true}",
  "dry_run": true,
  "verdict": "SAFE",
  "status": "DRY_RUN"
}""", "JSON")

    doc.add_page_break()

    # ── 10. DASHBOARD MONITORING ─────────────────────────────────
    doc.add_heading("10. Dashboard Monitoring", level=1)

    doc.add_paragraph(
        "Le projet intègre un dashboard web de monitoring en temps réel pour visualiser "
        "les actions auditées du serveur MCP. Cette interface full-stack est construite avec "
        "Flask (backend) et Bootstrap 5 + Chart.js (frontend), connectée au journal d'audit "
        "via des Server-Sent Events (SSE)."
    )

    doc.add_heading("10.1 Stack Technique Frontend", level=2)
    frontend_stack = [
        ("Framework Backend", "Flask 3.0+", "Routing, sessions, templating Jinja2"),
        ("Auth OIDC", "Authlib 1.3+", "Connexion Keycloak (authorization code flow)"),
        ("CSS Framework", "Bootstrap 5.3.3", "Grille responsive, composants UI, thème sombre"),
        ("Icônes", "Bootstrap Icons 1.11.3", "Iconographie vectorielle (CDN)"),
        ("Graphiques", "Chart.js 4.4.4", "4 types : line, doughnut, bar, horizontal bar"),
        ("JavaScript", "Vanilla JS (ES6 strict)", "IIFE, aucune dépendance npm, sans bundler"),
        ("Temps Réel", "Server-Sent Events", "EventSource natif, reconnexion auto 3s"),
        ("Templating", "Jinja2", "SSR côté Flask, blocks hérités"),
        ("Notifications", "Bootstrap Toast", "Alertes temps réel (BLOCKED / SUSPICIOUS)"),
    ]
    add_styled_table(doc, ["Composant", "Technologie", "Détails"], frontend_stack, [4, 4, 8])

    doc.add_heading("10.2 Architecture du Dashboard", level=2)
    doc.add_paragraph(
        "Le dashboard suit une architecture client-serveur classique avec rendu côté serveur "
        "(SSR) et mises à jour en temps réel via SSE. Le flux de données est le suivant :"
    )

    add_code_block(doc, """
┌───────────────────┐     HTTP / SSE      ┌──────────────────┐     JSONL     ┌──────────────┐
│  Navigateur       │ ◄─────────────────► │  Flask (app.py)  │ ◄────────────►│  audit.log   │
│  Bootstrap 5.3    │    Jinja2 + API     │  Port 5000       │  pollling 1s  │  (JSONL)     │
│  Chart.js 4.4     │                     │                  │               └──────────────┘
│  Vanilla JS       │                     │  Routes:         │
│  EventSource      │                     │  / (dashboard)   │     OIDC      ┌──────────────┐
│                   │                     │  /timeline       │ ◄────────────►│  Keycloak    │
│  sse.js           │                     │  /api/stats      │               │  Port 8080   │
│  dashboard.js     │                     │  /api/entries    │               └──────────────┘
│  timeline.js      │                     │  /api/events SSE │
└───────────────────┘                     │  /auth/*         │
                                          └──────────────────┘""")

    doc.add_heading("10.3 Structure des Fichiers", level=2)
    files = [
        ("dashboard/app.py", "263", "Application Flask, routes, API, SSE, watcher daemon"),
        ("dashboard/auth.py", "55", "Connexion OIDC Keycloak (Authlib)"),
        ("dashboard/audit_reader.py", "154", "Lecture JSONL, filtrage, statistiques, tail SSE"),
        ("dashboard/templates/base.html", "72", "Layout sidebar + contenu principal (Jinja2)"),
        ("dashboard/templates/login.html", "30", "Page de connexion Keycloak (autonome)"),
        ("dashboard/templates/dashboard.html", "152", "Vue globale : KPI, graphiques, utilisateurs actifs"),
        ("dashboard/templates/timeline.html", "119", "Timeline filtrable et paginée des audits"),
        ("dashboard/static/css/style.css", "112", "Overrides CSS thème sombre + print"),
        ("dashboard/static/js/sse.js", "73", "Client SSE, toasts, event bus (CustomEvent)"),
        ("dashboard/static/js/dashboard.js", "171", "Chart.js, KPI, filtre temporel, refresh auto"),
        ("dashboard/static/js/timeline.js", "163", "Pagination, filtres, modal détail, XSS protection"),
        ("dashboard/mcp_client.py", "200", "Client MCP Streamable HTTP brut (httpx, streaming SSE + élicitation)"),
        ("dashboard/templates/tools.html", "150", "Console MCP : formulaire dynamique + carte HITL"),
        ("dashboard/static/js/tools.js", "225", "Sélecteur d'outils, dry_run auto, approbation HITL"),
    ]
    add_styled_table(doc, ["Fichier", "Lignes", "Rôle"], files, [5, 2, 9])

    doc.add_heading("10.4 Pages et Fonctionnalités", level=2)

    doc.add_heading("10.4.1 Page Dashboard (/)", level=3)
    doc.add_paragraph(
        "Page d'accueil offrant une vue d'ensemble des actions auditées. Elle comprend :"
    )
    dashboard_features = [
        "Filtres temporels rapides : 24h, 7 jours, 30 jours, Tout",
        "4 cartes KPI : Total audité, BLOCKED, SUSPICIOUS, Utilisateurs actifs",
        "Graphique activité quotidienne (line chart avec area fill)",
        "Répartition des verdicts (doughnut chart : SAFE/SUSPICIOUS/BLOCKED)",
        "Top 10 des outils utilisés (barre horizontale)",
        "Activité par heure de la journée (barres verticales, 24 buckets)",
        "Tableau des utilisateurs actifs avec barres de progression",
        "Export JSON/CSV des données filtrées",
    ]
    for feature in dashboard_features:
        doc.add_paragraph(feature, style="List Bullet")

    doc.add_heading("10.4.2 Page Timeline (/timeline)", level=3)
    doc.add_paragraph(
        "Vue détaillée et filtrable du journal d'audit complet :"
    )
    timeline_features = [
        "Filtres avancés : outil, utilisateur, verdict, statut, plage de dates, recherche texte",
        "Pagination côté serveur (25/50/100 par page)",
        "Badges colorés DRY/LIVE, verdict et statut",
        "Modal de détail avec métadonnées et paramètres complets",
        "Protection XSS via fonction esc() (DOM-based escaping)",
        "Export CSV/JSON avec filtres appliqués",
        "Formatage français (toLocaleString('fr-FR'))",
    ]
    for feature in timeline_features:
        doc.add_paragraph(feature, style="List Bullet")

    doc.add_heading("10.5 Temps Réel — Server-Sent Events", level=2)
    doc.add_paragraph(
        "Le dashboard reçoit les nouvelles entrées d'audit en temps réel via SSE, "
        "complété par un rafraîchissement périodique de 30 secondes en cas de déconnexion."
    )

    sse_steps = [
        "1. Un thread daemon poll audit.log toutes les secondes",
        "2. Les nouvelles entrées sont broadcastées aux clients via queue/thread-safe",
        "3. Le navigateur (EventSource) reçoit les événements JSON",
        "4. Les verdicts BLOCKED/SUSPICIOUS déclenchent des toast notifications",
        "5. Un CustomEvent('audit:new') notifie dashboard.js et timeline.js pour refresh",
        "6. Reconnexion automatique avec backoff de 3 secondes en cas d'erreur",
    ]
    for step in sse_steps:
        doc.add_paragraph(step, style="List Bullet")

    doc.add_heading("10.6 Authentification OIDC", level=2)
    doc.add_paragraph(
        "Le dashboard utilise un flux OIDC authorization code via Keycloak, séparé du client "
        "MCP. L'authentification est gérée par Authlib avec découverte automatique des "
        "endpoints via /.well-known/openid-configuration."
    )

    auth_flow = [
        "1. L'utilisateur accède à / → redirigé vers /login si non authentifié",
        "2. Clic sur 'Se connecter avec Keycloak' → /auth/start",
        "3. Redirection vers Keycloak (port 8080) pour l'authentification",
        "4. Callback OIDC → extraction du token userinfo (username, email, roles)",
        "5. Stockage en session Flask (cookie signé) → accès aux pages protégées",
    ]
    for step in auth_flow:
        doc.add_paragraph(step, style="List Bullet")

    doc.add_heading("10.7 Design UI", level=2)
    doc.add_paragraph(
        "Le dashboard utilise un thème sombre cohérent avec le dark mode Bootstrap :"
    )
    design_items = [
        ("Fond principal", "#212529 (Bootstrap dark)"),
        ("Cartes / Sidebar", "#212529, bordure #343a40"),
        ("Texte", "Blanc (#fff), muted (#adb5bd)"),
        ("Accent", "Bleu Bootstrap #0d6efd"),
        ("Danger", "Rouge #dc3545 (BLOCKED)"),
        ("Warning", "Jaune #ffc107 (SUSPICIOUS)"),
        ("Success", "Vert #198754 (SAFE)"),
        ("Info", "Cyan #0dcaf0"),
        ("Impression", "Fond blanc, texte noir, sidebar masquée"),
    ]
    add_styled_table(doc, ["Élément", "Valeur"], design_items, [4, 12])

    doc.add_heading("10.8 Console MCP (exécution d'outils)", level=2)
    doc.add_paragraph(
        "La page /tools transforme le dashboard en console d'exécution : l'utilisateur "
        "connecté liste les 19 outils exposés par le serveur MCP, renseigne les paramètres "
        "via un formulaire généré dynamiquement depuis l'inputSchema, et exécute l'action. "
        "La présence d'élémentations (HITL) rend la console sûre pour la vraie exploitation : "
        "toute action destructive est d'abord simulée, puis soumise à validation humaine."
    )

    doc.add_heading("10.8.1 Client MCP maison (mcp_client.py)", level=3)
    doc.add_paragraph(
        "Le SDK officiel mcp 1.29.0 (transport streamable HTTP) est incompatible avec le "
        "serveur FastMCP 3.4.7 (erreurs 400 sur POST, 404 sur le GET SSE). Un client léger "
        "a donc été implémenté en protocole brut via httpx :"
    )
    mcp_client_items = [
        "initialize POST → capture du header mcp-session-id, puis notifications/initialized",
        "tools/list → rendu de la liste, du schéma et des annotations (destructiveHint)",
        "tools/call en STREAM pour lire le flux SSE incrémentalement",
        "Élication : lorsqu'un event elicitation/create arrive dans le flux (mode form, JSON-RPC id), le client y répond immédiatement par un second POST portant le même id et la décision (approve/decline) — évite le blocage du serveur qui attend la réponse avant de clore le flux",
        "Réinjection du token Keycloak en argument token de chaque appel (validation RBAC côté serveur)",
    ]
    for item in mcp_client_items:
        doc.add_paragraph(item, style="List Bullet")

    doc.add_heading("10.8.2 Flux de validation HITL", level=3)
    hitl_flow = [
        "1. Premier clic « Exécuter » : le JS force toujours dry_run=True → l'outil SIMULE l'action et journalise DRY_RUN, sans effet système",
        "2. Pour un outil marqué destructif, une carte « Validation humaine » (APPROUVER / DÉCLINER) apparaît sous le formulaire",
        "3. APPROUVER : ré-exécution avec dry_run=False + preApprove → le serveur déclenche l'élicitation MCP",
        "4. Le client répond APPROVE (JSON-RPC) ; le serveur exécute l'action, journalise APPROVED puis EXECUTED",
        "5. DÉCLINER ou absence d'approbation : fail-closed → action REFUSÉE, audit status DECLINED/BLOCKED",
    ]
    for step in hitl_flow:
        doc.add_paragraph(step, style="List Bullet")

    doc.add_heading("10.8.3 Déploiement", level=3)
    doc.add_paragraph(
        "En docker-compose, le serveur MCP écoute en transport HTTP sur 0.0.0.0:3000 "
        "(variables MCP_TRANSPORT, FASTMCP_HOST, FASTMCP_PORT) et le dashboard lit "
        "MCP_SERVER_URL=http://mcp-server:3000/mcp. Le dashboard monte audit.log en lecture "
        "et s'authentifie auprès de Keycloak via host.docker.internal pour joindre l'hôte "
        "(KEYCLOAK_URL interne ≠ URL publique du navigateur)."
    )

    doc.add_page_break()

    # ── 11. CONCLUSION ─────────────────────────────────────────────
    doc.add_heading("11. Conclusion", level=1)

    doc.add_heading("11.1 Récapitulatif", level=2)
    doc.add_paragraph(
        "Le projet DevOps Assistant MCP Server constitue une solution complète et sécurisée "
        "pour l'orchestration du cycle de vie DevOps. Les points forts sont :"
    )
    recap = [
        "19 outils documentés couvrant Git, CI/CD, qualité, sécurité et documentation",
        "Architecture multi-couches de sécurité (6 niveaux de protection)",
        "Mécanisme HITL fail-closed garantissant la validation humaine",
        "Protection contre les attaques par injection de prompts (11 familles de patterns)",
        "Traçabilité complète via journal d'audit structuré JSON",
        "Intégration d'un LLM local pour l'analyse intelligente du code",
        "Suite de tests complète (53 tests) avec couverture de code",
        "Déploiement conteneurisé avec Docker Compose",
        "Dashboard web de monitoring en temps réel (Flask + Bootstrap + SSE)",
    ]
    for item in recap:
        doc.add_paragraph(item, style="List Bullet")

    doc.add_heading("11.2 Perspectives", level=2)
    perspectives = [
        "Extension à d'autres fournisseurs CI/CD (GitLab CI, Jenkins)",
        "Intégration de modèles LLM supplémentaires (Gemma, Llama)",
        "Système d'alertes temps réel pour les menaces de sécurité",
        "Pipeline d'intégration continue (GitHub Actions) pour le projet lui-même",
        "Export des rapports en PDF directement depuis le dashboard",
    ]
    for item in perspectives:
        doc.add_paragraph(item, style="List Bullet")

    doc.add_paragraph()
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run("— Fin du rapport —")
    run.font.italic = True
    run.font.color.rgb = RGBColor(127, 127, 127)

    # ── Sauvegarde ─────────────────────────────────────────────────
    output_path = "rapport_projet.docx"
    doc.save(output_path)
    print(f"Rapport généré : {output_path}")


if __name__ == "__main__":
    create_report()
