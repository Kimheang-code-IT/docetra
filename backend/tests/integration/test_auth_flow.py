"""Auth + dashboard live checks (Docker API)."""

from __future__ import annotations

import pytest

from tests.integration.conftest import ADMIN_EMAIL, ADMIN_PASSWORD, CSRF_COOKIE, assert_envelope, login_admin, mutate

pytestmark = pytest.mark.integration


def test_login_issues_jwt_cookies_and_me_works(api_client):
    login = login_admin(api_client)
    body = login.json()
    assert body["data"]["user"]["email"] == ADMIN_EMAIL.lower()
    assert body["data"]["user"]["role"] == "SuperAdmin"
    assert "permissions" in body["data"]["user"]
    assert len(body["data"]["user"]["permissions"]) > 10

    cookie_names = set(api_client.cookies.keys())
    assert "docetra_session" in cookie_names
    assert "docetra_refresh" in cookie_names
    assert CSRF_COOKIE in cookie_names

    me = api_client.get("/api/v2/auth/me")
    assert me.status_code == 200, me.text
    assert me.json()["data"]["email"] == ADMIN_EMAIL.lower()

    refresh = mutate(api_client, "POST", "/api/v2/auth/refresh")
    assert refresh.status_code == 200, refresh.text
    assert refresh.json()["data"]["email"] == ADMIN_EMAIL.lower()


def test_dashboard_summary_after_login(auth_client):
    summary = auth_client.get("/api/v2/dashboard/summary")
    body = assert_envelope(summary)
    data = body["data"]
    assert "kpis" in data
    assert "workByStage" in data
    assert "recordsOverTime" in data
    assert "events" in data


def test_login_rejects_bad_password(api_client):
    response = api_client.post(
        "/api/v2/auth/login",
        json={"email": ADMIN_EMAIL, "password": "wrong-password"},
    )
    assert response.status_code == 401
