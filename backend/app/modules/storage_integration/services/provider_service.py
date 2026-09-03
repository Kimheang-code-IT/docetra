from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any as User

from app.core.secrets import mask_mapping, protect_mapping, reveal_mapping
from app.core.security import now_iso
from app.modules.admin_config.service import merge_setting
from app.modules.record.service import entity_bags


async def list_providers(db: AsyncSession) -> tuple[list[dict], int]:
    rows = await entity_bags.list_entities(db, "storage-providers")
    data = [{**row["public"], **mask_mapping(row["payload"])} for row in rows if row["status"] != "deleted"]
    total = len(data)
    return data, total


async def create_provider(db: AsyncSession, body: dict, user: User) -> dict:
    body = {**body, "connectionStatus": "not_tested", "isDefault": bool(body.get("isDefault")), "active": bool(body.get("active", True))}
    row = await entity_bags.create_entity(db, "storage-providers", protect_mapping(body), status="active", created_by=user.id, updated_by=user.id)
    from app.modules.storage_integration.services.storage import invalidate_storage_client

    await invalidate_storage_client()
    return {**row["public"], **mask_mapping(row["payload"])}


async def get_provider(db: AsyncSession, entity_id: str) -> dict:
    row = await entity_bags.get_entity(db, "storage-providers", entity_id)
    return {**row["public"], **mask_mapping(row["payload"])}


async def update_provider(db: AsyncSession, entity_id: str, body: dict) -> dict:
    current = await entity_bags.get_entity(db, "storage-providers", entity_id)
    row = await entity_bags.update_entity(db, "storage-providers", entity_id, payload=protect_mapping(merge_setting(reveal_mapping(current["payload"]), body)))
    from app.modules.storage_integration.services.storage import invalidate_storage_client

    await invalidate_storage_client()
    return {**row["public"], **mask_mapping(row["payload"])}


async def delete_provider(db: AsyncSession, entity_id: str) -> str:
    await entity_bags.delete_entity(db, "storage-providers", entity_id)
    return entity_id


async def test_provider_connection(db: AsyncSession, entity_id: str) -> dict:
    row = await entity_bags.get_entity(db, "storage-providers", entity_id)
    from app.modules.storage_integration.services.providers import test_provider

    result = await test_provider(reveal_mapping(row["payload"]))
    await entity_bags.update_entity(db, "storage-providers", entity_id, payload={**row["payload"], "connectionStatus": result["status"], "lastTestedAt": now_iso(), "lastTestMessage": result["message"]})
    return result


async def set_provider_active(db: AsyncSession, entity_id: str, active: bool) -> dict:
    current = await entity_bags.get_entity(db, "storage-providers", entity_id)
    row = await entity_bags.update_entity(db, "storage-providers", entity_id, payload={**current["payload"], "active": active})
    from app.modules.storage_integration.services.storage import invalidate_storage_client

    await invalidate_storage_client()
    return {**row["public"], **mask_mapping(row["payload"])}


async def set_provider_default(db: AsyncSession, entity_id: str) -> dict:
    rows = await entity_bags.list_entities(db, "storage-providers")
    for row in rows:
        await entity_bags.update_entity(db, "storage-providers", str(row["id"]), payload={**row["payload"], "isDefault": str(row["id"]) == entity_id})
    row = await entity_bags.get_entity(db, "storage-providers", entity_id)
    from app.modules.storage_integration.services.storage import invalidate_storage_client

    await invalidate_storage_client()
    return {**row["public"], **mask_mapping(row["payload"])}
