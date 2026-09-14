import subprocess
import json
import os
from loguru import logger

def run_semgrep_scan(cwd=None):
    """Lance un scan de sécurité statique avec Semgrep."""
    logger.info("Démarrage du scan Semgrep...")
    try:
        # Utilisation d'une liste pour la sécurité (comme demandé p.4 du PDF)
        # --config=auto utilise les règles de la communauté
        result = subprocess.run(
            ["semgrep", "scan", "--config=auto", "--json", "."],
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=300,
        )
        
        # On parse le JSON pour ne retourner que l'essentiel
        data = json.loads(result.stdout)
        results = data.get("results", [])
        
        if not results:
            return "✅ Aucun problème de sécurité détecté par Semgrep."
        
        summary = f"⚠️ {len(results)} vulnérabilité(s) détectée(s) :\n"
        for issue in results[:5]: # On limite aux 5 premières pour l'IA
            summary += f"- [{issue['extra']['severity']}] {issue['path']}: {issue['extra']['message']}\n"
        
        return summary
    except Exception as e:
        return f"Erreur lors du scan Semgrep : {str(e)}"

def run_pip_audit():
    """Vérifie les vulnérabilités dans les dépendances Python."""
    logger.info("Démarrage de pip-audit...")
    try:
        result = subprocess.run(
            ["pip-audit", "--format", "json"],
            capture_output=True,
            text=True
        )
        
        if not result.stdout.strip():
            return "✅ Aucune vulnérabilité trouvée dans les dépendances."

        data = json.loads(result.stdout)
        # pip-audit >= 2.x renvoie {"dependencies": [...]} ; plus anciens : liste directe
        if isinstance(data, dict):
            data = data.get("dependencies", [])
        vulnerabilities = [d for d in data if d.get("vulns")]
        
        if not vulnerabilities:
            return "✅ Toutes les dépendances sont à jour et sécurisées."

        report = "❌ Dépendances vulnérables trouvées :\n"
        for v in vulnerabilities:
            report += f"- {v['name']} (version {v['version']}): {len(v['vulns'])} CVE détectée(s)\n"
        
        return report
    except Exception as e:
        return f"Erreur lors de l'audit des dépendances : {str(e)}"