import ollama
import os

def analyze_code_with_llm(diff_content: str):
    """Envoie le diff à l'IA locale pour trouver des bugs logiques."""
    
    # On définit le modèle (Qwen 2.5 ou 3.5 comme demandé dans ton document)
    model = os.getenv("LLM_MODEL", "qwen2.5:latest")
    
    prompt = f"""
    Tu es un expert en Revue de Code DevOps et Cybersécurité.
    Analyse le diff suivant et identifie :
    1. Les bugs logiques (erreurs de calcul, conditions impossibles).
    2. Les failles de sécurité potentielles (secrets en clair, injections).
    3. Les optimisations possibles.

    DIFF À ANALYSER :
    {diff_content}

    Réponds de manière concise sous forme de liste à puces.
    """

    try:
        response = ollama.generate(model=model, prompt=prompt)
        return response['response']
    except Exception as e:
        return f"Erreur lors de l'analyse IA : {str(e)}"
