from app.core.datetime import extract_record_time, parse_instant
from app.core.permissions import catalog_rows, expand_permission_rows
from app.main import app


def paths():
    return set(app.openapi()["paths"])


def test_frontend_collections_are_routed():
    required = {
        "/api/v2/auth/login", "/api/v2/auth/logout", "/api/v2/auth/me", "/api/v2/auth/refresh",
        "/api/v2/auth/forgot-password", "/api/v2/auth/forgot-password/verify",
        "/api/v2/auth/forgot-password/reset", "/api/v2/auth/change-password",
        "/api/v2/auth/profile/avatar",
        "/api/v2/dashboard/summary",
        "/api/v2/meetings/topics", "/api/v2/meetings/history", "/api/v2/meetings/reorder",
        "/api/v2/meetings/history/{meeting_id}/assign-topic",
        "/api/v2/settings/app-config/email/test-connection",
        "/api/v2/settings/app-config/telegram/test-connection",
        "/api/v2/records/incoming-documents", "/api/v2/records/outgoing-documents",
        "/api/v2/records/documents", "/api/v2/records/master-list-requests",
        "/api/v2/organizations/departments", "/api/v2/organizations/companies", "/api/v2/organizations/officers",
        "/api/v2/users/roles", "/api/v2/users", "/api/v2/users/permission-catalog",
        "/api/v2/configuration/record-types", "/api/v2/configuration/record-attributes",
        "/api/v2/settings/app-info", "/api/v2/settings/app-config", "/api/v2/settings/storage",
        "/api/v2/portal/file-uploads", "/api/v2/portal/google-drive-sync", "/api/v2/portal/logs", "/api/v2/portal/drive-files",
        "/api/v2/system/logs", "/api/v2/exports", "/api/v2/search", "/api/v2/search/ask", "/api/v2/mentions",
    }
    assert required <= paths()


def test_health_is_public():
    assert "/health" in paths() and "/ready" in paths()


def test_permission_catalog_uses_frontend_document_types():
    types = {row["documentType"] for row in catalog_rows()}
    assert {"incoming_document", "meeting_topic", "department", "user", "storage"} <= types


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
