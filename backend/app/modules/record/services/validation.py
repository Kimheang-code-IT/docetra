import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import DomainError
from app.db import Entity

RECORD_RESOURCES = {
    "incoming-documents",
    "outgoing-documents",
    "documents",
    "master-list-requests",
    "meeting-topics",
    "meeting-history",
}


async def validate_record_payload(db: AsyncSession, resource: str, payload: dict) -> None:
    if resource not in RECORD_RESOURCES:
        return
    type_code = payload.get("recordTypeCode") or payload.get("recordType")
    if not type_code:
        return
    row = await db.scalar(
        select(Entity).where(Entity.resource == "record-types", Entity.status == "active", Entity.payload["code"].as_string() == str(type_code))
    )
    if not row:
        return
    fields = (row.payload or {}).get("fields") or (row.payload or {}).get("attributes") or []
    missing = []
    for field in fields:
        if not isinstance(field, dict) or not field.get("required"):
            continue
        key = str(field.get("code") or field.get("key") or "")
        if key and payload.get(key) in {None, ""}:
            missing.append(key)
    if missing:
        raise DomainError("VALIDATION_ERROR", f"Missing required fields: {', '.join(missing)}", 422)


async def validate_department_parent(db: AsyncSession, resource: str, entity_id, payload: dict) -> None:
    if resource != "departments":
        return
    parent_id = payload.get("parentId")
    if not parent_id:
        return
    if str(parent_id) == str(entity_id):
        raise DomainError("VALIDATION_ERROR", "A department cannot be its own parent", 422)
    seen = {str(entity_id)}
    current = str(parent_id)
    for _ in range(50):
        if current in seen:
            raise DomainError("VALIDATION_ERROR", "Department hierarchy would create a cycle", 422)
        seen.add(current)
        try:
            row = await db.get(Entity, uuid.UUID(current))
        except ValueError as exc:
            raise DomainError("VALIDATION_ERROR", "Invalid parent department", 422) from exc
        if not row or row.resource != "departments":
            return
        current = str((row.payload or {}).get("parentId") or "")
        if not current:
            return
