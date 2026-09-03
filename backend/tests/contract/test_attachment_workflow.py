"""Contract tests for the record attachment upload/detach workflow."""

from __future__ import annotations

from pathlib import Path


def test_openapi_attachment_upload_present(app):
    paths = app.openapi()["paths"]
    op = paths["/api/v2/records/{type_code}/{entity_id}/attachments/upload"]["post"]
    assert "200" in op.get("responses") or "201" in op.get("responses")
    content = (op.get("requestBody") or {}).get("content") or {}
    assert "multipart/form-data" in content, "upload endpoint must accept multipart file bytes"


def test_openapi_attachment_detach_present(app):
    paths = app.openapi()["paths"]
    assert "delete" in paths["/api/v2/records/{type_code}/{entity_id}/attachments/{file_id}"]


def test_attachment_upload_rejects_json_body(app):
    """The upload route must not silently accept metadata-only JSON."""
    paths = app.openapi()["paths"]
    op = paths["/api/v2/records/{type_code}/{entity_id}/attachments/upload"]["post"]
    content = (op.get("requestBody") or {}).get("content") or {}
    assert "application/json" not in content


def test_upload_workflow_module_boundaries():
    """The workflow composes public facades only — no sibling repositories/models."""
    import ast

    source = Path(__file__).parents[2] / "app" / "application" / "attachment_router.py"
    tree = ast.parse(source.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        modules = []
        if isinstance(node, ast.Import):
            modules = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules = [node.module]
        for name in modules:
            parts = name.split(".")
            if len(parts) >= 5 and parts[:2] == ["app", "modules"] and parts[-1] == "repository":
                raise AssertionError(f"workflow imports a repository: {name}")
