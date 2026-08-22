from fastapi import Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import current_user
from app.db.session import get_db
from app.models.people import User
from app.models.record import Entity, Record
from app.modules.organization.domain.map import is_valid_org_type, permission_prefix_for_org_type
from app.modules.record.domain.map import RECORD_RESOURCES, permission_prefix_for_type_code

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


def require_permission(user: User, key: str) -> None:
    if user.role not in {"SuperAdmin", "Admin"} and key not in (user.permissions or []):
        raise HTTPException(403, f"Missing permission: {key}")


async def creator_only(db: AsyncSession, user: User, resource: str) -> bool:
    # Typed Role/Permission model does not yet store onlyIfCreator flags.
    # SuperAdmin/Admin already bypass; keep disabled for standard roles until menu metadata lands.
    return False


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


def authorize_resource(resource: str):
    async def dependency(request: Request, user: User = Depends(current_user), db: AsyncSession = Depends(get_db)):
        if user.role in {"SuperAdmin", "Admin"}:
            return
        prefix = RESOURCE_PREFIX.get(resource)
        if not prefix:
            return
        action = _action_from_request(request)
        route = request.scope.get("route")
        route_path = getattr(route, "path", "") if route else ""
        if request.method == "POST" and "{entity_id}" not in route_path:
            if not any(request.url.path.endswith(s) for s in ("/archive", "/restore", "/bulk-delete")):
                action = "create"
        require_permission(user, f"{prefix}.{action}")
        entity_id = request.path_params.get("entity_id")
        if entity_id and await creator_only(db, user, resource):
            import uuid

            try:
                uid = uuid.UUID(str(entity_id))
            except ValueError:
                return
            if resource in RECORD_RESOURCES:
                row = await db.get(Record, uid)
                if row and row.created_by and getattr(user, "officer_id", None) and row.created_by != user.officer_id:
                    raise HTTPException(403, "This role is limited to records created by the current user")
            else:
                row = await db.get(Entity, uid)
                if row and row.created_by != user.id:
                    raise HTTPException(403, "This role is limited to records created by the current user")

    return dependency


def authorize_type_code():
    """Authorize `/records/{type_code}/...` using legacy or generated permission prefixes."""
    from app.modules.record.domain.map import is_valid_type_code

    async def dependency(request: Request, user: User = Depends(current_user)):
        type_code = str(request.path_params.get("type_code") or "")
        if not is_valid_type_code(type_code):
            raise HTTPException(404, "Record type not found")
        if user.role in {"SuperAdmin", "Admin"}:
            return
        prefix = permission_prefix_for_type_code(type_code)
        action = _action_from_request(request)
        route = request.scope.get("route")
        route_path = getattr(route, "path", "") if route else ""
        if request.method == "POST" and "{entity_id}" not in route_path:
            if not any(
                request.url.path.endswith(s)
                for s in ("/archive", "/restore", "/bulk-delete", "/schema", "/reorder", "/assign-topic", "/attachments/link")
            ):
                action = "create"
        if request.url.path.endswith("/schema"):
            action = "view"
        require_permission(user, f"{prefix}.{action}")

    return dependency


def authorize_org_type():
    """Authorize `/organizations/{org_type}/...` using legacy department/company prefixes."""

    async def dependency(request: Request, user: User = Depends(current_user)):
        org_type = str(request.path_params.get("org_type") or "")
        if not is_valid_org_type(org_type):
            raise HTTPException(404, "Organization type not found")
        if user.role in {"SuperAdmin", "Admin"}:
            return
        prefix = permission_prefix_for_org_type(org_type)
        action = _action_from_request(request)
        route = request.scope.get("route")
        route_path = getattr(route, "path", "") if route else ""
        if request.method == "POST" and "{entity_id}" not in route_path:
            if not any(request.url.path.endswith(s) for s in ("/archive", "/restore", "/bulk-delete")):
                action = "create"
        require_permission(user, f"{prefix}.{action}")

    return dependency
