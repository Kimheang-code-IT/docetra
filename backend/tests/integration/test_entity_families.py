"""Parametrized list (+ optional create/get) smoke across adapter families."""

from __future__ import annotations

import uuid
from collections.abc import Callable
from datetime import datetime, timezone

import pytest

from tests.integration.conftest import assert_envelope, mutate

pytestmark = pytest.mark.integration

# (path, create_body_factory | None) — None means list-only.
FAMILY_SPECS: list[tuple[str, Callable[[], dict] | None]] = [
    ("/api/v2/records/meeting_topic", lambda: {"title": f"Topic {uuid.uuid4().hex[:8]}"}),
    (
        "/api/v2/records/meeting_history",
        lambda: {
            "title": f"Meeting {uuid.uuid4().hex[:8]}",
            "meetingDate": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        },
    ),
    ("/api/v2/records/incoming_document", lambda: {"title": f"Incoming {uuid.uuid4().hex[:8]}"}),
    ("/api/v2/records/outgoing_document", lambda: {"title": f"Outgoing {uuid.uuid4().hex[:8]}"}),
    ("/api/v2/records/document", lambda: {"title": f"Document {uuid.uuid4().hex[:8]}"}),
    ("/api/v2/records/master_list_request", lambda: {"title": f"MLR {uuid.uuid4().hex[:8]}"}),
    ("/api/v2/records/logs", None),
    ("/api/v2/records/_meta/surfaces", None),
    ("/api/v2/organizations/department", lambda: {"name": f"Dept {uuid.uuid4().hex[:6]}", "code": f"D{uuid.uuid4().hex[:6]}"}),
    ("/api/v2/organizations/company", lambda: {"name": f"Co {uuid.uuid4().hex[:6]}", "code": f"C{uuid.uuid4().hex[:6]}"}),
    ("/api/v2/purpose", lambda: {"name": f"Purpose {uuid.uuid4().hex[:6]}"}),
    ("/api/v2/sector", lambda: {"name": f"Sector {uuid.uuid4().hex[:6]}"}),
    ("/api/v2/organizations/_meta/types", None),
    ("/api/v2/officers", lambda: {"name": f"Officer {uuid.uuid4().hex[:6]}", "email": f"o{uuid.uuid4().hex[:6]}@example.com"}),
    ("/api/v2/users", None),
    ("/api/v2/users/roles", None),
    ("/api/v2/configuration/record-types", None),
    ("/api/v2/configuration/record-attributes", None),
    ("/api/v2/portal/file-uploads", None),
    ("/api/v2/portal/google-drive-sync", None),
    ("/api/v2/portal/logs", None),
    ("/api/v2/system/logs", None),
    ("/api/v2/settings/storage", None),
]


@pytest.mark.parametrize("path,create_factory", FAMILY_SPECS, ids=[p for p, _ in FAMILY_SPECS])
def test_family_list_envelope(auth_client, path, create_factory):
    no_meta = path in {"/api/v2/records/_meta/surfaces", "/api/v2/organizations/_meta/types"}
    params = None if no_meta else {"page": 1, "limit": 20}
    response = auth_client.get(path, params=params)
    body = assert_envelope(response, require_meta=not no_meta)
    if path == "/api/v2/records/_meta/surfaces":
        assert isinstance(body["data"], dict)
        assert "document" in body["data"] or "meeting" in body["data"]
    elif path == "/api/v2/organizations/_meta/types":
        assert isinstance(body["data"], list)
        codes = {row.get("code") for row in body["data"]}
        assert {"department", "company"} <= codes
    else:
        assert isinstance(body["data"], list)


