import uuid
from fastapi import APIRouter,Depends,HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.v2.entities import stamp
from app.core.config import settings
from app.core.security import current_user
from app.db import Entity,User,get_db
from app.modules.storage_integration.storage import client

router=APIRouter(prefix="/files",tags=["files"])
@router.get("/{file_id}")
async def download(file_id:str,db:AsyncSession=Depends(get_db),user:User=Depends(current_user)):
    try: uid=uuid.UUID(file_id)
    except ValueError: raise HTTPException(404,"File not found")
    row=await db.scalar(select(Entity).where(Entity.id==uid))
    if not row or not row.payload.get("objectKey"): raise HTTPException(404,"File not found")
    if row.created_by and row.created_by != user.id and user.role not in {"SuperAdmin","Admin"}:
        permission="portal.file_upload.view" if row.resource=="file-uploads" else None
        if not permission or permission not in (user.permissions or []): raise HTTPException(403,"File access denied")
    response=client.get_object(settings.s3_bucket,row.payload["objectKey"])
    def chunks():
        try:
            while data:=response.read(64*1024): yield data
        finally: response.close(); response.release_conn()
    return StreamingResponse(chunks(),media_type=row.payload.get("mimeType","application/octet-stream"),headers={"Content-Disposition":f'attachment; filename="{row.payload.get("fileName","download")}"'})
