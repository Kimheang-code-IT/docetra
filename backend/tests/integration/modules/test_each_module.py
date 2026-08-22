"""Per-module live smoke — each domain family against running Docker API."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest

from tests.integration.conftest import assert_envelope, mutate

pytestmark = pytest.mark.integration


def test_record_module_list_and_create(auth_client):
    listed = auth_client.get("/api/v2/records/document", params={"page": 1, "limit": 5})
    assert_envelope(listed, require_meta=True)
    created = mutate(
        auth_client,
        "POST",
        "/api/v2/records/document",
        json={"title": f"UnitDoc {uuid.uuid4().hex[:8]}"},
    )
    body = assert_envelope(created)
    assert body["data"]["id"]
    assert body["data"].get("title")


def test_organization_module_department(auth_client):
    code = f"T{uuid.uuid4().hex[:6]}"
    created = mutate(
        auth_client,
        "POST",
        "/api/v2/organizations/department",
        json={"name": f"Test Dept {code}", "code": code},
    )
    body = assert_envelope(created)
    assert body["data"]["id"]
    listed = auth_client.get("/api/v2/organizations/department", params={"page": 1, "limit": 5})
    assert_envelope(listed, require_meta=True)


def test_people_access_module_users_and_catalog(auth_client):
    catalog = auth_client.get("/api/v2/users/permission-catalog")
    assert_envelope(catalog)
    assert isinstance(catalog.json()["data"], list)
    users = auth_client.get("/api/v2/users", params={"page": 1, "limit": 5})
    assert_envelope(users, require_meta=True)


def test_admin_config_module_settings_and_types(auth_client):
    info = auth_client.get("/api/v2/settings/app-info")
    assert info.status_code == 200
    types = auth_client.get("/api/v2/configuration/record-types", params={"page": 1, "limit": 5})
    assert_envelope(types, require_meta=True)


def test_storage_integration_module_portal_and_storage(auth_client):
    portal = auth_client.get("/api/v2/portal/file-uploads", params={"page": 1, "limit": 5})
    assert portal.status_code in {200, 403} or portal.status_code < 500
    storage = auth_client.get("/api/v2/settings/storage")
    assert storage.status_code in {200, 403}


def test_reporting_support_module_search_dashboard(auth_client):
    dash = auth_client.get("/api/v2/dashboard/summary")
    assert_envelope(dash)
    search = auth_client.get("/api/v2/search", params={"q": "a", "limit": 5})
    assert search.status_code == 200
    mentions = auth_client.get("/api/v2/mentions", params={"q": "a", "type": "officer", "limit": 5})
    assert mentions.status_code == 200
