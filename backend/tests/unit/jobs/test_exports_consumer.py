"""Export consumer — status transitions, retry ceiling, lock and failure handling."""

import uuid

import pytest

from app.core.config import settings
from app.modules.record.model import Entity
from app.modules.reporting_support.services import export as export_service
from app.jobs.consumers import exports as exports_module
from tests.unit.support import FakeSession


def _job(**payload) -> Entity:
    return Entity(
        id=uuid.uuid4(),
        resource="export-jobs",
        status="active",
        payload={"status": "queued", "attempts": 0, **payload},
    )


async def _true(*_a, **_k) -> bool:
    return True


async def _none(*_a, **_k) -> None:
    return None


def _loose(monkeypatch) -> None:
    monkeypatch.setattr(exports_module, "_acquire_lock", _true)
    monkeypatch.setattr(exports_module, "_release_lock", _none)
    monkeypatch.setattr(exports_module, "_cache_status", _none)
    monkeypatch.setattr(exports_module, "_drop_status", _none)


@pytest.mark.asyncio
async def test_execute_transitions_to_processing(monkeypatch):
    _loose(monkeypatch)
    monkeypatch.setattr(export_service, "generate_export", _none)
    row = _job()
    db = FakeSession()
    await exports_module._execute(db, row)

    assert row.payload["status"] == "processing"
    assert row.payload["attempts"] == 1
    assert db.flushes >= 1


@pytest.mark.asyncio
async def test_execute_completes_when_generator_succeeds(monkeypatch):
    async def fake_generate(_db, row) -> None:
        row.payload = {**row.payload, "status": "completed"}

    _loose(monkeypatch)
    monkeypatch.setattr(export_service, "generate_export", fake_generate)

    row = _job()
    await exports_module._execute(FakeSession(), row)
    assert row.payload["status"] == "completed"


@pytest.mark.asyncio
async def test_execute_retry_ceiling_fails_without_running(monkeypatch):
    called: list[str] = []

    async def tracking_export(_db, _row) -> None:
        called.append("export")

    _loose(monkeypatch)
    monkeypatch.setattr(export_service, "generate_export", tracking_export)

    row = _job(attempts=settings.job_max_retries)
    await exports_module._execute(FakeSession(), row)

    assert row.payload["status"] == "failed"
    assert row.payload["error"] == "Max export attempts reached"
    assert called == []


@pytest.mark.asyncio
async def test_execute_records_failure_and_truncates_error(monkeypatch):
    async def boom(_db, _row) -> None:
        raise RuntimeError("x" * 900)

    _loose(monkeypatch)
    monkeypatch.setattr(export_service, "generate_export", boom)

    row = _job()
    await exports_module._execute(FakeSession(), row)

    assert row.payload["status"] == "failed"
    assert len(row.payload["error"]) == 500
    assert row.payload["completedAt"]


@pytest.mark.asyncio
async def test_execute_skips_when_lock_held(monkeypatch):
    monkeypatch.setattr(exports_module, "_acquire_lock", _false)
    monkeypatch.setattr(exports_module, "_cache_status", _none)

    row = _job()
    await exports_module._execute(FakeSession(), row)
    assert row.payload["status"] == "queued"


@pytest.mark.asyncio
async def test_execute_ignores_terminal_statuses(monkeypatch):
    monkeypatch.setattr(exports_module, "generate_export", _none, raising=False)
    row = _job(status="completed")
    await exports_module._execute(FakeSession(), row)
    assert row.payload["status"] == "completed"


@pytest.mark.asyncio
async def test_handle_export_execute_ignores_invalid_job_id():
    await exports_module.handle_export_execute({"jobId": "not-a-uuid"})


@pytest.mark.asyncio
async def test_handle_export_execute_ignores_wrong_resource(monkeypatch):
    monkeypatch.setattr(exports_module, "_execute", _none)
    row = Entity(id=uuid.uuid4(), resource="documents", payload={"status": "queued"})
    session = FakeSession(get_row=row)
    monkeypatch.setattr(exports_module, "SessionLocal", lambda: session)
    await exports_module.handle_export_execute({"jobId": str(row.id)})


@pytest.mark.asyncio
async def test_handle_export_execute_runs_matching_job(monkeypatch):
    seen: list[uuid.UUID] = []

    async def fake_execute(_db, row) -> None:
        seen.append(row.id)

    monkeypatch.setattr(exports_module, "_execute", fake_execute)
    row = _job()
    session = FakeSession(get_row=row)
    monkeypatch.setattr(exports_module, "SessionLocal", lambda: session)
    await exports_module.handle_export_execute({"jobId": str(row.id)})

    assert seen == [row.id]
    assert session.commits == 1


@pytest.mark.asyncio
async def test_complete_exports_executes_selected_rows(monkeypatch):
    rows = [_job(), _job(status="processing")]
    seen: list[uuid.UUID] = []

    async def fake_execute(_db, row) -> None:
        seen.append(row.id)

    monkeypatch.setattr(exports_module, "_execute", fake_execute)
    session = FakeSession(select_batches=[rows])
    monkeypatch.setattr(exports_module, "SessionLocal", lambda: session)
    await exports_module.complete_exports()

    assert seen == [row.id for row in rows]
    assert session.commits == 1


async def _false(*_a, **_k) -> bool:
    return False
