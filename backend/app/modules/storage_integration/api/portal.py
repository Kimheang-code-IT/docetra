from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v2.deps import current_user, get_db
from app.api.v2.entities import router_for
from app.core.authorization import require_permission
from app.db import User
import app.modules.storage_integration.services.drive_sync as drive_sync

router = APIRouter(tags=["portal"])
router.include_router(router_for("portal/file-uploads", "file-uploads"))
router.include_router(router_for("portal/google-drive-sync", "google-drive-sync"))
router.include_router(router_for("portal/logs", "portal-logs"))


@router.get("/portal/drive-files")
async def drive_files(request: Request, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    require_permission(user, "portal.google_drive_sync.view")
    limit = min(200, int(request.query_params.get("limit", 50)))
    data, total = await drive_sync.list_drive_files(db, limit)
    return {"data": data, "meta": {"page": 1, "limit": 50, "total": total}}


@router.post("/portal/google-drive-sync/sources", status_code=201)
async def create_drive_source(body: dict, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    require_permission(user, "portal.google_drive_sync.edit")
    return {"data": await drive_sync.create_drive_source(db, body, user)}


@router.post("/portal/google-drive-sync/sources/{source_id}/sync", status_code=202)
async def start_drive_sync(source_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    require_permission(user, "portal.google_drive_sync.edit")
    return {"data": await drive_sync.start_drive_sync(db, source_id, user)}


@router.get("/portal/google-drive-sync/jobs/{job_id}")
async def drive_sync_status(job_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    require_permission(user, "portal.google_drive_sync.view")
    return {"data": await drive_sync.drive_sync_status(db, job_id)}
