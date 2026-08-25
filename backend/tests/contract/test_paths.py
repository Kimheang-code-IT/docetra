from app.core.datetime import extract_record_time, parse_instant
from app.core.permissions import TYPE_TO_PREFIX, catalog_rows, expand_permission_rows
from app.main import API_CONTENT_SECURITY_POLICY


def paths(app):
    return set(app.openapi()["paths"])


def test_frontend_collections_are_routed(app):
    required = {
        "/api/v2/auth/login", "/api/v2/auth/register", "/api/v2/auth/bootstrap",
        "/api/v2/auth/logout", "/api/v2/auth/me", "/api/v2/auth/refresh",
        "/api/v2/auth/forgot-password", "/api/v2/auth/forgot-password/verify",
        "/api/v2/auth/forgot-password/reset", "/api/v2/auth/change-password",
        "/api/v2/auth/profile/avatar",
        "/api/v2/dashboard/summary",
        "/api/v2/records/{type_code}",
        "/api/v2/records/_meta/surfaces",
        "/api/v2/records/logs",
        "/api/v2/records/{type_code}/reorder",
        "/api/v2/records/{type_code}/{entity_id}/assign-topic",
        "/api/v2/settings/app-config/email/test-connection",
        "/api/v2/settings/app-config/telegram/test-connection",
        "/api/v2/organizations/{org_type}",
        "/api/v2/organizations/_meta/types",
        "/api/v2/sector",
        "/api/v2/purpose",
        "/api/v2/officers",
        "/api/v2/users/roles", "/api/v2/users", "/api/v2/users/permission-catalog",
        "/api/v2/configuration/record-types", "/api/v2/configuration/record-attributes",
        "/api/v2/configuration/record-types/{entity_id}/permissions",
        "/api/v2/settings/app-info", "/api/v2/settings/app-config", "/api/v2/settings/storage",
        "/api/v2/portal/file-uploads", "/api/v2/portal/google-drive-sync", "/api/v2/portal/logs", "/api/v2/portal/drive-files",
        "/api/v2/system/logs", "/api/v2/exports", "/api/v2/search", "/api/v2/search/ask", "/api/v2/mentions",
    }
    openapi = paths(app)
    assert required <= openapi
    assert not any(p.startswith("/api/v2/meetings/") for p in openapi)
    assert {
        "/api/v2/records/incoming-documents",
        "/api/v2/records/outgoing-documents",
        "/api/v2/records/documents",
        "/api/v2/records/master-list-requests",
    }.isdisjoint(openapi)
    assert {
        "/api/v2/organizations/departments",
        "/api/v2/organizations/companies",
        "/api/v2/organizations/sectors",
        "/api/v2/organizations/purposes",
        "/api/v2/organizations/officers",
    }.isdisjoint(openapi)


def test_meeting_permission_prefixes_are_records_only():
    from app.modules.record.domain.map import permission_prefix_for_type_code

    assert permission_prefix_for_type_code("meeting_topic") == "records.meeting_topic"
    assert permission_prefix_for_type_code("meeting_history") == "records.meeting_history"
    catalog_rows()  # refresh tables
    assert TYPE_TO_PREFIX["meeting_topic"] == "records.meeting_topic"
    assert TYPE_TO_PREFIX["meeting_history"] == "records.meeting_history"


def test_health_is_public(app):
    assert "/health" in paths(app) and "/ready" in paths(app)
    assert "default-src 'none'" in API_CONTENT_SECURITY_POLICY
    assert "frame-ancestors 'none'" in API_CONTENT_SECURITY_POLICY


def test_permission_catalog_uses_frontend_document_types():
    types = {row["documentType"] for row in catalog_rows()}
    assert {"incoming_document", "meeting_topic", "department", "purpose", "sector", "user", "storage"} <= types


def test_expand_permission_rows():
    keys = expand_permission_rows([{"documentType": "incoming_document", "actions": ["view", "edit"]}])
    assert keys == ["records.incoming_documents.view", "records.incoming_documents.edit"]


def test_parse_date_only_bounds():
    start = parse_instant("2026-08-18")
    end = parse_instant("2026-08-18", end_of_day=True)
    assert start is not None and end is not None
    assert start < end


def test_extract_record_time_prefers_meeting_date():
    instant = extract_record_time({"meetingDate": "2026-08-18T08:30"})
    assert instant is not None
    assert instant.hour == 8
