import os

import docker
from docker.errors import DockerException, NotFound

from src.security.guard import redact_secrets
from src.security.validation import InvalidInputError, validate_relative_path

DEFAULT_IMAGE = os.getenv("APP_IMAGE", "mcp-demo-app")


def _client() -> docker.DockerClient:
    try:
        return docker.from_env()
    except DockerException as exc:
        raise RuntimeError(f"Docker indisponible : {exc}") from exc


def get_deployment_info() -> str:
    """Liste les conteneurs Docker en cours d'exécution (déploiements)."""
    try:
        client = _client()
        containers = client.containers.list(all=True)
        if not containers:
            return "Aucun conteneur Docker."
        lines = []
        for c in containers:
            image = c.image.tags[0] if c.image.tags else c.image.short_id
            status = c.status
            ports = c.ports or {}
            mapping = []
            for host, binds in ports.items():
                if binds:
                    for b in binds:
                        mapping.append(f"{host}->{b.get('HostPort', '?')}")
            lines.append(
                f"{c.short_id} | {c.name} | {image} | {status}"
                + (f" | ports: {', '.join(mapping)}" if mapping else "")
            )
        return "\n".join(lines)
    except DockerException as exc:
        return f"Erreur Docker : {exc}"


def get_container_logs(container_id: str, tail: int = 50) -> str:
    """Retourne les journaux d'un conteneur avec filtrage des secrets.

    Implémente B.5 : « Filtrage automatisé de l'outil get_logs pour empêcher
    l'exposition d'informations sensibles de production ».
    """
    cid = validate_relative_path(container_id)
    try:
        client = _client()
        container = client.containers.get(cid)
        logs = container.logs(tail=max(1, min(int(tail), 500))).decode(
            "utf-8", errors="replace"
        )
        return redact_secrets(logs)
    except NotFound:
        return f"Conteneur {cid} introuvable."
    except DockerException as exc:
        return f"Erreur Docker : {exc}"


def delete_container(container_id: str) -> str:
    """Supprime réellement un conteneur Docker (appelé après HITL).

    Args:
        container_id: Nom ou identifiant court/long du conteneur.

    Returns:
        Confirmation de suppression.
    """
    cid = validate_relative_path(container_id)
    try:
        client = _client()
        container = client.containers.get(cid)
        name = container.name
        container.remove(force=True)
        return f"Conteneur {name} ({cid}) supprimé."
    except NotFound:
        return f"Conteneur {cid} introuvable."
    except DockerException as exc:
        return f"Erreur Docker : {exc}"


def rollback_deployment(image_tag: str, dry_run: bool = True) -> str:
    """*Retour arrière* : recrée le conteneur applicatif sur une image antérieure.

    Args:
        image_tag: Tag Docker de l'image cible (ex. ``v1.2.0``).
        dry_run: Si True (défaut), simule le rollback sans effet système.

    Note:
        L'exécution réelle est soumise à la validation humaine HITL côté
        serveur MCP (l'outil ne l'exécute jamais seul sans approbation).
    """
    tag = validate_relative_path(image_tag)
    app_image = f"{DEFAULT_IMAGE}:{tag}"
    if dry_run:
        return (
            f"[DRY-RUN] Le conteneur applicatif serait repositionné sur "
            f"{app_image}."
        )
    try:
        client = _client()
        client.images.pull(app_image)
        # Détruit puis relance le conteneur applicatif (nom fixe "app").
        try:
            old = client.containers.get("app")
            old.remove(force=True)
        except NotFound:
            pass
        container = client.containers.run(
            app_image,
            name="app",
            detach=True,
            ports={"8000/tcp": 8000},
        )
        return f"Rollback effectué : conteneur 'app' sur {app_image} ({container.short_id})."
    except DockerException as exc:
        return f"Erreur Docker : {exc}"