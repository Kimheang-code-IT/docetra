"""Maps backend resources to frontend adapter contracts (paths, search types, permissions)."""

from app.core.authorization import RESOURCE_PREFIX

RECORD_RESOURCES = (
    "incoming-documents",
    "outgoing-documents",
    "documents",
    "master-list-requests",
)

RESOURCE_URL_PREFIX: dict[str, str] = {
    "incoming-documents": "/records/incoming-documents",
    "outgoing-documents": "/records/outgoing-documents",
    "documents": "/records/documents",
    "master-list-requests": "/records/master-list-requests",
    "record-logs": "/records/logs",
    "meeting-history": "/meetings/history",
    "meeting-topics": "/meetings/topics",
    "departments": "/organizations/departments",
    "companies": "/organizations/companies",
    "purposes": "/purpose",
    "sectors": "/sector",
    "officers": "/officers",
    "roles": "/user-management/roles",
    "users": "/user-management/users",
    "record-types": "/configuration/record-types",
    "record-attributes": "/configuration/record-attributes",
    "file-uploads": "/portal/file-uploads",
    "google-drive-sync": "/portal/google-drive-sync",
    "portal-logs": "/portal/logs",
    "system-logs": "/system-monitor/system-logs",
}

RESOURCE_SEARCH_TYPE: dict[str, str] = {
    "incoming-documents": "incomingDocument",
    "outgoing-documents": "outgoingDocument",
    "documents": "document",
    "master-list-requests": "document",
    "record-logs": "document",
    "meeting-history": "meeting",
    "meeting-topics": "meetingTopic",
    "departments": "department",
    "companies": "company",
    "purposes": "company",
    "sectors": "company",
    "officers": "officer",
    "users": "user",
    "roles": "user",
    "record-types": "document",
    "record-attributes": "document",
    "file-uploads": "file",
    "google-drive-sync": "file",
    "portal-logs": "other",
    "system-logs": "other",
}

RESOURCE_SOURCE_LABEL: dict[str, str] = {
    "incoming-documents": "Incoming document",
    "outgoing-documents": "Outgoing document",
    "documents": "Document",
    "master-list-requests": "Master list request",
    "meeting-history": "Meeting",
    "meeting-topics": "Meeting topic",
    "departments": "Department",
    "companies": "Company",
    "officers": "Officer",
    "users": "User",
    "file-uploads": "File upload",
}

DASHBOARD_KPIS: tuple[tuple[str, str, str], ...] = (
    ("incoming-documents", "docetra.pages.incomingDocument", "/records/incoming-documents"),
    ("outgoing-documents", "docetra.pages.outgoingDocument", "/records/outgoing-documents"),
    ("documents", "docetra.pages.document", "/records/documents"),
    ("meeting-history", "docetra.pages.meetingHistory", "/meetings/history"),
    ("master-list-requests", "docetra.pages.masterListRequest", "/records/master-list-requests"),
)

ASSIGNMENT_FIELD_TYPES: dict[str, str] = {
    "officeInCharge": "department",
    "involvedOfficers": "officer",
    "externalUnits": "company",
    "internalUnits": "department",
    "participants": "officer",
}


def entity_url(resource: str, entity_id: str) -> str:
    prefix = RESOURCE_URL_PREFIX.get(resource)
    if prefix:
        return f"{prefix}/{entity_id}"
    return f"/{resource.replace('-', '/')}/{entity_id}"


def search_entity_type(resource: str) -> str:
    return RESOURCE_SEARCH_TYPE.get(resource, "other")


def view_permission(resource: str) -> str:
    prefix = RESOURCE_PREFIX.get(resource)
    return f"{prefix}.view" if prefix else ""


def user_can_view_resource(user, resource: str) -> bool:
    if user.role in {"SuperAdmin", "Admin"}:
        return True
    if "ALL_PAGES" in (user.permissions or []):
        return True
    permission = view_permission(resource)
    if not permission:
        return True
    return permission in (user.permissions or [])


def normalize_assignment_refs(payload: dict) -> dict:
    data = dict(payload)
    for key, ref_type in ASSIGNMENT_FIELD_TYPES.items():
        if key not in data:
            continue
        value = data[key]
        if not isinstance(value, list):
            continue
        normalized: list[dict] = []
        for item in value:
            if isinstance(item, dict):
                item_id = str(item.get("id") or item.get("value") or "")
                if not item_id:
                    continue
                normalized.append({
                    "id": item_id,
                    "label": str(item.get("label") or item.get("name") or item_id),
                    "type": str(item.get("type") or ref_type),
                })
            elif item not in {None, ""}:
                text = str(item)
                normalized.append({"id": text, "label": text, "type": ref_type})
        data[key] = normalized
    assignees = data.get("assignees")
    if isinstance(assignees, list):
        mixed: list[dict] = []
        for item in assignees:
            if isinstance(item, dict) and item.get("id"):
                mixed.append({
                    "id": str(item["id"]),
                    "label": str(item.get("label") or item.get("name") or item["id"]),
                    "type": str(item.get("type") or "officer"),
                })
            elif item not in {None, ""}:
                text = str(item)
                mixed.append({"id": text, "label": text, "type": "officer"})
        data["assignees"] = mixed
    assignee = data.get("assignee")
    if isinstance(assignee, dict) and assignee.get("id"):
        data["assignee"] = {
            "id": str(assignee["id"]),
            "name": str(assignee.get("name") or assignee.get("label") or assignee["id"]),
            "email": assignee.get("email"),
            "avatarUrl": assignee.get("avatarUrl") or assignee.get("avatar"),
        }
    return data
