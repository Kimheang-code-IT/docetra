from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.secrets import mask_mapping, protect_mapping, reveal_mapping
from app.core.security import now_iso
from app.db import Entity, User
from app.modules.admin_config.services.settings import merge_setting
from app.modules.record.services.stamp import entity_or_404, stamp


async def list_providers(db: AsyncSession) -> tuple[list[dict], int]:
    rows = (await db.scalars(select(Entity).where(Entity.resource == "storage-providers", Entity.status != "deleted"))).all()
    data = [{**stamp(row), **mask_mapping(row.payload or {})} for row in rows]
    total = len(data)
    return data, total


async def create_provider(db: AsyncSession, body: dict, user: User) -> dict:
    body = {**body, "connectionStatus": "not_tested", "isDefault": bool(body.get("isDefault")), "active": bool(body.get("active", True))}
    row = Entity(resource="storage-providers", payload=protect_mapping(body), status="active", created_by=user.id, updated_by=user.id)
    db.add(row)
    await db.commit()
    await db.refresh(row)
    from app.modules.storage_integration.services.storage import invalidate_storage_client

    await invalidate_storage_client()
    return {**stamp(row), **mask_mapping(row.payload or {})}


async def get_provider(db: AsyncSession, entity_id: str) -> dict:
    row = await entity_or_404(db, "storage-providers", entity_id)
    return {**stamp(row), **mask_mapping(row.payload or {})}


async def update_provider(db: AsyncSession, entity_id: str, body: dict) -> dict:
    row = await entity_or_404(db, "storage-providers", entity_id)
    current = reveal_mapping(row.payload or {})
    row.payload = protect_mapping(merge_setting(current, body))
    await db.commit()
    await db.refresh(row)
    from app.modules.storage_integration.services.storage import invalidate_storage_client

    await invalidate_storage_client()
    return {**stamp(row), **mask_mapping(row.payload or {})}


async def delete_provider(db: AsyncSession, entity_id: str) -> str:
    row = await entity_or_404(db, "storage-providers", entity_id)
    await db.delete(row)
    await db.commit()
    return entity_id


async def test_provider_connection(db: AsyncSession, entity_id: str) -> dict:
    row = await entity_or_404(db, "storage-providers", entity_id)
    from app.modules.storage_integration.services.providers import test_provider

    result = await test_provider(reveal_mapping(row.payload or {}))
    row.payload = {**(row.payload or {}), "connectionStatus": result["status"], "lastTestedAt": now_iso(), "lastTestMessage": result["message"]}
    await db.commit()
    return result


async def set_provider_active(db: AsyncSession, entity_id: str, active: bool) -> dict:
    row = await entity_or_404(db, "storage-providers", entity_id)
    row.payload = {**(row.payload or {}), "active": active}
    await db.commit()
    await db.refresh(row)
    from app.modules.storage_integration.services.storage import invalidate_storage_client

    await invalidate_storage_client()
    return {**stamp(row), **mask_mapping(row.payload or {})}


async def set_provider_default(db: AsyncSession, entity_id: str) -> dict:
    rows = (await db.scalars(select(Entity).where(Entity.resource == "storage-providers"))).all()
    for row in rows:
        row.payload = {**(row.payload or {}), "isDefault": str(row.id) == entity_id}
    await db.commit()
    row = await entity_or_404(db, "storage-providers", entity_id)
    from app.modules.storage_integration.services.storage import invalidate_storage_client

    await invalidate_storage_client()
    return {**stamp(row), **mask_mapping(row.payload or {})}
