"""Shared authorization vocabulary.

Only permission-key mapping and request-action derivation live here. Resource
authorization dependencies and creator-scope checks belong to the owning
business module (see ``app.modules.record.services.creator_scope``).
"""

from fastapi import HTTPException, Request

from app.core.privileged import is_unrestricted

RESOURCE_PREFIX = {
    "meeting-topics": "records.meeting_topic",
    "meeting-history": "records.meeting_history",
    "incoming-documents": "records.incoming_documents",
    "outgoing-documents": "records.outgoing_documents",
    "documents": "records.documents",
    "master-list-requests": "records.master_list_requests",
    "record-logs": "records.logs",
    "departments": "organizations.departments",
    "companies": "organizations.companies",
    "company-purposes": "organizations.purposes",
    "company-sectors": "organizations.sectors",
    "sectors": "organizations.sectors",
    "purposes": "organizations.purposes",
    "officers": "organizations.officers",
    "roles": "users.roles",
    "users": "users.users",
    "record-types": "configuration.record_types",
    "record-attributes": "configuration.record_attributes",
    "file-uploads": "portal.file_upload",
    "google-drive-sync": "portal.google_drive_sync",
    "portal-logs": "portal.logs",
    "system-logs": "system.logs",
}


def require_permission(user, key: str) -> None:
    if not is_unrestricted(user) and key not in (user.permissions or []):
        raise HTTPException(403, f"Missing permission: {key}")


def _action_from_request(request: Request) -> str:
    path = request.url.path
    method = request.method
    action = "view" if method == "GET" else "edit"
    if path.endswith("/archive"):
        action = "archive"
    elif path.endswith("/restore"):
        action = "restore"
    elif path.endswith("/purge"):
        action = "purge"
    elif path.endswith("/bulk-delete"):
        action = "delete"
    elif path.endswith("/assign-topic"):
        action = "assign"
    elif path.endswith("/reorder") or path.endswith("/attachments/link"):
        action = "edit"
    elif "/comments" in path:
        action = "comment"
    elif path.endswith("/stage"):
        action = "transition"
    elif method == "DELETE":
        action = "delete"
    return action
