"""Shared fixtures for live Docker API integration tests."""

from __future__ import annotations

import os
import re
import time
import uuid
from collections.abc import Iterator
from typing import Any

import httpx
import pytest

API_BASE = os.getenv("DOCETRA_API_BASE", "http://127.0.0.1:8000").rstrip("/")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@gmail.com")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "123456")
CSRF_HEADER = "X-CSRF-Token"
CSRF_COOKIE = "XSRF-TOKEN"


def api_up() -> bool:
    try:
        response = httpx.get(f"{API_BASE}/ready", timeout=3.0)
        return response.status_code == 200
    except httpx.HTTPError:
        return False


def assert_envelope(response: httpx.Response, *, require_meta: bool = False) -> dict[str, Any]:
    assert response.status_code < 400, response.text
    body = response.json()
    assert isinstance(body, dict), body
    assert "data" in body, body
    if require_meta:
        assert "meta" in body, body
        assert isinstance(body["meta"], dict), body["meta"]
    return body


_ITEM_PATH = re.compile(
    r"^(?P<item>.*/[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})"
    r"(?P<suffix>/(?:archive|restore|purge|stage))?$"
)


def mutate(
    client: httpx.Client,
    method: str,
    path: str,
    *,
    json: dict[str, Any] | None = None,
    data: Any = None,
    files: Any = None,
    headers: dict[str, str] | None = None,
    attach_version: bool = True,
    **kwargs: Any,
) -> httpx.Response:
    """Issue a mutating request with double-submit CSRF header from the session cookie."""
    xsrf = client.cookies.get(CSRF_COOKIE)
    assert xsrf, f"Missing {CSRF_COOKIE} cookie — login first"
    merged = {**(headers or {}), CSRF_HEADER: xsrf}
    payload = dict(json) if json is not None else None
    params = dict(kwargs.pop("params", None) or {})
    method_u = method.upper()
    match = _ITEM_PATH.match(path) if attach_version else None
    suffix = match.group("suffix") if match else None
    needs_version = bool(
        match
        and (
            method_u in {"PATCH", "PUT", "DELETE"}
            or (method_u == "POST" and suffix in {"/archive", "/restore"})
        )
    )
    if needs_version and match:
        current = client.get(match.group("item"))
        if current.status_code < 400:
            version = (current.json().get("data") or {}).get("version")
            if version is not None:
                merged["If-Match"] = str(version)
                params.setdefault("version", version)
                if payload is None:
                    payload = {"version": version}
                else:
                    payload.setdefault("version", version)
    return client.request(
        method_u,
        path,
        json=payload,
        data=data,
        files=files,
        headers=merged,
        params=params or None,
        **kwargs,
    )


def login_admin(client: httpx.Client, *, attempts: int = 8) -> httpx.Response:
    """Login with backoff — Docker LOGIN_RATE_LIMIT is low for rapid fixture logins."""
    last: httpx.Response | None = None
    for attempt in range(attempts):
        last = client.post(
            "/api/v2/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        )
        if last.status_code == 200:
            return last
        if last.status_code == 429:
            time.sleep(min(2 ** attempt, 20))
            continue
        break
    assert last is not None
    assert last.status_code == 200, last.text
    return last


def login_user(client: httpx.Client, email: str, password: str, *, attempts: int = 8) -> httpx.Response:
    last: httpx.Response | None = None
    for attempt in range(attempts):
        last = client.post("/api/v2/auth/login", json={"email": email, "password": password})
        if last.status_code == 200:
            return last
        if last.status_code == 429:
            time.sleep(min(2 ** attempt, 20))
            continue
        break
    assert last is not None
    assert last.status_code == 200, last.text
    return last


def create_role(auth_client: httpx.Client, *, name: str, permission_rows: list[dict[str, Any]]) -> dict[str, Any]:
    created = mutate(
        auth_client,
        "POST",
        "/api/v2/users/roles",
        json={
            "code": f"R{uuid.uuid4().hex[:10].upper()}",
            "name": name,
            "status": "active",
            "permissionRows": permission_rows,
        },
    )
    assert created.status_code < 400, created.text
    return assert_envelope(created)["data"]


def create_restricted_user(
    auth_client: httpx.Client,
    *,
    email: str,
    password: str,
    permission_rows: list[dict[str, Any]],
    name: str = "Restricted",
) -> dict[str, Any]:
    role = create_role(auth_client, name=f"Lim {email.split('@')[0][-12:]}", permission_rows=permission_rows)
    created = mutate(
        auth_client,
        "POST",
        "/api/v2/users",
        json={
            "email": email,
            "name": name,
            "password": password,
            "roleId": role["id"],
            "status": "active",
            "roleName": "Admin",
            "permissions": ["users.users.purge"],
        },
    )
    assert created.status_code < 400, created.text
    data = assert_envelope(created)["data"]
    assert data.get("roleId") == role["id"]
    assert data.get("roleName") != "Admin"
    assert "users.users.purge" not in (data.get("permissions") or [])
    return data


@pytest.fixture(scope="session")
def require_api():
    if not api_up():
        pytest.skip(f"API not reachable at {API_BASE}")


@pytest.fixture
def api_client(require_api) -> Iterator[httpx.Client]:
    with httpx.Client(base_url=API_BASE, timeout=20.0, follow_redirects=True) as client:
        yield client


@pytest.fixture(scope="session")
def auth_client(require_api) -> Iterator[httpx.Client]:
    """One shared admin session for the whole integration run (avoids login 429)."""
    with httpx.Client(base_url=API_BASE, timeout=20.0, follow_redirects=True) as client:
        login_admin(client)
        assert client.cookies.get("docetra_session")
        assert client.cookies.get(CSRF_COOKIE)
        yield client
