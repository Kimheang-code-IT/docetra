"""Cross-cutting: search, exports, mentions, CSRF, CORS preflight."""

from __future__ import annotations

import pytest

from tests.integration.conftest import assert_envelope, mutate

pytestmark = pytest.mark.integration


def test_search_keyword(auth_client):
    response = auth_client.get("/api/v2/search", params={"q": "doc", "mode": "keyword", "limit": 5})
    body = assert_envelope(response)
    assert isinstance(body["data"], list)


def test_search_ask(auth_client):
    response = mutate(auth_client, "POST", "/api/v2/search/ask", json={"q": "documents"})
    body = assert_envelope(response)
    assert "answer" in body["data"]
    assert "citations" in body["data"]


def test_mentions(auth_client):
    response = auth_client.get("/api/v2/mentions", params={"q": "a", "type": "officer", "limit": 10})
    body = assert_envelope(response)
    assert isinstance(body["data"], list)


def test_export_job_create_and_get(auth_client):
    created = mutate(
        auth_client,
        "POST",
        "/api/v2/exports",
        json={"resource": "documents", "format": "csv"},
    )
    assert created.status_code == 202, created.text
    body = assert_envelope(created)
    job_id = body["data"]["id"]
    status = auth_client.get(f"/api/v2/exports/{job_id}")
    status_body = assert_envelope(status)
    assert status_body["data"]["id"] == job_id


def test_files_unknown_returns_404(auth_client):
    response = auth_client.get("/api/v2/files/00000000-0000-0000-0000-000000000001")
    assert response.status_code == 404


def test_cors_preflight_from_frontend_origin(api_client):
    response = api_client.options(
        "/api/v2/auth/me",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )
    # Starlette may return 200/204 for OPTIONS.
    assert response.status_code in {200, 204}
    allow_origin = response.headers.get("access-control-allow-origin")
    assert allow_origin == "http://localhost:3000"
    assert response.headers.get("access-control-allow-credentials") == "true"


def test_csrf_blocks_logout_without_header(auth_client):
    response = auth_client.post("/api/v2/auth/logout", json={})
    assert response.status_code == 403, response.text
