"""Additional security acceptance checks for authenticated permission denials."""

from __future__ import annotations

import uuid

import pytest

from tests.integration.conftest import CSRF_COOKIE, CSRF_HEADER, assert_envelope, mutate

pytestmark = pytest.mark.integration


def test_unauthenticated_cannot_create_record(api_client):
    response = api_client.post("/api/v2/records/document", json={"title": "nope"})
    assert response.status_code in {401, 403}


def test_csrf_header_mismatch_rejected(auth_client):
    response = auth_client.post(
        "/api/v2/records/document",
        json={"title": "bad csrf"},
        headers={CSRF_HEADER: "not-the-cookie-value"},
    )
    assert response.status_code == 403


def test_logout_requires_csrf(api_client, require_api):
    from tests.integration.conftest import login_admin

    login_admin(api_client)
    # Missing CSRF should be rejected
    response = api_client.post("/api/v2/auth/logout")
    assert response.status_code == 403
    # With CSRF succeeds
    ok = mutate(api_client, "POST", "/api/v2/auth/logout")
    assert ok.status_code == 200
    me = api_client.get("/api/v2/auth/me")
    assert me.status_code in {401, 403}


def test_login_rate_limit_returns_429(api_client, require_api):
    email = f"rate-limit-{uuid.uuid4().hex[:8]}@docetra.test"
    statuses: list[int] = []
    for _ in range(12):
        response = api_client.post(
            "/api/v2/auth/login",
            json={"email": email, "password": "Wrong-Password-123"},
        )
        statuses.append(response.status_code)
        if response.status_code == 429:
            break
    assert 429 in statuses, statuses


def test_upload_rejects_disallowed_extension(auth_client):
    created = mutate(auth_client, "POST", "/api/v2/records/document", json={"title": f"Upload {uuid.uuid4().hex[:8]}"})
    entity_id = assert_envelope(created)["data"]["id"]
    response = mutate(
        auth_client,
        "POST",
        f"/api/v2/records/document/{entity_id}/attachments/upload",
        files={"file": ("payload.exe", b"MZ\x90\x00binary", "application/octet-stream")},
    )
    assert response.status_code == 415, response.text