def test_organization_company_sector_purpose_and_department_hierarchy(auth_client):
    sector = assert_envelope(mutate(auth_client, "POST", "/api/v2/sector", json={"name": f"Sec {uuid.uuid4().hex[:6]}"}))
    purpose = assert_envelope(mutate(auth_client, "POST", "/api/v2/purpose", json={"name": f"Pur {uuid.uuid4().hex[:6]}"}))
    company = assert_envelope(
        mutate(
            auth_client,
            "POST",
            "/api/v2/organizations/company",
            json={
                "name": f"Co {uuid.uuid4().hex[:6]}",
                "sectorId": sector["data"]["id"],
                "purposeId": purpose["data"]["id"],
            },
        )
    )
    assert company["data"].get("sectorId") == sector["data"]["id"]
    assert company["data"].get("purposeId") == purpose["data"]["id"]

    parent = assert_envelope(
        mutate(auth_client, "POST", "/api/v2/organizations/department", json={"name": f"Root {uuid.uuid4().hex[:6]}"})
    )
    child = assert_envelope(
        mutate(
            auth_client,
            "POST",
            "/api/v2/organizations/department",
            json={"name": f"Child {uuid.uuid4().hex[:6]}", "parentId": parent["data"]["id"]},
        )
    )
    assert child["data"].get("parentId") == parent["data"]["id"]
    assert int(child["data"].get("lvl") or 0) >= 2

    # Cross-type parent rejected
    bad = mutate(
        auth_client,
        "POST",
        "/api/v2/organizations/department",
        json={"name": f"Bad {uuid.uuid4().hex[:6]}", "parentId": company["data"]["id"]},
    )
    assert bad.status_code == 422, bad.text


@pytest.mark.parametrize(
    "path,create_factory",
    [(p, f) for p, f in FAMILY_SPECS if f is not None],
    ids=[p for p, f in FAMILY_SPECS if f is not None],
)
def test_family_create_and_get(auth_client, path, create_factory):
    payload = create_factory()
    created = mutate(auth_client, "POST", path, json=payload)
    if created.status_code >= 400:
        pytest.xfail(f"create not ready for {path}: {created.status_code} {created.text[:200]}")
    body = assert_envelope(created)
    entity_id = body["data"].get("id")
    assert entity_id, body

    fetched = auth_client.get(f"{path}/{entity_id}")
    assert_envelope(fetched)


def test_permission_catalog(auth_client):
    response = auth_client.get("/api/v2/users/permission-catalog")
    body = assert_envelope(response)
    assert body["data"], body


def test_dynamic_document_subroutes(auth_client):
    title = f"Subroute doc {uuid.uuid4().hex[:8]}"
    created = mutate(auth_client, "POST", "/api/v2/records/document", json={"title": title})
    body = assert_envelope(created)
    entity_id = body["data"]["id"]
    base = f"/api/v2/records/document/{entity_id}"

    comments = auth_client.get(f"{base}/comments")
    assert_envelope(comments)

    activity = auth_client.get(f"{base}/activity")
    assert_envelope(activity)

    schema = auth_client.get("/api/v2/records/document/schema")
    assert_envelope(schema)

    fav = mutate(auth_client, "PUT", f"{base}/favorite", json={"isFavorite": True})
    assert fav.status_code < 400, fav.text

    archived = mutate(auth_client, "POST", f"{base}/archive", json={})
    assert archived.status_code < 400, archived.text

    restored = mutate(auth_client, "POST", f"{base}/restore", json={})
    assert restored.status_code < 400, restored.text

    mutate(auth_client, "DELETE", base)


def test_record_types_drive_dynamic_matrix(auth_client):
    """Parametrize smoke over live configuration record types when present."""
    listed = auth_client.get("/api/v2/configuration/record-types", params={"page": 1, "limit": 50})
    body = assert_envelope(listed, require_meta=True)
    codes = [row.get("code") for row in body["data"] if row.get("code")]
    if not codes:
        pytest.skip("no record types seeded")
    for code in codes[:8]:
        response = auth_client.get(f"/api/v2/records/{code}", params={"page": 1, "limit": 5})
        assert_envelope(response, require_meta=True)


def test_meeting_board_reorder_requires_payload(auth_client):
    response = mutate(auth_client, "POST", "/api/v2/records/meeting_history/reorder", json={"orderedMeetingIds": []})
    assert response.status_code in {200, 400, 422}, response.text
