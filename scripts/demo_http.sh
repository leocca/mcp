#!/usr/bin/env bash
# ----------------------------------------------------------------
# Démo MCP Inspector — Transport Streamable HTTP (port 3000)
# ----------------------------------------------------------------
# Usage :
#   bash scripts/demo_http.sh
#
# Prérequis : venv Python activé, Ollama en cours, port 3000 libre.
set -euo pipefail
cd "$(dirname "$0")/.."

PORT="${FASTMCP_PORT:-3000}"
HOST="${FASTMCP_HOST:-127.0.0.1}"

cleanup() {
  echo -e "\n▸ Arrêt du serveur MCP (PID $SERVER_PID) …"
  kill "$SERVER_PID" 2>/dev/null || true
  wait "$SERVER_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo "▸ Démarrage du serveur MCP sur http://${HOST}:${PORT} …"
python -m src.server --transport http --host "$HOST" --port "$PORT" &
SERVER_PID=$!
sleep 2

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  Serveur MCP prêt : http://${HOST}:${PORT}                  ║"
echo "║                                                            ║"
echo "║  1. Ouvrir MCP Inspector (navigateur) :                    ║"
echo "║     npx -y @modelcontextprotocol/inspector                 ║"
echo "║                                                            ║"
echo "║  2. Connexion :                                            ║"
echo "║     URL : http://${HOST}:${PORT}                           ║"
echo "║     Transport : Streamable HTTP                            ║"
echo "║                                                            ║"
echo "║  Ou lancer directement :                                   ║"
echo "║     npx -y @modelcontextprotocol/inspector                 ║"
echo "║       --url http://${HOST}:${PORT}                         ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "▸ Appuyer sur Entrée pour arrêter le serveur …"
read -r
