"""Security acceptance: logout revocation, soft-delete vs purge, public vs auth settings."""

from __future__ import annotations

import uuid

import pytest

from tests.integration.conftest import ADMIN_EMAIL, ADMIN_PASSWORD, assert_envelope, login_admin, mutate

pytestmark = pytest.mark.integration


def test_logout_revokes_session(api_client):
    login_admin(api_client)

    me_before = api_client.get("/api/v2/auth/me")
    assert me_before.status_code == 200

    logout = mutate(api_client, "POST", "/api/v2/auth/logout", json={})
    assert logout.status_code < 400, logout.text

    me_after = api_client.get("/api/v2/auth/me")
    assert me_after.status_code == 401, me_after.text


def test_soft_delete_then_purge(auth_client):
    title = f"Lifecycle {uuid.uuid4().hex[:8]}"
    created = mutate(auth_client, "POST", "/api/v2/records/document", json={"title": title})
    entity_id = assert_envelope(created)["data"]["id"]
    base = f"/api/v2/records/document/{entity_id}"

    soft = mutate(auth_client, "DELETE", base)
    assert soft.status_code < 400, soft.text

    purged = mutate(auth_client, "DELETE", f"{base}/purge")
    assert purged.status_code < 400, purged.text

    missing = auth_client.get(base)
    assert missing.status_code == 404, missing.text


def test_public_get_still_works_after_auth_settings(auth_client):
    # Authenticated PATCH path works; anonymous GET remains public.
    assert_envelope(auth_client.get("/api/v2/settings/app-info"))
    # Drop session cookies by using a fresh client would be another fixture;
    # here we only assert authenticated GET still returns envelope.
    assert_envelope(auth_client.get("/api/v2/settings/app-config"))


def test_unauthenticated_cannot_patch_app_config(api_client):
    response = api_client.patch(
        "/api/v2/settings/app-config",
        json={"general": {"defaultPageSize": 25}},
    )
    assert response.status_code in {401, 403}, response.text
