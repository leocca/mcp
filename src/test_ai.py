import ollama

try:
    response = ollama.generate(model='qwen2.5', prompt='Pourquoi utiliser Docker en DevOps ?')
    print("Réponse de l'IA :")
    print(response['response'])
except Exception as e:
    print(f"Erreur : {e}")
