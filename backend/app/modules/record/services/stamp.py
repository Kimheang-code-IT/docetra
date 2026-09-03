import uuid
from typing import Any

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.datetime import extract_record_time, iso_utc, utcnow
from app.core.frontend_contract import normalize_assignment_refs
from app.core.errors import DomainError
from app.modules.record.model import Activity
from app.platform.messaging.model import Outbox
from typing import Any as User
from app.platform.audit.model import AuditLog
from app.modules.people_access.service import identity_sync, strip_secrets
from app.modules.record.domain.constants import DOMAIN_STATUS, READ_ONLY
from app.modules.record.model import Entity
from app.modules.record.repository import RecordRepository
from app.modules.admin_config.service import runtime


def stamp(entity: Entity) -> dict[str, Any]:
    result = dict(entity.payload or {})
    result.update({
        "id": str(entity.id),
        "createdAt": iso_utc(entity.created_at),
        "updatedAt": iso_utc(entity.updated_at),
        "version": entity.version,
    })
    if entity.stage is not None:
        result["stage"] = entity.stage
    if entity.archived_at:
        result["archivedAt"] = iso_utc(entity.archived_at)
    if entity.deleted_at:
        result["deletedAt"] = iso_utc(entity.deleted_at)
    if entity.record_time:
        result.setdefault("recordTime", iso_utc(entity.record_time))
    if entity.status in {"archived", "deleted"} or entity.resource not in DOMAIN_STATUS:
        result["status"] = entity.status
    elif "status" not in result:
        result["status"] = entity.status
    return normalize_assignment_refs(strip_secrets(result))


async def entity_or_404(db: AsyncSession, resource: str, entity_id: str) -> Entity:
    try:
        uid = uuid.UUID(entity_id)
    except ValueError as exc:
        raise HTTPException(404, "Not found") from exc
    row = await RecordRepository(db).entity(resource, uid)
    if not row:
        raise HTTPException(404, "Not found")
    return row


async def entity_by_id(db: AsyncSession, entity_id: uuid.UUID) -> Entity | None:
    return await RecordRepository(db).entity_by_id(entity_id)


async def audit(db: AsyncSession, entity: Entity, user: User, action: str, summary: str) -> None:
    db.add(Activity(entity_id=entity.id, actor_id=user.id, action=action, summary=summary))
    db.add(Outbox(topic=f"entity.{action}", payload={"resource": entity.resource, "id": str(entity.id)}))
    if entity.resource not in READ_ONLY:
        title = (entity.payload or {}).get("title") or (entity.payload or {}).get("name") or str(entity.id)
        portal = entity.resource in {"file-uploads", "google-drive-sync", "drive-files", "export-jobs"}
        db.add(AuditLog(
            created_by=user.officer_id,
            action_code=action,
            table_name=entity.resource,
            row_id=entity.id,
            message=summary,
            detail_data={
                "entityTitle": title,
                "entityType": entity.resource,
                "occurredAt": iso_utc(utcnow()),
                "correlationId": str(entity.id),
            },
            source_log="portal" if portal else "record",
            status_code="success",
        ))


async def assert_writable(db: AsyncSession, resource: str) -> None:
    if resource in READ_ONLY:
        raise DomainError("READ_ONLY", "This resource is read-only", 405)
    config = await runtime.load_app_config(db)
    general = runtime.general_defaults(config)
    if general["maintenanceMode"]:
        raise DomainError("MAINTENANCE", "System is in maintenance mode", 503)
    if general["readOnlyMode"]:
        raise DomainError("READ_ONLY", "System is in read-only mode", 403)


async def apply_side_effects(db: AsyncSession, row: Entity, source_payload: dict | None = None) -> None:
    await identity_sync.sync_domain_row(db, row)
