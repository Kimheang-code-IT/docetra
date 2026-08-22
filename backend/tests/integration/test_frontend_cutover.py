"""Frontend cutover gaps: password reset, comments, limited-role 403."""

from __future__ import annotations

import uuid

import httpx
import pytest

from tests.integration.conftest import API_BASE, CSRF_COOKIE, assert_envelope, mutate

pytestmark = pytest.mark.integration


def _create_user(auth_client, *, email: str, password: str, permissions: list[str]) -> dict:
    created = mutate(
        auth_client,
        "POST",
        "/api/v2/users",
        json={
            "email": email,
            "name": "Cutover Limited",
            "password": password,
            "roleName": "User",
            "permissions": permissions,
            "status": "active",
        },
    )
    if created.status_code >= 400:
        pytest.skip(f"Could not create limited user for FE cutover tests: {created.status_code} {created.text}")
    return assert_envelope(created)["data"]


def test_forgot_password_family_is_csrf_exempt(api_client, auth_client):
    email = f"cutover-reset-{uuid.uuid4().hex[:10]}@example.com"
    password = "CutoverPass1"
    _create_user(auth_client, email=email, password=password, permissions=["dashboard.view"])

    forgot = api_client.post("/api/v2/auth/forgot-password", json={"email": email})
    assert forgot.status_code == 200, forgot.text
    body = assert_envelope(forgot)
    code = body["data"].get("debugCode")
    if not code:
        pytest.skip("Forgot-password debugCode is only returned when APP_ENV=development")

    verify = api_client.post(
        "/api/v2/auth/forgot-password/verify",
        json={"email": email, "code": code},
    )
    assert verify.status_code == 200, verify.text

    reset = api_client.post(
        "/api/v2/auth/forgot-password/reset",
        json={
            "email": email,
            "code": code,
            "password": "CutoverPass2",
            "passwordConfirmation": "CutoverPass2",
        },
    )
    assert reset.status_code == 200, reset.text

    login = api_client.post("/api/v2/auth/login", json={"email": email, "password": "CutoverPass2"})
    assert login.status_code == 200, login.text


def test_change_password_requires_csrf(auth_client):
    email = f"cutover-change-{uuid.uuid4().hex[:10]}@example.com"
    password = "CutoverPass1"
    _create_user(auth_client, email=email, password=password, permissions=["dashboard.view"])

    with httpx.Client(base_url=API_BASE, timeout=20.0, follow_redirects=True) as client:
        login = client.post("/api/v2/auth/login", json={"email": email, "password": password})
        assert login.status_code == 200, login.text
        assert client.cookies.get(CSRF_COOKIE)

        denied = client.post(
            "/api/v2/auth/change-password",
            json={
                "currentPassword": password,
                "password": "CutoverPass2",
                "passwordConfirmation": "CutoverPass2",
            },
        )
        assert denied.status_code == 403, denied.text

        changed = mutate(
            client,
            "POST",
            "/api/v2/auth/change-password",
            json={
                "currentPassword": password,
                "password": "CutoverPass2",
                "passwordConfirmation": "CutoverPass2",
            },
        )
        assert changed.status_code == 200, changed.text
        assert changed.json()["data"]["changed"] is True

        relogin = client.post("/api/v2/auth/login", json={"email": email, "password": "CutoverPass2"})
        assert relogin.status_code == 200, relogin.text


def test_comment_post_on_document_record(auth_client):
    title = f"Cutover comment doc {uuid.uuid4().hex[:8]}"
    created = mutate(auth_client, "POST", "/api/v2/records/document", json={"title": title})
    entity_id = assert_envelope(created)["data"]["id"]

    posted = mutate(
        auth_client,
        "POST",
        f"/api/v2/records/document/{entity_id}/comments",
        json={"body": "Frontend adapter comment"},
    )
    body = assert_envelope(posted)
    assert body["data"]["body"] == "Frontend adapter comment"
    assert body["data"]["entityId"] == entity_id


def test_limited_role_forbidden_on_document_list(auth_client):
    email = f"cutover-limited-{uuid.uuid4().hex[:10]}@example.com"
    password = "CutoverPass1"
    _create_user(auth_client, email=email, password=password, permissions=["dashboard.view"])

    with httpx.Client(base_url=API_BASE, timeout=20.0, follow_redirects=True) as client:
        login = client.post("/api/v2/auth/login", json={"email": email, "password": password})
        assert login.status_code == 200, login.text
        denied = client.get("/api/v2/records/document")
        assert denied.status_code == 403, denied.text
