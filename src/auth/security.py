import os
from keycloak import KeycloakOpenID
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

# Configuration Keycloak
try:
    keycloak_openid = KeycloakOpenID(
        server_url=os.getenv("KEYCLOAK_URL"),
        client_id=os.getenv("KEYCLOAK_CLIENT_ID"),
        realm_name=os.getenv("KEYCLOAK_REALM"),
        client_secret_key=os.getenv("KEYCLOAK_CLIENT_SECRET")
    )
except Exception as e:
    logger.warning(f"Configuration Keycloak incomplète : {e}")

def verify_keycloak_token(token: str):
    """Vérifie le token auprès de Keycloak et récupère les infos utilisateur."""
    try:
        # 1. Décoder et vérifier la signature du token
        # Note : userinfo() appelle l'endpoint de Keycloak (nécessite que Keycloak soit en ligne)
        user_info = keycloak_openid.userinfo(token)

        # 2. Récupérer les rôles (RBAC)
        token_info = keycloak_openid.decode_token(token)
        roles = token_info.get("realm_access", {}).get("roles", [])
        
        return {
            "username": user_info.get("preferred_username"),
            "roles": roles,
            "active": True
        }
    except Exception as e:
        logger.error(f"Erreur Auth Keycloak : {str(e)}")
        return None

def has_role(user_data, required_role):
    """Vérifie si l'utilisateur possède le rôle nécessaire."""
    if not user_data:
        return False
    return required_role in user_data.get("roles", [])
