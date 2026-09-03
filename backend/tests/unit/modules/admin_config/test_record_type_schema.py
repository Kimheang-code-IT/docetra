"""Record-type schema serialization for document boards and forms."""

from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

from app.modules.record.services.configuration import build_resolved_schema, serialize_record_type
from app.modules.record.domain.map import merge_type_ui_payload


def _type_row(code="master_list_request", payload=None, **extra):
    now = datetime(2026, 8, 23, 5, 30, tzinfo=timezone.utc)
    return SimpleNamespace(
        id=uuid4(),
        code=code,
        nam=code.replace("_", " ").title(),
        description=None,
        is_active=1,
        deletable=1,
        payload=payload or {},
        created_at=now,
        updated_at=now,
        **extra,
    )


def test_serialize_built_in_document_type_has_workflow_stages():
    public = serialize_record_type(_type_row())
    assert public["features"]["enableWorkflow"] is True
    assert public["workflowEnabled"] is True
    assert [stage["code"] for stage in public["stages"]][0] == "created"
    assert public["stages"][-1]["code"] == "finished_final"
    assert public["stages"][-1]["isFinal"] is True
    assert public["numbering"]["prefix"] == "MLR"


def test_serialize_meeting_type_uses_meeting_stages():
    public = serialize_record_type(_type_row("meeting_topic"))
    assert [stage["code"] for stage in public["stages"]] == ["intake", "review", "approval", "completed"]


def test_resolved_schema_matches_frontend_contract():
    row = _type_row("incoming_document")
    schema = build_resolved_schema(row)
    assert set(schema) >= {"recordType", "attributes", "tabs", "fields", "workflowStages", "version"}
    assert schema["recordType"]["code"] == "incoming_document"
    assert schema["workflowStages"] == schema["recordType"]["stages"]
    assert schema["recordType"]["features"]["enableWorkflow"] is True


def test_disabled_workflow_does_not_inject_stages():
    public = serialize_record_type(_type_row("document", payload={
        "features": {"enableWorkflow": False},
        "stages": [],
        "supportsStages": True,
    }))
    merged = merge_type_ui_payload("document", {"features": {"enableWorkflow": False}, "stages": []})
    assert merged["features"]["enableWorkflow"] is False
    assert merged["stages"] == []
    assert public["features"]["enableWorkflow"] is False
    assert public["stages"] == []
