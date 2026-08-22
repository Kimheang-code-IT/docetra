import re
from pathlib import Path

STATIC_FRONTEND_PATHS = {
    "/api/v2/auth/login",
    "/api/v2/auth/logout",
    "/api/v2/auth/me",
    "/api/v2/auth/refresh",
    "/api/v2/auth/forgot-password",
    "/api/v2/auth/forgot-password/verify",
    "/api/v2/auth/forgot-password/resend",
    "/api/v2/auth/forgot-password/reset",
    "/api/v2/auth/change-password",
    "/api/v2/auth/profile/avatar",
    "/api/v2/dashboard/summary",
    "/api/v2/records/meeting_topic",
    "/api/v2/records/meeting_history",
    "/api/v2/records/meeting_history/reorder",
    "/api/v2/records/incoming_document",
    "/api/v2/records/outgoing_document",
    "/api/v2/records/document",
    "/api/v2/records/master_list_request",
    "/api/v2/records/logs",
    "/api/v2/records/_meta/surfaces",
    "/api/v2/organizations/department",
    "/api/v2/organizations/company",
    "/api/v2/organizations/_meta/types",
    "/api/v2/sector",
    "/api/v2/purpose",
    "/api/v2/officers",
    "/api/v2/users/roles",
    "/api/v2/users",
    "/api/v2/users/permission-catalog",
    "/api/v2/configuration/record-types",
    "/api/v2/configuration/record-attributes",
    "/api/v2/settings/app-info",
    "/api/v2/settings/app-info/reset",
    "/api/v2/settings/app-config",
    "/api/v2/settings/app-config/email/test-connection",
    "/api/v2/settings/app-config/email/send-test",
    "/api/v2/settings/app-config/telegram/test-connection",
    "/api/v2/settings/app-config/telegram/send-test",
    "/api/v2/settings/storage",
    "/api/v2/portal/file-uploads",
    "/api/v2/portal/google-drive-sync",
    "/api/v2/portal/logs",
    "/api/v2/portal/drive-files",
    "/api/v2/system/logs",
    "/api/v2/exports",
    "/api/v2/search",
    "/api/v2/search/ask",
    "/api/v2/mentions",
}

# Concrete type-code paths are covered by the dynamic OpenAPI param route.
DYNAMIC_RECORD_OPENAPI = "/api/v2/records/{type_code}"
DYNAMIC_ORG_OPENAPI = "/api/v2/organizations/{org_type}"

PARAMETRIZED_PATTERNS = [
    (r"MEETINGS_REORDER", "/api/v2/records/{type_code}/reorder"),
    (r"MEETING_ASSIGN_TOPIC", "/api/v2/records/{type_code}/{entity_id}/assign-topic"),
    (r"MEETING_ATTACHMENTS_LINK", "/api/v2/records/{type_code}/{entity_id}/attachments/link"),
    (r"MEETING_ATTACHMENTS\b", "/api/v2/records/{type_code}/{entity_id}/attachments"),
    (r"STORAGE_PROVIDER_TEST", "/api/v2/settings/storage/{entity_id}/test-connection"),
    (r"STORAGE_PROVIDER_SET_DEFAULT", "/api/v2/settings/storage/{entity_id}/set-default"),
    (r"STORAGE_PROVIDER_SET_ACTIVE", "/api/v2/settings/storage/{entity_id}/set-active"),
    (r"STORAGE_PROVIDER\b", "/api/v2/settings/storage/{entity_id}"),
    (r"RECORD_COMMENTS", "/api/v2/records/{type_code}/{entity_id}/comments"),
    (r"RECORD_ACTIVITY", "/api/v2/records/{type_code}/{entity_id}/activity"),
    (r"RECORD_ATTACHMENTS", "/api/v2/records/{type_code}/{entity_id}/attachments"),
    (r"FILES\b", "/api/v2/files/{file_id}"),
]

# Paths that exist only as FE literals pointing at dynamic routes — satisfied by OpenAPI param.
TYPE_CODE_LITERALS = {
    "/api/v2/records/meeting_topic",
    "/api/v2/records/meeting_history",
    "/api/v2/records/meeting_history/reorder",
    "/api/v2/records/incoming_document",
    "/api/v2/records/outgoing_document",
    "/api/v2/records/document",
    "/api/v2/records/master_list_request",
}

ORG_TYPE_LITERALS = {
    "/api/v2/organizations/department",
    "/api/v2/organizations/company",
}


def _paths_from_api_endpoints() -> set[str]:
    repo_root = Path(__file__).resolve().parents[3]
    source = (repo_root / "frontend" / "app" / "utils" / "constants" / "api-endpoints.ts").read_text(encoding="utf-8")
    return set(re.findall(r"'(/api/v2[^']*)'", source))


def _expected_openapi_paths(source: str) -> set[str]:
    paths = set(STATIC_FRONTEND_PATHS)
    for key, openapi_path in PARAMETRIZED_PATTERNS:
        if re.search(rf"\b{key}\b", source):
            paths.add(openapi_path)
    return paths


def test_openapi_includes_frontend_api_endpoints(app):
    repo_root = Path(__file__).resolve().parents[3]
    source = (repo_root / "frontend" / "app" / "utils" / "constants" / "api-endpoints.ts").read_text(encoding="utf-8")
    openapi_paths = set(app.openapi()["paths"])
    expected = _expected_openapi_paths(source)
    missing = set()
    for path in expected:
        if path in openapi_paths:
            continue
        if path in TYPE_CODE_LITERALS and DYNAMIC_RECORD_OPENAPI in openapi_paths:
            continue
        if path in ORG_TYPE_LITERALS and DYNAMIC_ORG_OPENAPI in openapi_paths:
            continue
        if path.endswith("/comments") or path.endswith("/activity") or path.endswith("/attachments"):
            if DYNAMIC_RECORD_OPENAPI + "/{entity_id}/comments" in openapi_paths or any(
                p.startswith("/api/v2/records/{type_code}/{entity_id}") for p in openapi_paths
            ):
                continue
        missing.add(path)
    assert not missing, f"OpenAPI missing frontend paths: {sorted(missing)}"
    assert DYNAMIC_RECORD_OPENAPI in openapi_paths
    assert DYNAMIC_ORG_OPENAPI in openapi_paths


def test_api_endpoints_ts_contains_static_paths():
    frontend_paths = _paths_from_api_endpoints()
    missing = STATIC_FRONTEND_PATHS - frontend_paths - TYPE_CODE_LITERALS - ORG_TYPE_LITERALS
    missing_literals = (TYPE_CODE_LITERALS | ORG_TYPE_LITERALS) - frontend_paths
    assert not missing_literals, f"api-endpoints.ts missing type-code/org paths: {sorted(missing_literals)}"
    assert not missing, f"api-endpoints.ts missing static paths: {sorted(missing)}"
