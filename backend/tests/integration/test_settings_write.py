"""Authenticated settings mutations + CSRF enforcement."""

from __future__ import annotations

import pytest

from tests.integration.conftest import assert_envelope, mutate

pytestmark = pytest.mark.integration


def test_patch_app_config_requires_csrf(auth_client):
    # Intentionally omit CSRF header — cookie alone must not be enough.
    response = auth_client.patch(
        "/api/v2/settings/app-config",
        json={"general": {"defaultPageSize": 21}},
    )
    assert response.status_code == 403, response.text


def test_patch_app_config_with_csrf(auth_client):
    before = assert_envelope(auth_client.get("/api/v2/settings/app-config"))["data"]
    original = int((before.get("general") or {}).get("defaultPageSize") or 20)
    marker = original + 1

    patched = mutate(
        auth_client,
        "PATCH",
        "/api/v2/settings/app-config",
        json={"general": {"defaultPageSize": marker}},
    )
    body = assert_envelope(patched)
    assert int(body["data"]["general"]["defaultPageSize"]) == marker

    # Restore prior value so local/dev stays clean.
    restore = mutate(
        auth_client,
        "PATCH",
        "/api/v2/settings/app-config",
        json={"general": {"defaultPageSize": original}},
    )
    assert_envelope(restore)
