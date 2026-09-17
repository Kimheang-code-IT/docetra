import uuid
from datetime import datetime, timezone

from app.modules.record.model import Record, RecordDetail, RecordType
from app.modules.record.services.record_collections import _topic_id_filter
from app.modules.record.services.serializer import (
    apply_core_fields,
    details_map,
    record_to_payload,
    record_type_display_name,
    value_from_detail,
)


def test_value_from_detail_prefers_typed_columns():
    row = RecordDetail(record_id=uuid.uuid4(), record_attribute_code="flag", value_boolean=True)
    assert value_from_detail(row) is True


def test_details_map_groups_by_record_id():
    first = uuid.uuid4()
    second = uuid.uuid4()
    rows = [
        RecordDetail(record_id=first, record_attribute_code="a", value_string="one"),
        RecordDetail(record_id=first, record_attribute_code="b", value_number=2),
        RecordDetail(record_id=second, record_attribute_code="a", value_string="other"),
    ]
    grouped = details_map(rows)
    assert grouped[first]["a"] == "one"
    assert grouped[first]["b"] == 2.0
    assert grouped[second]["a"] == "other"


def test_record_to_payload_includes_core_and_details():
    now = datetime.now(timezone.utc)
    row = Record(id=uuid.uuid4(), title="Brief", version=4, lifecycle="active", status=1)
    row.created_at = now
    row.updated_at = now
    payload = record_to_payload(row, {"office": "cabinet"})
    assert payload["title"] == "Brief"
    assert payload["version"] == 4
    assert payload["office"] == "cabinet"
    assert payload["status"] == "active"


def test_meeting_history_payload_aliases_topic_and_meeting_date():
    now = datetime.now(timezone.utc)
    topic_id = uuid.uuid4()
    row = Record(
        id=uuid.uuid4(),
        title="Meeting 11bd304b",
        version=1,
        lifecycle="active",
        status=1,
        record_type_code="meeting_history",
        record_time=now,
        parent_record=topic_id,
    )
    row.created_at = now
    row.updated_at = now
    payload = record_to_payload(row, {})
    assert payload["meetingDate"] == payload["recordTime"]
    assert payload["topicId"] == str(topic_id)
    assert payload["parentId"] == str(topic_id)


def test_apply_core_fields_uses_topic_id_as_parent():
    row = Record(id=uuid.uuid4(), title="Meeting", version=1, lifecycle="active", status=1)
    topic_id = uuid.uuid4()
    apply_core_fields(row, {"topicId": str(topic_id), "meetingDate": "2026-08-28T10:54:00Z"})
    assert row.parent_record == topic_id
    apply_core_fields(row, {"topicId": None})
    assert row.parent_record is None


def test_topic_id_filter_ignores_blank_and_rejects_invalid():
    assert _topic_id_filter(None) is None
    assert _topic_id_filter("") is None
    assert _topic_id_filter("not-a-uuid") is not None


def test_record_type_display_name_prefers_nam_then_code():
    named = RecordType(code="incoming_document", nam="Incoming letter")
    unnamed = RecordType(code="outgoing_document", nam=None)
    assert record_type_display_name(named) == "Incoming letter"
    assert record_type_display_name(unnamed) == "Outgoing Document"
    assert record_type_display_name(None, "meeting_history") == "Meeting History"
    assert record_type_display_name(None, None) == ""
