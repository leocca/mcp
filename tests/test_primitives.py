"""Tests des primitives Resources & Prompts (exigence A.2)."""

import pytest

from src.server import mcp

pytestmark = pytest.mark.asyncio


class TestResources:
    async def test_ressources_static_registrees(self):
        ress = await mcp.list_resources()
        uris = {str(r.uri) for r in ress}
        assert "devops://git/status" in uris
        assert "devops://git/log" in uris
        assert "devops://pipeline/latest" in uris
        assert "devops://containers" in uris
        assert "devops://security/findings" in uris

    async def test_lecture_git_log(self):
        content = await mcp.read_resource("devops://git/log")
        text = str(content)
        assert "contents=" in text or len(text) > 0

    async def test_templates_registrees(self):
        templates = await mcp.list_resource_templates()
        uris = {t.uri_template for t in templates}
        assert "devops://git/diff/{commit_sha}" in uris
        assert "devops://repo/file/{path}" in uris

    async def test_template_lecture_fichier(self):
        templates = await mcp.list_resource_templates()
        file_tpl = next(t for t in templates if t.uri_template.endswith("{path}"))
        result = await file_tpl.read({"path": "README.md"})
        assert "DevOps" in str(result)

    async def test_template_diff_invalid_sha_rejetee(self):
        templates = await mcp.list_resource_templates()
        diff_tpl = next(t for t in templates if t.uri_template.endswith("{commit_sha}"))
        with pytest.raises(Exception):
            await diff_tpl.read({"commit_sha": "rm -rf /;"})


class TestPrompts:
    async def test_prompts_registres(self):
        prompts = await mcp.list_prompts()
        names = {p.name for p in prompts}
        assert {"review_pr", "audit_predeploy", "incident_triage", "generate_documentation"} <= names

    async def test_render_audit_predeploy(self):
        result = await mcp.render_prompt("audit_predeploy", {})
        assert "CHECKLIST" in str(result)

    async def test_render_review_pr(self):
        result = await mcp.render_prompt("review_pr", {"pr_id": "12"})
        assert "Pull Request #12" in str(result)

    async def test_render_incident_triage(self):
        result = await mcp.render_prompt("incident_triage", {"pipeline_branch": "main"})
        assert "main" in str(result)