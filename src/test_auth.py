import os
from keycloak import KeycloakOpenID
from dotenv import load_dotenv

# Chargement des variables d'environnement
load_dotenv()

# Initialisation du client Keycloak
keycloak_openid = KeycloakOpenID(
    server_url=os.getenv("KEYCLOAK_URL"),
    client_id=os.getenv("KEYCLOAK_CLIENT_ID"),
    realm_name=os.getenv("KEYCLOAK_REALM"),
    client_secret_key=os.getenv("KEYCLOAK_CLIENT_SECRET")
)

def test_login():
    print("--- Tentative de connexion à Keycloak ---")
    try:
        # On essaie de récupérer un token avec l'utilisateur testuser
        token = keycloak_openid.token("testuser", "password123")
        
        print("✅ Succès ! Token récupéré.")
        print(f"\nAccess Token (extrait) : {token['access_token'][:50]}...")
        
        # On vérifie si on peut récupérer les infos de l'utilisateur avec ce token
        user_info = keycloak_openid.userinfo(token['access_token'])
        print(f"✅ Utilisateur authentifié : {user_info['preferred_username']}")
        
    except Exception as e:
        print(f"❌ Erreur de connexion : {str(e)}")
        print("\nVérifiez :")
        print("1. Que Docker (Keycloak) tourne bien.")
        print("2. Que 'Direct access grants' est bien activé dans Keycloak.")
        print("3. Que le Client Secret dans le .env est le bon.")

if __name__ == "__main__":
    test_login()
