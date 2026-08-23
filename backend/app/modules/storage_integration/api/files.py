import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.privileged import is_unrestricted
from app.core.security import current_user
from app.db import Entity, User, get_db
from app.models.storage import File
from app.modules.storage_integration.services.storage import get_object_bytes

router = APIRouter(prefix="/files", tags=["files"])


@router.get("/{file_id}")
async def download(file_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    try:
        uid = uuid.UUID(file_id)
    except ValueError as exc:
        raise HTTPException(404, "File not found") from exc

    object_key = None
    mime_type = "application/octet-stream"
    file_name = "download"
    created_by = None
    resource = None

    file_row = await db.get(File, uid)
    if file_row and file_row.path:
        object_key = file_row.path
        mime_type = file_row.mime_type or mime_type
        file_name = file_row.nam or file_name
        created_by = file_row.created_by
        resource = "file-uploads"
    else:
        row = await db.scalar(select(Entity).where(Entity.id == uid))
        if not row or not (row.payload or {}).get("objectKey"):
            raise HTTPException(404, "File not found")
        object_key = row.payload["objectKey"]
        mime_type = row.payload.get("mimeType") or mime_type
        file_name = row.payload.get("fileName") or file_name
        created_by = row.created_by
        resource = row.resource

    if created_by and str(created_by) != str(user.id) and not is_unrestricted(user):
        permission = "portal.file_upload.view" if resource == "file-uploads" else None
        if not permission or permission not in (user.permissions or []):
            raise HTTPException(403, "File access denied")

    data = await get_object_bytes(object_key, db)
    return Response(
        content=data,
        media_type=mime_type,
        headers={"Content-Disposition": f'attachment; filename="{file_name}"'},
    )
