FROM python:3.10-slim

WORKDIR /app

# Dépendances système (git nécessaire pour les outils git, sans sed/awk dans les subprocess)
RUN apt-get update && \
    apt-get install -y --no-install-recommends git && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ src/

ENV PYTHONPATH=/app

# Utilisateur non-root pour la sécurité (principe du moindre privilège)
RUN groupadd -r mcp && useradd -r -g mcp mcp
USER mcp

EXPOSE 3000

# Transport : stdio par défaut — pour Streamable HTTP décommenter :
# ENTRYPOINT ["python", "-m", "src.server", "--transport", "http"]
ENTRYPOINT ["python", "-m", "src.server"]