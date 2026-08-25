import pytest
from fastapi import HTTPException

from app.core.security import bearer_token, csrf_protect


def make_request(headers: dict[str, str] | None = None, method: str = "POST", path: str = "/api/v2/records") -> object:
    from starlette.requests import Request

    scope = {
        "type": "http",
        "method": method,
        "path": path,
        "headers": [(key.lower().encode(), value.encode()) for key, value in (headers or {}).items()],
        "query_string": b"",
    }
    return Request(scope)


def test_bearer_token_extracts_from_authorization_header():
    request = make_request({"Authorization": "Bearer abc.def.ghi"})
    assert bearer_token(request) == "abc.def.ghi"


def test_bearer_token_is_case_insensitive_on_scheme():
    request = make_request({"Authorization": "bearer abc.def.ghi"})
    assert bearer_token(request) == "abc.def.ghi"


def test_bearer_token_returns_none_for_other_schemes():
    assert bearer_token(make_request({"Authorization": "Basic dXNlcjpwYXNz"})) is None
    assert bearer_token(make_request({"Authorization": "Bearer "})) is None
    assert bearer_token(make_request()) is None


async def test_csrf_protect_allows_bearer_authenticated_requests_without_cookies():
    request = make_request({"Authorization": "Bearer abc.def.ghi"})
    await csrf_protect(request)


async def test_csrf_protect_rejects_cookie_requests_without_headers():
    with pytest.raises(HTTPException) as error:
        await csrf_protect(make_request())
    assert error.value.status_code == 403
