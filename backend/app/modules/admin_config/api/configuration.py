from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v2.deps import current_user, get_db
from app.api.v2.entities import router_for
from app.core.authorization import require_permission
from app.db import User
import app.modules.admin_config.services.configuration as record_schema

router = APIRouter(tags=["configuration"])
router.include_router(router_for("configuration/record-types", "record-types"))
router.include_router(router_for("configuration/record-attributes", "record-attributes"))


@router.get("/configuration/record-types/by-code/{code}/schema")
async def schema_by_code(code: str, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    require_permission(user, "configuration.record_types.view")
    return {"data": await record_schema.schema_by_code(db, code)}


@router.get("/configuration/record-types/{entity_id}/schema")
async def schema_by_id(entity_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    require_permission(user, "configuration.record_types.view")
    return {"data": await record_schema.schema_by_id(db, entity_id)}
