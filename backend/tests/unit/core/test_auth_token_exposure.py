"""Auth responses must not leak JWTs in JSON unless bearer mode opted in."""

from __future__ import annotations

from app.core.config import Settings
from app.modules.people_access.api.auth import _optional_tokens


def test_tokens_omitted_by_default():
    assert Settings().expose_auth_tokens is False
    assert _optional_tokens("access-jwt", "refresh-jwt") == {}


def test_tokens_present_only_when_opted_in(monkeypatch):
    monkeypatch.setattr(
        "app.modules.people_access.api.auth.settings",
        Settings(expose_auth_tokens=True),
    )
    assert _optional_tokens("access-jwt", "refresh-jwt") == {
        "token": "access-jwt",
        "refreshToken": "refresh-jwt",
    }
