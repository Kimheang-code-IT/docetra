"""Outbox publisher — publish, attempt accounting and dead-letter logging."""

import uuid

import pytest

from app.core.config import settings
from app.platform.messaging.model import Outbox
from app.jobs.consumers import outbox as outbox_module
from tests.unit.support import FakeChannel, FakeExchange, FakeSession


def _row(attempts: int = 0) -> Outbox:
    return Outbox(id=uuid.uuid4(), topic="entity.created", payload={"id": "1"}, attempts=attempts)


@pytest.mark.asyncio
async def test_publish_marks_rows_processed(monkeypatch):
    row = _row()
    session = FakeSession(select_batches=[[row]])
    monkeypatch.setattr(outbox_module, "SessionLocal", lambda: session)
    channel = FakeChannel()

    await outbox_module.publish_outbox(channel)

    assert row.processed_at is not None
    assert row.attempts == 1
    assert session.commits == 1
    assert channel.exchange.published[0]["routing_key"] == "entity.created"


@pytest.mark.asyncio
async def test_publish_failure_increments_attempts(monkeypatch):
    row = _row(attempts=1)
    session = FakeSession(select_batches=[[row]])
    monkeypatch.setattr(outbox_module, "SessionLocal", lambda: session)
    channel = FakeChannel(FakeExchange(fail=True))

    await outbox_module.publish_outbox(channel)

    assert row.processed_at is None
    assert row.attempts == 2
    assert not session.added


@pytest.mark.asyncio
async def test_publish_failure_at_ceiling_logs_system_error(monkeypatch):
    row = _row(attempts=settings.job_max_retries - 1)
    session = FakeSession(select_batches=[[row]])
    monkeypatch.setattr(outbox_module, "SessionLocal", lambda: session)
    channel = FakeChannel(FakeExchange(fail=True))

    await outbox_module.publish_outbox(channel)

    assert row.attempts == settings.job_max_retries
    assert row.processed_at is not None
    logs = [obj for obj in session.added if getattr(obj, "resource", None) == "system-logs"]
    assert len(logs) == 1
    assert logs[0].payload["action"] == "outbox.failed"
    assert logs[0].payload["topic"] == "entity.created"


@pytest.mark.asyncio
async def test_publish_declares_durable_topic_exchange(monkeypatch):
    session = FakeSession(select_batches=[[]])
    monkeypatch.setattr(outbox_module, "SessionLocal", lambda: session)
    channel = FakeChannel()

    await outbox_module.publish_outbox(channel)

    from app.jobs.topology import EVENT_EXCHANGE

    assert channel.declared[0][0] == EVENT_EXCHANGE
    assert channel.declared[0][2] is True
