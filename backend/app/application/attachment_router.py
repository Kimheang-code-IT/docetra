"""Attachment upload workflow — composes Storage Integration and Record.

Preferred attachment flow:

    Frontend (multipart)
    → Storage public service: validate policy, store object bytes, create File row
    → validate the public File result
    → Record public service: attach the returned file reference to the record

Record never imports Storage internals; Storage never imports Record beyond
its approved DAG edge.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any as User

from app.api.v2.deps import current_user, get_db
from app.core.authorization import require_permission
from app.core.http_schemas import DataEnvelope
from app.modules.record.service import CollectionService, permission_prefix_for_type_code
from app.modules.storage_integration.service import StorageFileCollectionService

router = APIRouter(tags=["record-attachments"])


@router.post("/records/{type_code}/{entity_id}/attachments/upload", status_code=201, response_model=DataEnvelope)
async def upload_record_attachment(
    type_code: str,
    entity_id: str,
    request: Request,
    file: Annotated[UploadFile, File(description="Binary file content; stored via the Storage Integration upload flow")],
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    require_permission(user, f"{permission_prefix_for_type_code(type_code)}.edit")

    # 1) Store the real bytes + File row through the Storage public service.
    file_payload = await StorageFileCollectionService().create_upload(db, user, request)
    if not file_payload.get("id") or not file_payload.get("objectKey"):
        raise HTTPException(502, "Uploaded file is not available in object storage")

    # 2) Attach the returned public file reference to the record.
    expected = request.query_params.get("version")
    result = await CollectionService(type_code=type_code).attach_file(
        db, user, entity_id, file_payload, expected,
    )

    file_id = str(file_payload["id"])
    entry = next(
        (item for item in (result.get("attachments") or []) if str(item.get("id") or "") == file_id),
        file_payload,
    )
    return {"data": entry, "meta": {"version": result.get("version")}}


@router.delete("/records/{type_code}/{entity_id}/attachments/{file_id}", response_model=DataEnvelope)
async def detach_record_attachment(
    type_code: str,
    entity_id: str,
    file_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    require_permission(user, f"{permission_prefix_for_type_code(type_code)}.edit")

    expected = request.query_params.get("version")
    result = await CollectionService(type_code=type_code).detach_file(
        db, user, entity_id, file_id, expected,
    )
    # The shared File is intentionally NOT deleted here: other records may
    # still reference it. Purging the object requires the explicit, authorized
    # storage purge flow.
    return {"data": {"id": file_id}, "meta": {"version": result.get("version"), "attachments": result.get("attachments")}}
