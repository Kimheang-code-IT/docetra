"""Optimistic concurrency is required for versioned record mutations."""

from __future__ import annotations

import uuid

import pytest

from tests.integration.conftest import assert_envelope, mutate

pytestmark = pytest.mark.integration

BASE = "/api/v2/records/document"


def test_patch_requires_version_and_rejects_stale_token(auth_client):
    created = mutate(auth_client, "POST", BASE, json={"title": f"Version {uuid.uuid4().hex[:8]}"})
    entity_id = assert_envelope(created)["data"]["id"]
    path = f"{BASE}/{entity_id}"
    version = assert_envelope(auth_client.get(path))["data"]["version"]

    missing = mutate(auth_client, "PATCH", path, json={"title": "no token"}, attach_version=False)
    assert missing.status_code == 428, missing.text

    stale = mutate(
        auth_client,
        "PATCH",
        path,
        json={"title": "stale", "version": int(version) - 1 if int(version) > 1 else 0},
        attach_version=False,
        headers={"If-Match": str(int(version) - 1 if int(version) > 1 else 0)},
    )
    assert stale.status_code == 409, stale.text
