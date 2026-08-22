"""OpenAPI response schema smoke for key frontend envelopes."""

from __future__ import annotations


def test_openapi_dashboard_summary_has_data_schema(app):
    paths = app.openapi()["paths"]
    op = paths["/api/v2/dashboard/summary"]["get"]
    responses = op.get("responses") or {}
    assert "200" in responses


def test_openapi_documents_list_present(app):
    paths = app.openapi()["paths"]
    assert "/api/v2/records/{type_code}" in paths
    assert "get" in paths["/api/v2/records/{type_code}"]
    assert "post" in paths["/api/v2/records/{type_code}"]
    assert "/api/v2/records/documents" not in paths


def test_openapi_auth_login_present(app):
    paths = app.openapi()["paths"]
    assert "/api/v2/auth/login" in paths
    assert "post" in paths["/api/v2/auth/login"]
