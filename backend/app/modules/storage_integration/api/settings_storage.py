from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v2.deps import current_user, get_db
from app.core.authorization import require_permission
from app.core.http_schemas import DataEnvelope, StorageActiveBody
from typing import Any as User
import app.modules.storage_integration.services.provider_service as admin_storage
from app.modules.storage_integration.domain.schemas import StorageProviderPayload

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/storage", response_model=DataEnvelope)
async def storage_list(db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    require_permission(user, "settings.storage.view")
    data, total = await admin_storage.list_providers(db)
    return {"data": data, "meta": {"page": 1, "limit": total or 20, "total": total}}


@router.post("/storage", response_model=DataEnvelope)
async def storage_create(body: StorageProviderPayload, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    require_permission(user, "settings.storage.configure")
    return {"data": await admin_storage.create_provider(db, body.model_dump(exclude_unset=True), user)}


@router.get("/storage/{entity_id}", response_model=DataEnvelope)
async def storage_get(entity_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    require_permission(user, "settings.storage.view")
    return {"data": await admin_storage.get_provider(db, entity_id)}


@router.put("/storage/{entity_id}", response_model=DataEnvelope)
@router.patch("/storage/{entity_id}", response_model=DataEnvelope)
async def storage_update(entity_id: str, body: StorageProviderPayload, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    require_permission(user, "settings.storage.edit")
    return {"data": await admin_storage.update_provider(db, entity_id, body.model_dump(exclude_unset=True))}


@router.delete("/storage/{entity_id}", response_model=DataEnvelope)
async def storage_delete(entity_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    require_permission(user, "settings.storage.configure")
    return {"data": {"id": await admin_storage.delete_provider(db, entity_id)}}


@router.post("/storage/{entity_id}/test-connection", response_model=DataEnvelope)
async def storage_test(entity_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    require_permission(user, "settings.storage.configure")
    return {"data": await admin_storage.test_provider_connection(db, entity_id)}


@router.post("/storage/{entity_id}/set-active", response_model=DataEnvelope)
async def storage_active(entity_id: str, body: StorageActiveBody, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    require_permission(user, "settings.storage.configure")
    return {"data": await admin_storage.set_provider_active(db, entity_id, body.active)}


@router.post("/storage/{entity_id}/set-default", response_model=DataEnvelope)
async def storage_default(entity_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    require_permission(user, "settings.storage.configure")
    return {"data": await admin_storage.set_provider_default(db, entity_id)}
