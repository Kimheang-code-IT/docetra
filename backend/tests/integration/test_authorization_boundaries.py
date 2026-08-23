"""Restricted-user regressions for privilege, collection scope, and comments."""

from __future__ import annotations

import uuid
from collections.abc import Iterator
from contextlib import contextmanager

import httpx
import pytest

from tests.integration.conftest import (
    API_BASE,
    assert_envelope,
    create_restricted_user,
    login_user,
    mutate,
)

pytestmark = pytest.mark.integration


@contextmanager
def restricted_session(email: str, password: str) -> Iterator[httpx.Client]:
    with httpx.Client(base_url=API_BASE, timeout=20.0, follow_redirects=True) as client:
        login_user(client, email, password)
        yield client


def test_user_create_ignores_payload_privileges_and_requires_role(auth_client):
    denied = mutate(
        auth_client,
        "POST",
        "/api/v2/users",
        json={
            "email": f"no-role-{uuid.uuid4().hex[:8]}@example.com",
            "name": "No Role",
            "password": "Restricted1",
            "roleName": "Admin",
            "permissions": ["users.users.purge"],
            "status": "active",
        },
    )
    assert denied.status_code == 422, denied.text

    roles = assert_envelope(auth_client.get("/api/v2/users/roles", params={"limit": 200, "status": "all"}))["data"]
    super_role = next((row for row in roles if row.get("name") == "SuperAdmin"), None)
    assert super_role, "seeded SuperAdmin role is required"

    email = f"mgr-{uuid.uuid4().hex[:8]}@example.com"
    password = "Restricted1"
    create_restricted_user(
        auth_client,
        email=email,
        password=password,
        permission_rows=[
            {"documentType": "user", "actions": ["view", "create", "edit"], "level": 0},
            {"documentType": "role", "actions": ["view", "create", "edit"], "level": 0},
        ],
    )
    with restricted_session(email, password) as client:
        escalate = mutate(
            client,
            "POST",
            "/api/v2/users",
            json={
                "email": f"esc-{uuid.uuid4().hex[:8]}@example.com",
                "name": "Escalated",
                "password": "Restricted1",
                "roleId": super_role["id"],
                "status": "active",
            },
        )
        assert escalate.status_code == 403, escalate.text

        forged_role = mutate(
            client,
            "POST",
            "/api/v2/users/roles",
            json={"code": f"ADM{uuid.uuid4().hex[:6]}", "name": "Admin", "status": "active", "permissionRows": []},
        )
        assert forged_role.status_code == 403, forged_role.text


def test_cross_record_type_delete_and_stage_are_404(auth_client):
    document = assert_envelope(mutate(auth_client, "POST", "/api/v2/records/document", json={"title": f"Doc {uuid.uuid4().hex[:6]}"}))
    incoming = assert_envelope(mutate(auth_client, "POST", "/api/v2/records/incoming_document", json={"title": f"In {uuid.uuid4().hex[:6]}"}))
    email = f"docs-{uuid.uuid4().hex[:8]}@example.com"
    password = "Restricted1"
    create_restricted_user(
        auth_client,
        email=email,
        password=password,
        permission_rows=[{"documentType": "document", "actions": ["view", "delete", "transition", "comment"], "level": 0}],
    )
    with restricted_session(email, password) as client:
        cross_delete = mutate(client, "DELETE", f"/api/v2/records/document/{incoming['data']['id']}")
        assert cross_delete.status_code == 404, cross_delete.text
        cross_stage = mutate(client, "PATCH", f"/api/v2/records/document/{incoming['data']['id']}/stage", json={"stage": "done"})
        assert cross_stage.status_code == 404, cross_stage.text
        own_delete = mutate(client, "DELETE", f"/api/v2/records/document/{document['data']['id']}")
        assert own_delete.status_code < 400, own_delete.text


def test_cross_organization_type_delete_is_404(auth_client):
    department = assert_envelope(
        mutate(auth_client, "POST", "/api/v2/organizations/department", json={"name": f"Dept {uuid.uuid4().hex[:6]}"})
    )
    company = assert_envelope(
        mutate(auth_client, "POST", "/api/v2/organizations/company", json={"name": f"Co {uuid.uuid4().hex[:6]}"})
    )
    email = f"orgs-{uuid.uuid4().hex[:8]}@example.com"
    password = "Restricted1"
    create_restricted_user(
        auth_client,
        email=email,
        password=password,
        permission_rows=[{"documentType": "department", "actions": ["view", "delete"], "level": 0}],
    )
    with restricted_session(email, password) as client:
        cross = mutate(client, "DELETE", f"/api/v2/organizations/department/{company['data']['id']}")
        assert cross.status_code == 404, cross.text
        own = mutate(client, "DELETE", f"/api/v2/organizations/department/{department['data']['id']}")
        assert own.status_code < 400, own.text


def test_comment_and_activity_require_parent_and_author(auth_client):
    document = assert_envelope(mutate(auth_client, "POST", "/api/v2/records/document", json={"title": f"Cmt {uuid.uuid4().hex[:6]}"}))
    incoming = assert_envelope(mutate(auth_client, "POST", "/api/v2/records/incoming_document", json={"title": f"CmtIn {uuid.uuid4().hex[:6]}"}))
    admin_comment = assert_envelope(
        mutate(auth_client, "POST", f"/api/v2/records/document/{document['data']['id']}/comments", json={"body": "admin note"})
    )
    email = f"cmt-{uuid.uuid4().hex[:8]}@example.com"
    password = "Restricted1"
    create_restricted_user(
        auth_client,
        email=email,
        password=password,
        permission_rows=[{"documentType": "document", "actions": ["view", "comment"], "level": 0}],
    )
    with restricted_session(email, password) as client:
        stolen = mutate(
            client,
            "PATCH",
            f"/api/v2/records/document/{document['data']['id']}/comments/{admin_comment['data']['id']}",
            json={"body": "hijacked"},
        )
        assert stolen.status_code == 403, stolen.text

        cross_activity = client.get(f"/api/v2/records/document/{incoming['data']['id']}/activity")
        assert cross_activity.status_code == 404, cross_activity.text

        own = assert_envelope(
            mutate(client, "POST", f"/api/v2/records/document/{document['data']['id']}/comments", json={"body": "mine"})
        )
        edited = mutate(
            client,
            "PATCH",
            f"/api/v2/records/document/{document['data']['id']}/comments/{own['data']['id']}",
            json={"body": "mine edited"},
        )
        assert edited.status_code < 400, edited.text
