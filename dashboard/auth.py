"""Authentification Keycloak OIDC pour le dashboard Flask."""

from __future__ import annotations

import os
from functools import wraps

from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
from flask import Flask, session, redirect, url_for, request

load_dotenv()

oauth = OAuth()

KEYCLOAK_URL = os.getenv("KEYCLOAK_URL", "http://localhost:8080")
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM", "devops-realm")
KEYCLOAK_CLIENT_ID = os.getenv(
    "DASHBOARD_CLIENT_ID", os.getenv("KEYCLOAK_CLIENT_ID", "dashboard")
)
KEYCLOAK_CLIENT_SECRET = os.getenv(
    "DASHBOARD_CLIENT_SECRET", os.getenv("KEYCLOAK_CLIENT_SECRET", "")
)
REDIRECT_URI = os.getenv("DASHBOARD_REDIRECT_URI", "http://localhost:5000/callback")


def init_auth(app: Flask) -> None:
    """Configure l'authentification Keycloak OIDC sur l'application Flask."""
    app.secret_key = os.getenv("FLASK_SECRET_KEY", os.urandom(32).hex())

    oauth.init_app(app)
    oauth.register(
        name="keycloak",
        client_id=KEYCLOAK_CLIENT_ID,
        client_secret=KEYCLOAK_CLIENT_SECRET,
        server_metadata_url=f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )


def login_required(f):
    """Décorateur : redirige vers Keycloak si non authentifié."""

    @wraps(f)
    def decorated(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return decorated


def get_current_user() -> dict | None:
    """Retourne les infos de l'utilisateur courant depuis la session."""
    return session.get("user")
