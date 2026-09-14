#!/usr/bin/env bash
# ----------------------------------------------------------------
# Démo MCP Inspector — Transport stdio (local)
# ----------------------------------------------------------------
# Usage :
#   bash scripts/demo_stdio.sh
#
# Prérequis : node/npm (pour npx), venv Python activé, Ollama en cours.
set -euo pipefail
cd "$(dirname "$0")/.."

echo "▸ Lancement du serveur MCP en stdio (Ctrl+C pour quitter) …"
exec npx -y @modelcontextprotocol/inspector \
  --transport stdio \
  python -m src.server
