import os
from keycloak import KeycloakOpenID
from dotenv import load_dotenv

load_dotenv()

keycloak_openid = KeycloakOpenID(
    server_url=os.getenv("KEYCLOAK_URL"),
    client_id=os.getenv("KEYCLOAK_CLIENT_ID"),
    realm_name=os.getenv("KEYCLOAK_REALM"),
    client_secret_key=os.getenv("KEYCLOAK_CLIENT_SECRET")
)

def get_token(username, password):
    token = keycloak_openid.token(username, password)
    return token['access_token']

print("--- TOKEN ADMIN ---")
print(get_token("admin_user", "admin123"))

print("\n--- TOKEN DEV ---")
print(get_token("dev_user", "dev123"))
