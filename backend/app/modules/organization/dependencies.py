"""Public FastAPI dependencies for Organization."""

from fastapi import Depends, HTTPException, Request

from app.core.authorization import _action_from_request, require_permission
from app.core.privileged import is_unrestricted
from app.core.security import current_user
from typing import Any as User
from app.modules.organization.domain.map import is_valid_org_type, permission_prefix_for_org_type


def authorize_org_type():
    async def dependency(request: Request, user: User = Depends(current_user)):
        org_type = str(request.path_params.get("org_type") or "")
        if not is_valid_org_type(org_type):
            raise HTTPException(404, "Organization type not found")
        if is_unrestricted(user):
            return
        action = _action_from_request(request)
        route = request.scope.get("route")
        route_path = getattr(route, "path", "") if route else ""
        if request.method == "POST" and "{entity_id}" not in route_path:
            if not any(request.url.path.endswith(suffix) for suffix in ("/archive", "/restore", "/bulk-delete")):
                action = "create"
        require_permission(user, f"{permission_prefix_for_org_type(org_type)}.{action}")

    return dependency


__all__ = ["authorize_org_type"]
