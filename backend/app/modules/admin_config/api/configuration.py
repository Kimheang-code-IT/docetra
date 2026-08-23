from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v2.deps import current_user, get_db
from app.api.v2.entities import router_for
from app.core.authorization import require_permission
from app.core.http_schemas import DataEnvelope
from app.core.privileged import is_unrestricted
from app.db import User
from app.modules.record.domain.map import permission_prefix_for_type_code, resolve_type_code
import app.modules.admin_config.services.configuration as record_schema

router = APIRouter(tags=["configuration"])
router.include_router(router_for("configuration/record-types", "record-types"))
router.include_router(router_for("configuration/record-attributes", "record-attributes"))


def _authorize_schema_read(user: User, type_code: str) -> None:
    if is_unrestricted(user):
        return
    perms = set(user.permissions or [])
    if "configuration.record_types.view" in perms:
        return
    prefix = permission_prefix_for_type_code(type_code)
    if f"{prefix}.view" in perms:
        return
    require_permission(user, "configuration.record_types.view")


@router.get("/configuration/record-types/by-code/{code}/schema", response_model=DataEnvelope)
async def schema_by_code(code: str, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    resolved = resolve_type_code(code)
    _authorize_schema_read(user, resolved)
    return {"data": await record_schema.schema_by_code(db, resolved)}


@router.get("/configuration/record-types/{entity_id}/schema", response_model=DataEnvelope)
async def schema_by_id(entity_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    data = await record_schema.schema_by_id(db, entity_id)
    _authorize_schema_read(user, data["recordType"]["code"])
    return {"data": data}
