from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v2.deps import current_user, get_db
from app.core.authorization import RESOURCE_PREFIX, require_permission
from app.core.security import now_iso
from app.db import Entity, User
from app.modules.record.services.stamp import entity_or_404, stamp
from app.modules.reporting_support.services.export import RESOURCE_MAP

router = APIRouter(prefix="/exports", tags=["exports"])


@router.post("", status_code=202)
async def create_export(body: dict, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    from app.core.errors import DomainError
    import app.modules.admin_config.services.runtime as runtime

    general = runtime.general_defaults(await runtime.load_app_config(db))
    if not general["enableExport"]:
        raise DomainError("EXPORT_DISABLED", "Exports are disabled in application settings", 403)
    resource = RESOURCE_MAP.get(str(body.get("resource")), str(body.get("resource") or ""))
    prefix = RESOURCE_PREFIX.get(resource)
    if not prefix:
        raise HTTPException(422, "Unsupported export resource")
    require_permission(user, f"{prefix}.export")
    if body.get("format") not in {None, "csv"}:
        raise HTTPException(422, "Only CSV export is supported")
    row = Entity(
        resource="export-jobs",
        payload={**body, "status": "queued", "resource": body.get("resource"), "createdAt": now_iso()},
        status="active",
        created_by=user.id,
        updated_by=user.id,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    data = stamp(row)
    data["status"] = "queued"
    return {"data": data}


@router.get("/{entity_id}")
async def export_status(entity_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    row = await entity_or_404(db, "export-jobs", entity_id)
    if row.created_by != user.id and user.role not in {"SuperAdmin", "Admin"}:
        raise HTTPException(403, "Export access denied")
    data = stamp(row)
    data["status"] = (row.payload or {}).get("status") or "queued"
    return {"data": data}


@router.delete("/{entity_id}")
async def delete_export(entity_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    row = await entity_or_404(db, "export-jobs", entity_id)
    if row.created_by != user.id and user.role not in {"SuperAdmin", "Admin"}:
        raise HTTPException(403, "Export access denied")
    object_key = (row.payload or {}).get("objectKey")
    if object_key:
        from app.modules.storage_integration.services.storage import delete_object

        await delete_object(object_key)
    await db.delete(row)
    await db.commit()
    return {"data": {"id": entity_id, "deleted": True}}
