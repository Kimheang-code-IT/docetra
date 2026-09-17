"""Cross-cutting: search, exports, mentions, CSRF, CORS preflight."""

from __future__ import annotations

import uuid

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


def test_audit_trail_records_mutation(auth_client):
    title = f"Audit trail {uuid.uuid4().hex[:8]}"
    created = mutate(auth_client, "POST", "/api/v2/records/document", json={"title": title})
    entity_id = assert_envelope(created)["data"]["id"]

    logs = auth_client.get("/api/v2/records/logs", params={"page": 1, "limit": 50})
    body = assert_envelope(logs, require_meta=True)
    entries = [entry for entry in body["data"] if (entry.get("detail") or {}).get("correlationId") == entity_id]
    assert entries, body
    entry = entries[0]
    assert entry["action"] in {"create", "created"}
    assert entry["sourceLog"] in {"record", "api", "unknown"}
    assert entry["target"]


def test_files_unknown_returns_404(auth_client):
    response = auth_client.get("/api/v2/files/00000000-0000-0000-0000-000000000001")
    assert response.status_code == 404


def test_cors_preflight_from_frontend_origin(api_client):
    # Matches CORS_ALLOWED_ORIGINS in infrastructure/.env.example (the nginx edge origin).
    origin = "http://localhost:8080"
    response = api_client.options(
        "/api/v2/auth/me",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "GET",
        },
    )
    # Starlette may return 200/204 for OPTIONS.
    assert response.status_code in {200, 204}
    allow_origin = response.headers.get("access-control-allow-origin")
    assert allow_origin == origin
    assert response.headers.get("access-control-allow-credentials") == "true"


def test_csrf_blocks_logout_without_header(auth_client):
    response = auth_client.post("/api/v2/auth/logout", json={})
    assert response.status_code == 403, response.text
