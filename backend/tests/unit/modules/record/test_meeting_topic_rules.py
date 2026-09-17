"""Unit tests for meeting topic assignment rules.

Covers:
- assign/reorder topic validation (invalid id, missing, wrong type, archived)
- deleted/purged topics detach their child meetings (no dangling topicId)
"""

from __future__ import annotations

import uuid

import pytest
from fastapi import HTTPException

from app.modules.record.services import meeting as meeting_mod
from app.modules.record.services import record_collections as rc_mod
from app.modules.record.services.record_collections import RecordApplicationService


class _FakeRecord:
    def __init__(self, *, lifecycle="active", status=1, code="meeting_topic", type_id=None):
        self.id = uuid.uuid4()
        self.lifecycle = lifecycle
        self.status = status
        self.record_type_code = code
        self.record_type_id = type_id


class _FakeType:
    def __init__(self, code):
        self.code = code


class _FakeDb:
    """Minimal AsyncSession stand-in: only .get() is needed by _resolve_topic."""

    def __init__(self, rows=None, types=None):
        self._rows = rows or {}
        self._types = types or {}

    async def get(self, model, uid):
        from app.modules.record.model import Record, RecordType

        if model is Record:
            return self._rows.get(uid)
        if model is RecordType:
            return self._types.get(uid)
        return None


@pytest.mark.asyncio
async def test_resolve_topic_none_for_unassign():
    db = _FakeDb()
    assert await meeting_mod._resolve_topic(db, None) is None
    assert await meeting_mod._resolve_topic(db, "") is None
    assert await meeting_mod._resolve_topic(db, "   ") is None


@pytest.mark.asyncio
async def test_resolve_topic_rejects_invalid_id():
    db = _FakeDb()
    with pytest.raises(HTTPException) as err:
        await meeting_mod._resolve_topic(db, "not-a-uuid")
    assert err.value.status_code == 422


@pytest.mark.asyncio
async def test_resolve_topic_404_when_missing_or_deleted():
    topic = _FakeRecord()
    dead = _FakeRecord(lifecycle="deleted", status=0)
    db = _FakeDb(rows={topic.id: topic, dead.id: dead})
    with pytest.raises(HTTPException) as err:
        await meeting_mod._resolve_topic(db, str(uuid.uuid4()))
    assert err.value.status_code == 404
    with pytest.raises(HTTPException) as err:
        await meeting_mod._resolve_topic(db, str(dead.id))
    assert err.value.status_code == 404


@pytest.mark.asyncio
async def test_resolve_topic_rejects_non_topic_record():
    meeting = _FakeRecord(code="meeting_history")
    db = _FakeDb(rows={meeting.id: meeting})
    with pytest.raises(HTTPException) as err:
        await meeting_mod._resolve_topic(db, str(meeting.id))
    assert err.value.status_code == 422


@pytest.mark.asyncio
async def test_resolve_topic_resolves_code_via_type_row():
    """record_type_code may be empty; the type row decides."""
    type_id = uuid.uuid4()
    topic = _FakeRecord(code=None, type_id=type_id)
    db = _FakeDb(rows={topic.id: topic}, types={type_id: _FakeType("meeting_topic")})
    resolved = await meeting_mod._resolve_topic(db, str(topic.id))
    assert resolved is topic


@pytest.mark.asyncio
async def test_resolve_topic_rejects_archived():
    topic = _FakeRecord(status=2, lifecycle="archived")
    db = _FakeDb(rows={topic.id: topic})
    with pytest.raises(HTTPException) as err:
        await meeting_mod._resolve_topic(db, str(topic.id))
    assert err.value.status_code == 422


@pytest.mark.asyncio
async def test_resolve_topic_accepts_active_topic():
    topic = _FakeRecord()
    db = _FakeDb(rows={topic.id: topic})
    assert await meeting_mod._resolve_topic(db, str(topic.id)) is topic


# ---------------------------------------------------------------------------
# Topic deletion detaches children


class _CapturingDb:
    """Captures executed statements instead of hitting a database."""

    def __init__(self, child_ids):
        self.child_ids = child_ids
        self.executed = []

    async def scalars(self, _stmt):
        class _Result:
            def __init__(self, ids):
                self._ids = ids

            def all(self):
                return list(self._ids)

        return _Result(self.child_ids)

    async def execute(self, stmt):
        self.executed.append(stmt)


def _service_with_type_code(code):
    class _Host:
        def resolve_type_code(self):
            return code

        async def get_record_row_or_404(self, db, entity_id, user=None):
            return _Row()

        def _assert_version(self, current, expected):
            return None

    class _Row:
        id = uuid.uuid4()
        version = 3
        lifecycle = "active"
        status = 1
        deleted_at = None

    return RecordApplicationService(_Host())


@pytest.mark.asyncio
async def test_clear_topic_children_updates_rows_and_details():
    db = _CapturingDb([uuid.uuid4(), uuid.uuid4()])
    service = _service_with_type_code("meeting_topic")
    await service._clear_topic_children(db, uuid.uuid4())
    assert len(db.executed) == 2, "expected one record update + one detail delete"


@pytest.mark.asyncio
async def test_clear_topic_children_noop_without_children():
    db = _CapturingDb([])
    service = _service_with_type_code("meeting_topic")
    await service._clear_topic_children(db, uuid.uuid4())
    assert db.executed == []


@pytest.mark.asyncio
async def test_soft_delete_only_clears_children_for_topics(monkeypatch):
    """The detach hook fires on the meeting_topic type, not other types."""
    called = {"n": 0}

    async def fake_clear(self, db, topic_id):
        called["n"] += 1

    monkeypatch.setattr(RecordApplicationService, "_clear_topic_children", fake_clear)

    class _Db:
        async def flush(self):
            pass

    service = _service_with_type_code("meeting_topic")
    await service.soft_delete(_Db(), None, "x", 3)
    assert called["n"] == 1

    service = _service_with_type_code("incoming_document")
    await service.soft_delete(_Db(), None, "x", 3)
    assert called["n"] == 1, "non-topic delete must not touch topic children"
