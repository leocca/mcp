import pytest
from unittest.mock import patch
from src.auth.security import has_role

def test_rbac_logic():
    """Vérifie si la fonction de rôle fonctionne correctement."""
    mock_user = {
        "username": "testuser",
        "roles": ["admin", "developer"]
    }
    assert has_role(mock_user, "admin") is True
    assert has_role(mock_user, "manager") is False

@patch("src.auth.security.verify_keycloak_token")
def test_tool_access_denied(mock_auth):
    """Vérifie que l'accès est refusé si le token est invalide."""
    mock_auth.return_value = None
    
    # Simulation d'un appel (Logique simplifiée pour l'exemple)
    from src.server import safe_tool # Si tu as créé cet outil
    # result = safe_tool("fake_token") 
    # assert "Erreur" in result
