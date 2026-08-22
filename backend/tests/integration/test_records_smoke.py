"""Critical path: documents list → create → get → patch → soft-delete."""

from __future__ import annotations

import uuid

import pytest

from tests.integration.conftest import assert_envelope, mutate

pytestmark = pytest.mark.integration

BASE = "/api/v2/records/document"


def test_documents_crud_smoke(auth_client):
    listed = auth_client.get(BASE, params={"page": 1, "limit": 20})
    list_body = assert_envelope(listed, require_meta=True)
    assert isinstance(list_body["data"], list)

    title = f"Integration smoke doc {uuid.uuid4().hex[:8]}"
    created = mutate(auth_client, "POST", BASE, json={"title": title})
    create_body = assert_envelope(created)
    entity_id = create_body["data"]["id"]
    assert create_body["data"].get("title") == title

    fetched = auth_client.get(f"{BASE}/{entity_id}")
    get_body = assert_envelope(fetched)
    assert get_body["data"]["id"] == entity_id

    updated_title = f"{title} updated"
    patched = mutate(auth_client, "PATCH", f"{BASE}/{entity_id}", json={"title": updated_title})
    patch_body = assert_envelope(patched)
    assert patch_body["data"].get("title") == updated_title

    deleted = mutate(auth_client, "DELETE", f"{BASE}/{entity_id}")
    assert deleted.status_code < 400, deleted.text
    assert "data" in deleted.json()
