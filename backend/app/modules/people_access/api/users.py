from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v2.deps import current_user, get_db
from app.api.v2.entities import router_for
from app.core.authorization import require_permission
from app.db import User
from app.modules.people_access.services.permission_catalog import permission_catalog

router = APIRouter(tags=["users"])


@router.get("/users/permission-catalog")
async def permission_catalog_route(user: User = Depends(current_user)):
    # Must be registered before router_for("users") so {entity_id} does not capture this path.
    require_permission(user, "users.roles.view")
    return {"data": permission_catalog()}


router.include_router(router_for("users/roles", "roles"))
router.include_router(router_for("users", "users"))
