"""Exporte les schémas JSON de tous les outils MCP dans schemas/tools.json.

Usage :
    venv/bin/python src/export_schemas.py

L'entrée « tools » contient un tableau de {name, description, inputSchema, annotations}.
"""

import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

OUTPUT = os.getenv("SCHEMA_OUTPUT", "schemas/tools.json")


async def main():
    from src.server import mcp

    os.makedirs(os.path.dirname(OUTPUT) or ".", exist_ok=True)
    tools = await mcp.list_tools()
    entries = []
    for t in tools:
        mcp_tool = t.to_mcp_tool()
        entries.append({
            "name": mcp_tool.name,
            "description": (mcp_tool.description or "").split("\n\n")[0],
            "inputSchema": mcp_tool.inputSchema,
        })

    payload = {"tools": entries}
    with open(OUTPUT, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)
    print(f"Schémas exportés : {OUTPUT} ({len(entries)} outils)")


if __name__ == "__main__":
    asyncio.run(main())