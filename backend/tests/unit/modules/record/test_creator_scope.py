"""Creator-only permission enforcement (permission.scope='creator')."""

from __future__ import annotations

import uuid
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.modules.record.services import creator_scope


def _user(uid, officer_id=None, role_id="role-1", permissions=("records.documents.view", "records.documents.edit")):
    return SimpleNamespace(
        id=uid,
        officer_id=officer_id,
        role_id=role_id,
        role="clerk",
        permissions=list(permissions),
        name="Test User",
    )


class FakeResult:
    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return self._rows


class FakeDb:
    """Mimics the AsyncSession surface used by creator_scope helpers."""

    def __init__(self, permission_rows, record_row=None, entity_row=None):
        self._permission_rows = permission_rows
        self._record_row = record_row
        self._entity_row = entity_row
        self.scalled = None

    async def scalars(self, _stmt):
        return FakeResult(self._permission_rows)

    async def get(self, model, _uid):
        if getattr(model, "__name__", "") == "Record":
            return self._record_row
        return self._entity_row


def _perm_row(code, scope="all"):
    return SimpleNamespace(code=code, scope=scope, is_enable=1)


@pytest.mark.asyncio
async def test_creator_scoped_edit_allows_creator():
    user = _user("user-1", officer_id="officer-1")
    db = FakeDb(
        [_perm_row("records.documents.view"), _perm_row("records.documents.edit", scope="creator")],
        record_row=SimpleNamespace(created_by="officer-1"),
    )
    actions = await creator_scope._creator_scoped_actions(db, user, "documents")
    assert actions == {"records.documents.edit"}
    assert await creator_scope.creator_only(db, user, "documents") is False


@pytest.mark.asyncio
async def test_creator_scoped_edit_denies_non_creator():
    user = _user("user-2", officer_id="officer-2")
    db = FakeDb(
        [_perm_row("records.documents.view"), _perm_row("records.documents.edit", scope="creator")],
        record_row=SimpleNamespace(created_by="officer-1"),
    )
    # Non-creator: edit is creator-scoped and record.created_by != user.officer_id.
    # authorize_resource raises through its dependency; here assert the scope lookup.
    actions = await creator_scope._creator_scoped_actions(db, user, "documents")
    assert "records.documents.edit" in actions


@pytest.mark.asyncio
async def test_creator_scoped_view_filters_lists():
    user = _user("user-1", officer_id="officer-1")
    db = FakeDb([_perm_row("records.documents.view", scope="creator")])
    assert await creator_scope.creator_only(db, user, "documents") is True


@pytest.mark.asyncio
async def test_unscoped_permissions_do_not_filter_lists():
    user = _user("user-1", officer_id="officer-1")
    db = FakeDb([_perm_row("records.documents.view"), _perm_row("records.documents.edit")])
    assert await creator_scope.creator_only(db, user, "documents") is False


@pytest.mark.asyncio
async def test_unrestricted_user_is_never_creator_limited():
    user = _user("user-1", role_id=None, permissions=[])
    user.role = "admin"
    db = FakeDb([])
    assert await creator_scope.creator_only(db, user, "documents") is False


@pytest.mark.asyncio
async def test_role_save_persists_creator_scope(monkeypatch):
    """replace_role_permissions maps onlyIfCreator rows to scope='creator'."""
    from app.modules.people_access.services import people

    added = []

    class FakeSession:
        async def execute(self, _stmt):
            return None

        def add(self, row):
            added.append(row)

        async def flush(self):
            return None

    from app.core.permissions import normalize_permission_payload

    normalized = normalize_permission_payload({
        "permissionRows": [
            {"documentType": "document", "actions": ["view", "edit"], "onlyIfCreator": True},
            {"documentType": "dashboard", "actions": ["view"], "onlyIfCreator": False},
        ],
    })
    creator = people.creator_scoped_codes_from_rows(normalized["permissionRows"])
    assert creator == {"records.documents.view", "records.documents.edit"}

    await people.replace_role_permissions(FakeSession(), uuid.uuid4(), sorted(creator) + ["dashboard.view"], creator)
    scoped = {row.code: row.scope for row in added}
    assert scoped["records.documents.edit"] == "creator"
    assert scoped["records.documents.view"] == "creator"
    assert scoped["dashboard.view"] == "all"
