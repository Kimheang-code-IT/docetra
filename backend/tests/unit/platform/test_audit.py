"""Platform audit trail — append-only writes via the record stamp helper."""

from types import SimpleNamespace
import uuid

import pytest

from app.modules.record.domain.constants import READ_ONLY
from app.modules.record.model import Activity, Entity
from app.modules.record.services import stamp as stamp_service
from app.platform.audit.model import AuditLog
from app.platform.messaging.model import Outbox
from tests.unit.support import FakeSession


def _entity(resource: str, **payload) -> Entity:
    return Entity(id=uuid.uuid4(), resource=resource, payload={"title": "Title", **payload})


def _user() -> SimpleNamespace:
    return SimpleNamespace(id=uuid.uuid4(), officer_id=uuid.uuid4())


@pytest.mark.asyncio
async def test_audit_writes_activity_outbox_and_audit_log():
    session = FakeSession()
    entity = _entity("documents")
    user = _user()

    await stamp_service.audit(session, entity, user, "created", "created a document")

    kinds = [type(obj) for obj in session.added]
    assert Activity in kinds
    assert Outbox in kinds
    assert AuditLog in kinds

    outbox = next(obj for obj in session.added if isinstance(obj, Outbox))
    assert outbox.topic == "entity.created"
    assert outbox.payload == {"resource": "documents", "id": str(entity.id)}

    log = next(obj for obj in session.added if isinstance(obj, AuditLog))
    assert log.action_code == "created"
    assert log.table_name == "documents"
    assert log.row_id == entity.id
    assert log.created_by == user.officer_id
    assert log.message == "created a document"
    assert log.source_log == "record"
    assert log.status_code == "success"
    assert log.detail_data["entityTitle"] == "Title"
    assert log.detail_data["entityType"] == "documents"
    assert log.detail_data["correlationId"] == str(entity.id)
    assert log.detail_data["occurredAt"]


@pytest.mark.asyncio
async def test_audit_tags_portal_resources():
    session = FakeSession()
    await stamp_service.audit(session, _entity("file-uploads"), _user(), "uploaded", "uploaded a file")
    log = next(obj for obj in session.added if isinstance(obj, AuditLog))
    assert log.source_log == "portal"


@pytest.mark.asyncio
@pytest.mark.parametrize("resource", sorted(READ_ONLY))
async def test_audit_skips_audit_log_for_read_only_resources(resource):
    session = FakeSession()
    await stamp_service.audit(session, _entity(resource), _user(), "viewed", "viewed")
    assert not any(isinstance(obj, AuditLog) for obj in session.added)
    assert any(isinstance(obj, Outbox) for obj in session.added)


@pytest.mark.asyncio
async def test_audit_never_commits():
    session = FakeSession()
    await stamp_service.audit(session, _entity("documents"), _user(), "updated", "updated")
    assert session.commits == 0
