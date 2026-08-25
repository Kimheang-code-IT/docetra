from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v2.deps import current_user, get_db
from app.core.authorization import RESOURCE_PREFIX, require_permission
from app.core.datetime import parse_instant
from app.core.http_schemas import DataEnvelope
from app.core.privileged import is_unrestricted
from app.core.security import now_iso
from app.db import Entity, Outbox, User
from app.modules.record.services.stamp import entity_or_404, stamp
from app.modules.reporting_support.domain.schemas import ExportCreateRequest
from app.modules.reporting_support.services.export import RESOURCE_MAP

router = APIRouter(prefix="/exports", tags=["exports"])

STATUS_CACHE_TTL_SECONDS = 60


def _status_cache_key(entity_id: str) -> str:
    return f"export-job:{entity_id}"


async def _validate_date_range(start_raw: str | None, end_raw: str | None) -> None:
    start = parse_instant(start_raw)
    end = parse_instant(end_raw, end_of_day=True)
    if start_raw and not start:
        raise HTTPException(422, "Invalid startDate; use YYYY-MM-DD or an ISO datetime")
    if end_raw and not end:
        raise HTTPException(422, "Invalid endDate; use YYYY-MM-DD or an ISO datetime")
    if start and end and start > end:
        raise HTTPException(422, "startDate must be on or before endDate")


async def _cache_status(entity_id: str, data: dict, owner_id) -> None:
    try:
        from app.core.cache import short_cache

        await short_cache.set(_status_cache_key(entity_id), {"ownerId": str(owner_id or ""), "data": data}, STATUS_CACHE_TTL_SECONDS)
    except Exception:
        pass


@router.post("", status_code=202, response_model=DataEnvelope)
async def create_export(body: ExportCreateRequest, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    from app.core.errors import DomainError
    import app.modules.admin_config.services.runtime as runtime

    general = runtime.general_defaults(await runtime.load_app_config(db))
    if not general["enableExport"]:
        raise DomainError("EXPORT_DISABLED", "Exports are disabled in application settings", 403)
    resource = RESOURCE_MAP.get(str(body.resource), str(body.resource or ""))
    prefix = RESOURCE_PREFIX.get(resource)
    if not prefix:
        raise HTTPException(422, "Unsupported export resource")
    require_permission(user, f"{prefix}.export")
    if body.format not in {None, "csv"}:
        raise HTTPException(422, "Only CSV export is supported")
    await _validate_date_range(body.startDate, body.endDate)
    payload = body.model_dump()
    row = Entity(
        resource="export-jobs",
        payload={**payload, "status": "queued", "resource": body.resource, "createdAt": now_iso()},
        status="active",
        created_by=user.id,
        updated_by=user.id,
    )
    db.add(row)
    await db.flush()
    # Transactional outbox: worker publishes this to RabbitMQ and runs the export.
    db.add(Outbox(topic="export.execute", payload={"jobId": str(row.id)}))
    await db.commit()
    await db.refresh(row)
    data = stamp(row)
    data["status"] = "queued"
    await _cache_status(str(row.id), data, row.created_by)
    return {"data": data}


@router.get("/{entity_id}", response_model=DataEnvelope)
async def export_status(entity_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    try:
        from app.core.cache import short_cache

        cached = await short_cache.get(_status_cache_key(entity_id))
    except Exception:
        cached = None
    if (
        cached
        and isinstance(cached, dict)
        and isinstance(cached.get("data"), dict)
        and (cached.get("ownerId") == str(user.id) or is_unrestricted(user))
    ):
        return {"data": cached["data"]}
    row = await entity_or_404(db, "export-jobs", entity_id)
    if row.created_by != user.id and not is_unrestricted(user):
        raise HTTPException(403, "Export access denied")
    data = stamp(row)
    data["status"] = (row.payload or {}).get("status") or "queued"
    await _cache_status(entity_id, data, row.created_by)
    return {"data": data}


@router.delete("/{entity_id}", response_model=DataEnvelope)
async def delete_export(entity_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    row = await entity_or_404(db, "export-jobs", entity_id)
    if row.created_by != user.id and not is_unrestricted(user):
        raise HTTPException(403, "Export access denied")
    object_key = (row.payload or {}).get("objectKey")
    payload = dict(row.payload or {})
    payload["status"] = "pending_purge"
    row.payload = payload
    await db.commit()
    if object_key:
        from app.modules.storage_integration.services.storage import delete_object

        await delete_object(object_key)
    try:
        from app.core.cache import short_cache

        await short_cache.delete(_status_cache_key(entity_id))
    except Exception:
        pass
    row = await entity_or_404(db, "export-jobs", entity_id)
    await db.delete(row)
    await db.commit()
    return {"data": {"id": entity_id, "deleted": True}}
