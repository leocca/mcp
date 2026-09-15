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
        "10. Conclusion",
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
        "Image Python 3.10-slim, utilisateur non-root (mcp), point d'entrée stdio par défaut."
    )
    add_code_block(doc, """
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
""", "Dockerfile")

    doc.add_heading("7.2 Docker Compose", level=2)
    doc.add_paragraph("Stack de 3 services avec ordre de démarrage explicite :")
    services = [
        ("postgres", "PostgreSQL 15", "Aucune dépendance"),
        ("keycloak", "Keycloak (OIDC)", "Dépend de postgres"),
        ("mcp-server", "Serveur MCP (ce dépôt)", "Dépend de keycloak"),
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

# 4. Tests
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

    # ── 10. CONCLUSION ─────────────────────────────────────────────
    doc.add_heading("10. Conclusion", level=1)

    doc.add_heading("10.1 Récapitulatif", level=2)
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
    ]
    for item in recap:
        doc.add_paragraph(item, style="List Bullet")

    doc.add_heading("10.2 Perspectives", level=2)
    perspectives = [
        "Extension à d'autres fournisseurs CI/CD (GitLab CI, Jenkins)",
        "Intégration de modèles LLM supplémentaires (Gemma, Llama)",
        "Dashboard web pour le monitoring des actions auditées",
        "Système d'alertes temps réel pour les menaces de sécurité",
        "Pipeline d'intégration continue (GitHub Actions) pour le projet lui-même",
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
