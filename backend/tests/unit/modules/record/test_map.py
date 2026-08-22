"""record module — maps, constants, permission prefixes."""

from app.modules.record.domain import constants
from app.modules.record.domain.map import (
    TYPE_UI_DEFAULTS,
    is_valid_type_code,
    merge_type_ui_payload,
    permission_prefix_for_type_code,
)
from app.modules.record.domain.schemas import MeetingReorder, RecordPayload
from app.shared.pagination import parse_limit


def test_builtin_type_codes_valid():
    for code in TYPE_UI_DEFAULTS:
        assert is_valid_type_code(code)


def test_reserved_type_segments_rejected():
    assert not is_valid_type_code("_meta")
    assert not is_valid_type_code("logs")
    assert not is_valid_type_code("BadCode")


def test_permission_prefixes_use_records_not_meetings():
    assert permission_prefix_for_type_code("meeting_history") == "records.meeting_history"
    assert permission_prefix_for_type_code("meeting_topic") == "records.meeting_topic"
    assert permission_prefix_for_type_code("incoming_document") == "records.incoming_documents"


def test_merge_type_ui_payload():
    merged = merge_type_ui_payload("document", {"icon": "custom"})
    assert merged["uiSurface"] == "document"
    assert merged["icon"] == "custom"


def test_record_constants_present():
    assert "status" in constants.QUERY_KEYS or hasattr(constants, "DOMAIN_STATUS") or hasattr(constants, "READ_ONLY")


def test_record_schemas_accept_extra():
    payload = RecordPayload(title="Hello", customField=1)
    assert payload.title == "Hello"
    reorder = MeetingReorder(orderedMeetingIds=["a", "b"])
    assert reorder.orderedMeetingIds == ["a", "b"]


def test_collection_parse_limit_shared():
    assert parse_limit("all") == 100
