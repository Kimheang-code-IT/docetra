"""Record-owned creator-scope authorization helpers.

Creator scope comes from the canonical ``permission.scope`` column
('all' | 'creator', migration 0010). Roles marked ``onlyIfCreator`` grant
actions only on resources the current user created.
"""

from __future__ import annotations

import uuid

from fastapi import Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.authorization import RESOURCE_PREFIX, require_permission
from app.core.privileged import is_unrestricted
from app.core.security import current_user
from app.db.session import get_db
from app.modules.people_access.service import people
from app.modules.record.model import Entity, Record

RECORD_RESOURCES = frozenset(
    {
        "meeting-topics",
        "meeting-history",
        "incoming-documents",
        "outgoing-documents",
        "documents",
        "master-list-requests",
        "record-logs",
    }
)


async def _creator_scoped_actions(db: AsyncSession, user, resource: str) -> set[str]:
    """Enabled actions under this resource prefix that are creator-scoped."""
    if is_unrestricted(user):
        return set()
    role_id = getattr(user, "role_id", None)
    prefix = RESOURCE_PREFIX.get(resource)
    if not role_id or not prefix:
        return set()
    return await people.creator_scoped_actions_for_prefix(db, role_id, prefix)


async def creator_only(db: AsyncSession, user, resource: str) -> bool:
    """True when the user's `view` permission for this resource is creator-scoped,
    meaning list surfaces must show only resources they created."""
    prefix = RESOURCE_PREFIX.get(resource)
    if not prefix:
        return False
    return f"{prefix}.view" in await _creator_scoped_actions(db, user, resource)


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


def authorize_resource(resource: str, *, record_resources: frozenset[str] = frozenset()):
    async def dependency(request: Request, user=Depends(current_user), db: AsyncSession = Depends(get_db)):
        if is_unrestricted(user):
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
        if not entity_id:
            return
        creator_actions = await _creator_scoped_actions(db, user, resource)
        if f"{prefix}.{action}" not in creator_actions:
            return
        try:
            uid = uuid.UUID(str(entity_id))
        except ValueError:
            return
        if resource in record_resources:
            row = await db.get(Record, uid)
            if row and row.created_by and getattr(user, "officer_id", None) and row.created_by != user.officer_id:
                raise HTTPException(403, "This role is limited to records created by the current user")
        else:
            row = await db.get(Entity, uid)
            if row and row.created_by != user.id:
                raise HTTPException(403, "This role is limited to records created by the current user")

    return dependency
