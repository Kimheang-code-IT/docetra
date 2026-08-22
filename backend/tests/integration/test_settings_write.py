"""Authenticated settings mutations + CSRF enforcement."""

from __future__ import annotations

import pytest

from tests.integration.conftest import assert_envelope, mutate

pytestmark = pytest.mark.integration


def test_patch_app_info_requires_csrf(auth_client):
    # Intentionally omit CSRF header — cookie alone must not be enough.
    response = auth_client.patch(
        "/api/v2/settings/app-info",
        json={"shortName": "ShouldFail"},
    )
    assert response.status_code == 403, response.text


def test_patch_app_info_with_csrf(auth_client):
    before = assert_envelope(auth_client.get("/api/v2/settings/app-info"))["data"]
    original_short = before.get("shortName") or "Docetra"
    marker = f"{original_short}-it"

    patched = mutate(
        auth_client,
        "PATCH",
        "/api/v2/settings/app-info",
        json={"shortName": marker},
    )
    body = assert_envelope(patched)
    assert body["data"].get("shortName") == marker

    # Restore prior branding so local/dev stays clean.
    restore = mutate(
        auth_client,
        "PATCH",
        "/api/v2/settings/app-info",
        json={"shortName": original_short},
    )
    assert_envelope(restore)
