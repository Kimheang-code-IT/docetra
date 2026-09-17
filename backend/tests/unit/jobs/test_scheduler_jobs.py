"""Scheduler jobs — meeting reminders, export cleanup and reconcile tick."""

from datetime import datetime, timedelta, timezone
import uuid

import pytest

from app.modules.record.model import Entity, MeetingSchedule, Record
from app.modules.storage_integration.service import storage as storage_service
from app.jobs.scheduler import cleanup as cleanup_module
from app.jobs.scheduler import meeting_reminders as reminders_module
from app.jobs.scheduler import reconcile as reconcile_module
from tests.unit.support import FakeSession


def _now() -> datetime:
    return datetime.now(timezone.utc)


@pytest.mark.asyncio
async def test_due_meeting_reminders_publishes_and_marks_queued(monkeypatch):
    schedule = MeetingSchedule(
        id=uuid.uuid4(),
        meeting_id=uuid.uuid4(),
        job_key=str(uuid.uuid4()),
        run_at=_now() + timedelta(minutes=5),
        kind="reminder",
        status="scheduled",
    )
    published: list[tuple[str, dict]] = []

    async def fake_publish(topic, payload) -> None:
        published.append((topic, payload))

    monkeypatch.setattr(reminders_module, "publish", fake_publish)
    session = FakeSession(select_batches=[[schedule]])
    monkeypatch.setattr(reminders_module, "SessionLocal", lambda: session)

    await reminders_module.due_meeting_reminders()

    assert schedule.status == "queued"
    assert published[0][0] == "meeting.reminder.due"
    assert published[0][1]["meetingId"] == str(schedule.meeting_id)
    assert session.commits == 1


@pytest.mark.asyncio
async def test_due_meeting_reminders_falls_back_to_active_meetings(monkeypatch):
    record = Record(
        id=uuid.uuid4(),
        title="Standup",
        record_type_code="meeting_history",
        lifecycle="active",
        record_time=_now() + timedelta(minutes=10),
    )
    published: list[tuple[str, dict]] = []

    async def fake_publish(topic, payload) -> None:
        published.append((topic, payload))

    monkeypatch.setattr(reminders_module, "publish", fake_publish)
    session = FakeSession(select_batches=[[], [record]])
    monkeypatch.setattr(reminders_module, "SessionLocal", lambda: session)

    await reminders_module.due_meeting_reminders()

    assert published == [("meeting.reminder.due", {"meetingId": str(record.id), "at": record.record_time.isoformat()})]


@pytest.mark.asyncio
async def test_cleanup_deletes_expired_exports_and_objects(monkeypatch):
    row = Entity(id=uuid.uuid4(), resource="export-jobs", payload={"objectKey": "exports/1.csv"})
    deleted: list[str] = []

    async def fake_delete(key, *_a, **_k) -> None:
        deleted.append(key)

    monkeypatch.setattr(storage_service, "delete_object", fake_delete)
    session = FakeSession(select_batches=[[row]])
    monkeypatch.setattr(cleanup_module, "SessionLocal", lambda: session)

    await cleanup_module.cleanup_expired_exports()

    assert deleted == ["exports/1.csv"]
    assert session.deleted == [row]
    assert session.commits == 1


@pytest.mark.asyncio
async def test_cleanup_skips_row_when_object_delete_fails(monkeypatch):
    row = Entity(id=uuid.uuid4(), resource="export-jobs", payload={"objectKey": "exports/2.csv"})

    async def failing_delete(*_a, **_k) -> None:
        raise RuntimeError("minio down")

    monkeypatch.setattr(storage_service, "delete_object", failing_delete)
    session = FakeSession(select_batches=[[row]])
    monkeypatch.setattr(cleanup_module, "SessionLocal", lambda: session)

    await cleanup_module.cleanup_expired_exports()

    assert session.deleted == []
    assert session.commits == 1


@pytest.mark.asyncio
async def test_reconcile_publishes_tick(monkeypatch):
    calls = []

    async def fake_tick() -> None:
        calls.append(True)

    monkeypatch.setattr(reconcile_module, "publish_tick", fake_tick)
    await reconcile_module.reconcile()
    assert calls == [True]
