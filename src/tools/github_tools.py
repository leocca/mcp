import os

from github import Github
from github.GithubException import GithubException

from src.logic.analysis import analyze_code_with_llm
from src.security.guard import detect_prompt_injection, redact_secrets
from src.security.validation import InvalidInputError, validate_branch_name
from src.tools.git_tools import get_pr_diff

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_NAME = os.getenv("TARGET_REPOSITORY")


def _get_github() -> Github:
    if not GITHUB_TOKEN:
        raise RuntimeError("GITHUB_TOKEN non configuré.")
    return Github(GITHUB_TOKEN)


def _get_repo(g: Github):
    return g.get_repo(REPO_NAME)


def suggest_review(pr_id: int) -> str:
    """(IA) Génère des commentaires de revue de code pour une PR.

    Le diff est transmis au LLM local via :func:`analyze_code_with_llm`.
    Le contenu revient du dépôt distant : il est d'abord passé au garde-fou
    anti-injection avant d'être envoyé au modèle.
    """
    if int(pr_id) <= 0:
        raise InvalidInputError(f"Numéro de PR invalide : {pr_id!r}.")
    try:
        repo = _get_repo(_get_github())
        pr = repo.get_pull(int(pr_id))
        title = pr.title or ""
    except GithubException as exc:
        return f"Erreur GitHub : {exc}"

    diff = get_pr_diff(int(pr_id))

    # Traitement du contenu distant comme NON fiable (A.6 / B.5)
    verdict = detect_prompt_injection(f"{title}\n{diff}")
    if not verdict.safe:
        return (
            f"[BLOQUÉ] Le contenu de la PR {pr_id} contient des marqueurs "
            f"d'injection de prompt ({verdict.severity}). Refus d'analyse."
        )

    prompt = (
        "Tu es un expert en revue de code. Pour la PR suivante, génère des "
        "commentaires de revue concrets et bienveillants : un commentaire par "
        f"problème, avec fichier, ligne supposée et suggestion de correction.\n\nTITRE : {title}\n\nDIFF :\n{diff}"
    )
    review = analyze_code_with_llm(prompt)
    return redact_secrets(review)


def list_issues(state: str = "open", limit: int = 10) -> str:
    """Liste les tickets (issues) du dépôt cible."""
    try:
        repo = _get_repo(_get_github())
        issues = repo.get_issues(state=state)
        lines = []
        for i, issue in enumerate(issues[: max(1, min(int(limit), 30))]):
            labels = ", ".join(lb.name for lb in issue.labels)
            lines.append(
                f"#{issue.number} [{state}] {issue.title} "
                f"({issue.user.login if issue.user else 'anon'})"
                + (f" | labels: {labels}" if labels else "")
            )
        return "\n".join(lines) if lines else f"Aucun ticket {state}."
    except GithubException as exc:
        return f"Erreur GitHub : {exc}"


def create_issue(title: str, body: str = "") -> str:
    """Crée un ticket sur le dépôt cible.

    Args:
        title: Titre du ticket.
        body: Description détaillée (optionnelle).
    """
    if not title or len(title.strip()) < 3:
        raise InvalidInputError("Titre de ticket trop court ou vide.")
    try:
        repo = _get_repo(_get_github())
        issue = repo.create_issue(title=title.strip(), body=body)
        return f"Ticket créé : #{issue.number} - {issue.title}"
    except GithubException as exc:
        return f"Erreur GitHub : {exc}"


def get_pipeline_status(limit: int = 3) -> str:
    """Retourne le statut des derniers workflows GitHub Actions."""
    try:
        repo = _get_repo(_get_github())
        runs = repo.get_workflow_runs()
        lines = []
        for run in runs[: max(1, min(int(limit), 10))]:
            lines.append(
                f"[{run.status}] #{run.id} {run.name or run.event} | "
                f"{run.head_branch or '?'} | {run.conclusion or 'pending'}"
            )
        return "\n".join(lines) if lines else "Aucune exécution de workflow."
    except GithubException as exc:
        return f"Erreur GitHub Actions : {exc}"


def trigger_pipeline(branch: str, workflow_file: str = "", dry_run: bool = True) -> str:
    """*Déclenchement CI* : relance un workflow GitHub Actions via dispatch.

    Args:
        branch: Branche cible (validation stricte du nom).
        workflow_file: Nom du fichier de workflow (optionnel si un seul).
        dry_run: Si True (défaut), simule le déclenchement sans l'exécuter.

    Returns:
        Confirmation ou simulation.
    """
    branch = validate_branch_name(branch)
    if dry_run:
        return (
            f"[DRY-RUN] Le workflow {workflow_file or '(*)'} serait déclenché "
            f"sur la branche {branch}."
        )
    try:
        repo = _get_repo(_get_github())
        workflows = list(repo.get_workflows())
        if not workflows:
            return "Erreur : aucun workflow GitHub Actions dans le dépôt."

        target = None
        if workflow_file:
            for wf in workflows:
                if wf.path.endswith(workflow_file):
                    target = wf
                    break
            if target is None:
                return f"Erreur : workflow {workflow_file} introuvable."
        else:
            if len(workflows) > 1:
                choices = "\n".join(f"- {w.path}" for w in workflows)
                return (
                    "Plusieurs workflows disponibles, précisez workflow_file :\n"
                    + choices
                )
            target = workflows[0]

        target.create_dispatch(branch)
        return f"Pipeline déclenché sur {branch} (workflow {target.path})."
    except GithubException as exc:
        return f"Erreur GitHub Actions : {exc}"