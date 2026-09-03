"""Dashboard cache isolation: permission-filtered data must never leak."""

from __future__ import annotations

from types import SimpleNamespace

from app.modules.reporting_support.api.dashboard import dashboard_cache_key


def _user(uid: str, role: str, permissions: list[str]):
    return SimpleNamespace(id=uid, role=role, permissions=permissions)


def test_different_permissions_produce_different_cache_keys() -> None:
    user_a = _user("11111111-1111-1111-1111-111111111111", "clerk", ["records.documents.view"])
    user_b = _user("22222222-2222-2222-2222-222222222222", "clerk", ["records.meeting_history.view"])
    assert dashboard_cache_key(user_a) != dashboard_cache_key(user_b)


def test_same_user_same_permissions_is_cache_stable() -> None:
    user = _user("11111111-1111-1111-1111-111111111111", "clerk", ["b", "a"])
    again = _user("11111111-1111-1111-1111-111111111111", "clerk", ["a", "b"])
    assert dashboard_cache_key(user) == dashboard_cache_key(again)


def test_permission_change_invalidates_cache_key() -> None:
    before = _user("11111111-1111-1111-1111-111111111111", "clerk", ["records.documents.view"])
    after = _user("11111111-1111-1111-1111-111111111111", "clerk", ["records.documents.view", "dashboard.view"])
    assert dashboard_cache_key(before) != dashboard_cache_key(after)


def test_key_is_never_the_legacy_global_key() -> None:
    user = _user("11111111-1111-1111-1111-111111111111", "admin", [])
    assert dashboard_cache_key(user) != "dashboard:summary"
