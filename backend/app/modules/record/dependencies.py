"""Public FastAPI dependencies for Record."""

from fastapi import Depends, HTTPException, Request

from app.core.authorization import _action_from_request, require_permission
from app.core.privileged import is_unrestricted
from app.core.security import current_user
from typing import Any as User
from app.modules.record.domain.map import is_valid_type_code, permission_prefix_for_type_code


def authorize_type_code():
    async def dependency(request: Request, user: User = Depends(current_user)):
        type_code = str(request.path_params.get("type_code") or "")
        if not is_valid_type_code(type_code):
            raise HTTPException(404, "Record type not found")
        if is_unrestricted(user):
            return
        action = _action_from_request(request)
        route = request.scope.get("route")
        route_path = getattr(route, "path", "") if route else ""
        if request.method == "POST" and "{entity_id}" not in route_path:
            excluded = (
                "/archive",
                "/restore",
                "/bulk-delete",
                "/schema",
                "/reorder",
                "/assign-topic",
                "/attachments/link",
            )
            if not any(request.url.path.endswith(suffix) for suffix in excluded):
                action = "create"
        if request.url.path.endswith("/schema"):
            action = "view"
        require_permission(user, f"{permission_prefix_for_type_code(type_code)}.{action}")

    return dependency


__all__ = ["authorize_type_code"]
