import uuid
from datetime import datetime, timezone

from app.models.record import Record, RecordDetail
from app.modules.record.services.serializer import details_map, record_to_payload, value_from_detail


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
