"""Organization-scoped record type resolution."""

import uuid
from datetime import datetime, timezone
from types import SimpleNamespace

from app.modules.record.model import Record, RecordAttribute, RecordDetail, RecordType, RecordTypePermission
from app.modules.record.services.serializer import record_to_payload
from app.modules.record.services.type_access import OWNER, SHARED, pick_type_for_code


def _type(code: str, created_at: datetime, type_id: uuid.UUID | None = None) -> SimpleNamespace:
    return SimpleNamespace(id=type_id or uuid.uuid4(), code=code, created_at=created_at)


def test_pick_type_prefers_owner_over_older_shared():
    older = _type("document", datetime(2024, 1, 1, tzinfo=timezone.utc))
    newer_owner = _type("document", datetime(2025, 1, 1, tzinfo=timezone.utc))
    picked = pick_type_for_code([(older, SHARED), (newer_owner, OWNER)], "document")
    assert picked is newer_owner


def test_pick_type_falls_back_to_oldest_when_no_owner():
    older = _type("document", datetime(2024, 1, 1, tzinfo=timezone.utc))
    newer = _type("document", datetime(2025, 1, 1, tzinfo=timezone.utc))
    picked = pick_type_for_code([(newer, SHARED), (older, SHARED)], "document")
    assert picked is older


def test_pick_type_ignores_other_codes():
    row = _type("meeting_history", datetime(2024, 1, 1, tzinfo=timezone.utc))
    assert pick_type_for_code([(row, OWNER)], "document") is None


def test_record_type_and_attribute_code_are_not_unique():
    assert RecordType.__table__.c.id.primary_key
    assert RecordAttribute.__table__.c.id.primary_key
    assert not RecordType.__table__.c.code.unique
    assert not RecordAttribute.__table__.c.code.unique
    assert Record.__table__.c.record_type_id is not None
    assert RecordDetail.__table__.c.record_attribute_id is not None
    constraint_names = {item.name for item in RecordTypePermission.__table__.constraints}
    assert "uq_record_type_permission_org_type" in constraint_names


def test_record_to_payload_includes_record_type_id():
    now = datetime.now(timezone.utc)
    type_id = uuid.uuid4()
    row = Record(
        id=uuid.uuid4(),
        title="Brief",
        version=1,
        lifecycle="active",
        status=1,
        record_type_id=type_id,
        record_type_code="document",
    )
    row.created_at = now
    row.updated_at = now
    payload = record_to_payload(row)
    assert payload["recordTypeId"] == str(type_id)
    assert payload["recordTypeCode"] == "document"
