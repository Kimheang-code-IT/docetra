from datetime import datetime, timezone
from uuid import UUID

from app.core.frontend_contract import (
    entity_url,
    normalize_assignment_refs,
    search_entity_type,
    view_permission,
)
from app.modules.reporting_support.services.search import build_search_hit


def test_search_entity_type_mapping():
    assert search_entity_type("incoming-documents") == "incomingDocument"
    assert search_entity_type("meeting-history") == "meeting"
    assert search_entity_type("officers") == "officer"


def test_entity_url_uses_frontend_routes():
    assert entity_url("incoming-documents", "abc") == "/records/incoming-documents/abc"
    assert entity_url("meeting-history", "abc") == "/meetings/history/abc"
    assert entity_url("officers", "abc") == "/officers/abc"
    assert entity_url("sectors", "abc") == "/sector/abc"
    assert entity_url("purposes", "abc") == "/purpose/abc"


def test_normalize_assignment_refs():
    payload = normalize_assignment_refs({
        "officeInCharge": ["dept-1"],
        "involvedOfficers": [{"id": "off-1", "label": "Officer One", "type": "officer"}],
    })
    assert payload["officeInCharge"] == [{"id": "dept-1", "label": "dept-1", "type": "department"}]
    assert payload["involvedOfficers"][0]["label"] == "Officer One"


def test_view_permission_prefix():
    assert view_permission("incoming-documents") == "records.incoming_documents.view"
    assert view_permission("file-uploads") == "portal.file_upload.view"


def test_build_search_hit_shape():
    updated = datetime(2026, 8, 18, 8, 30, tzinfo=timezone.utc)
    entity_id = str(UUID("11111111-1111-1111-1111-111111111111"))
    hit = build_search_hit(
        resource="incoming-documents",
        entity_id=entity_id,
        title="Letter 1",
        description="Important",
        updated_at=updated,
    )
    assert hit["entityType"] == "incomingDocument"
    assert hit["entityId"] == hit["id"] == entity_id
    assert hit["url"] == f"/records/incoming-documents/{entity_id}"
    assert hit["permission"] == "records.incoming_documents.view"
    assert hit["sourceLabel"] == "Incoming document"
