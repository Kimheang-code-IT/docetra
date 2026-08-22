"""Cross-module flow: record + org + search + settings work together on one session."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest

from tests.integration.conftest import assert_envelope, mutate

pytestmark = pytest.mark.integration


def test_modules_together_record_org_search_settings(auth_client):
    """Admin session exercises record, organization, reporting, and admin_config in one flow."""
    # 1) Create department (organization)
    code = f"J{uuid.uuid4().hex[:6]}"
    dept = mutate(
        auth_client,
        "POST",
        "/api/v2/organizations/department",
        json={"name": f"Joint {code}", "code": code},
    )
    dept_body = assert_envelope(dept)
    dept_id = dept_body["data"]["id"]

    # 2) Create document record (record)
    title = f"Joint Doc {uuid.uuid4().hex[:8]}"
    doc = mutate(
        auth_client,
        "POST",
        "/api/v2/records/document",
        json={"title": title, "officeInCharge": dept_id},
    )
    doc_body = assert_envelope(doc)
    doc_id = doc_body["data"]["id"]
    assert doc_id

    # 3) Read back record
    got = auth_client.get(f"/api/v2/records/document/{doc_id}")
    assert_envelope(got)
    assert got.json()["data"]["id"] == doc_id

    # 4) Search / mentions (reporting_support)
    search = auth_client.get("/api/v2/search", params={"q": title[:8], "limit": 10})
    assert search.status_code == 200
    mentions = auth_client.get("/api/v2/mentions", params={"q": "Joint", "type": "department", "limit": 10})
    assert mentions.status_code == 200

    # 5) Settings public + authenticated config (admin_config)
    info = auth_client.get("/api/v2/settings/app-info")
    assert info.status_code == 200
    assert "data" in info.json() or isinstance(info.json(), dict)

    # 6) Surfaces meta still available
    surfaces = auth_client.get("/api/v2/records/_meta/surfaces")
    assert surfaces.status_code == 200


def test_security_csrf_required_on_cross_module_write(api_client, auth_client):
    """Mutating without CSRF must fail; same path with CSRF from auth session works."""
    bare = api_client.post(
        "/api/v2/records/document",
        json={"title": f"No CSRF {uuid.uuid4().hex[:6]}"},
    )
    assert bare.status_code in {401, 403}

    ok = mutate(
        auth_client,
        "POST",
        "/api/v2/records/document",
        json={"title": f"With CSRF {uuid.uuid4().hex[:6]}"},
    )
    assert_envelope(ok)
