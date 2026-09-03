import json
import uuid
from collections.abc import Iterable, Sequence
from datetime import datetime
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.datetime import extract_record_time, iso_utc, utcnow
from app.core.frontend_contract import normalize_assignment_refs
from app.modules.people_access.service import strip_secrets
from app.modules.record.domain.map import CORE_RECORD_KEYS, LIFECYCLE_TO_STATUS, STATUS_TO_LIFECYCLE
from app.modules.record.model import Record, RecordAttribute, RecordDetail, RecordTemplate, RecordType


def lifecycle_status(row: Record) -> str:
    return row.lifecycle or STATUS_TO_LIFECYCLE.get(row.status, "active")


def value_from_detail(row: RecordDetail) -> Any:
    if row.value_json is not None:
        return row.value_json
    if row.value_id is not None:
        return str(row.value_id)
    if row.value_boolean is not None:
        return row.value_boolean
    if row.value_time is not None:
        return iso_utc(row.value_time)
    if row.value_number is not None:
        return float(row.value_number)
    if row.value_string is not None:
        return row.value_string
    return None


def details_map(rows: Iterable[RecordDetail]) -> dict[uuid.UUID, dict[str, Any]]:
    grouped: dict[uuid.UUID, dict[str, Any]] = {}
    for row in rows:
        value = value_from_detail(row)
        if value is None:
            continue
        grouped.setdefault(row.record_id, {})[row.record_attribute_code] = value
    return grouped


def record_to_payload(row: Record, details: dict[str, Any] | None = None) -> dict[str, Any]:
    result = dict(details or {})
    result.update({
        "id": str(row.id),
        "title": row.title,
        "status": lifecycle_status(row),
        "version": row.version,
        "createdAt": iso_utc(row.created_at),
        "updatedAt": iso_utc(row.updated_at),
    })
    if row.stage is not None:
        result["stage"] = row.stage
    if row.record_time:
        result["recordTime"] = iso_utc(row.record_time)
    if row.record_type_id:
        result["recordTypeId"] = str(row.record_type_id)
    if row.record_type_code:
        result["recordTypeCode"] = row.record_type_code
        result.setdefault("recordType", row.record_type_code)
    if row.record_content:
        result["recordContent"] = row.record_content
        result.setdefault("description", row.record_content)
    if row.record_tag:
        result["recordTag"] = row.record_tag
        result["tags"] = [part.strip() for part in row.record_tag.split(",") if part.strip()]
    if row.parent_record:
        result["parentRecord"] = str(row.parent_record)
        result["parentId"] = str(row.parent_record)
    if row.archived_at:
        result["archivedAt"] = iso_utc(row.archived_at)
    if row.deleted_at:
        result["deletedAt"] = iso_utc(row.deleted_at)
    if row.record_metadata:
        try:
            meta = json.loads(row.record_metadata)
            if isinstance(meta, dict):
                result.setdefault("metadata", meta)
        except json.JSONDecodeError:
            result["recordMetadata"] = row.record_metadata
    return normalize_assignment_refs(strip_secrets(result))


async def details_as_dict(db: AsyncSession, record_id: uuid.UUID) -> dict[str, Any]:
    grouped = await details_by_record_ids(db, [record_id])
    return grouped.get(record_id, {})


async def details_by_record_ids(db: AsyncSession, record_ids: Sequence[uuid.UUID]) -> dict[uuid.UUID, dict[str, Any]]:
    if not record_ids:
        return {}
    rows = (await db.scalars(select(RecordDetail).where(RecordDetail.record_id.in_(list(record_ids))))).all()
    grouped = {record_id: {} for record_id in record_ids}
    grouped.update(details_map(rows))
    return grouped


async def serialize_records(db: AsyncSession, rows: Sequence[Record]) -> list[dict[str, Any]]:
    grouped = await details_by_record_ids(db, [row.id for row in rows])
    return [record_to_payload(row, grouped.get(row.id, {})) for row in rows]


async def serialize_record(db: AsyncSession, row: Record) -> dict[str, Any]:
    payloads = await serialize_records(db, [row])
    return payloads[0]


def _detail_values(code: str, value: Any) -> dict[str, Any]:
    cols: dict[str, Any] = {
        "value_string": None,
        "value_number": None,
        "value_time": None,
        "value_boolean": None,
        "value_json": None,
        "value_id": None,
    }
    if isinstance(value, bool):
        cols["value_boolean"] = value
    elif isinstance(value, (int, float)) and not isinstance(value, bool):
        cols["value_number"] = value
    elif isinstance(value, datetime):
        cols["value_time"] = value
    elif isinstance(value, uuid.UUID):
        cols["value_id"] = value
    elif isinstance(value, (dict, list)):
        cols["value_json"] = value
    elif value is None:
        pass
    else:
        text = str(value)
        try:
            cols["value_id"] = uuid.UUID(text)
        except ValueError:
            cols["value_string"] = text
    return cols


async def _resolve_attribute(
    db: AsyncSession,
    code: str,
    record_type_id: uuid.UUID | None,
) -> RecordAttribute | None:
    if record_type_id:
        assigned = await db.scalar(
            select(RecordAttribute)
            .join(RecordTemplate, RecordTemplate.record_attribute_id == RecordAttribute.id)
            .where(
                RecordTemplate.record_type_id == record_type_id,
                RecordAttribute.code == code,
            )
            .order_by(RecordTemplate.ordering)
        )
        if assigned:
            return assigned
    return await db.scalar(
        select(RecordAttribute).where(RecordAttribute.code == code).order_by(RecordAttribute.created_at)
    )


async def replace_details(
    db: AsyncSession,
    record_id: uuid.UUID,
    payload: dict,
    actor_officer_id: uuid.UUID | None,
    record_type_id: uuid.UUID | None = None,
) -> None:
    await db.execute(delete(RecordDetail).where(RecordDetail.record_id == record_id))
    for key, value in payload.items():
        if key in CORE_RECORD_KEYS or value is None:
            continue
        cols = _detail_values(key, value)
        attribute = await _resolve_attribute(db, key, record_type_id)
        db.add(RecordDetail(
            record_id=record_id,
            record_attribute_id=attribute.id if attribute else None,
            record_attribute_code=attribute.code if attribute else key,
            created_by=actor_officer_id,
            updated_by=actor_officer_id,
            **cols,
        ))


async def ensure_record_type(
    db: AsyncSession,
    code: str,
    actor_officer_id: uuid.UUID | None = None,
    organization_id: uuid.UUID | None = None,
    *,
    unrestricted: bool = False,
) -> RecordType:
    from app.modules.record.domain.map import merge_type_ui_payload
    import app.modules.record.services.type_access as type_access

    org_id = organization_id or await type_access.organization_id_for_officer(db, actor_officer_id)
    row = await type_access.resolve_type_by_code(
        db,
        code,
        organization_id=org_id,
        unrestricted=unrestricted or org_id is None,
    )
    if row:
        merged = merge_type_ui_payload(code, dict(row.payload or {}))
        if dict(row.payload or {}) != merged:
            row.payload = merged
            db.add(row)
        return row
    row = RecordType(
        code=code,
        nam=code.replace("_", " ").title(),
        is_active=1,
        payload=merge_type_ui_payload(code, {}),
        created_by=actor_officer_id,
        updated_by=actor_officer_id,
    )
    db.add(row)
    await db.flush()
    if org_id:
        await type_access.grant(
            db,
            row.id,
            org_id,
            permission_kind=type_access.OWNER,
            actor_officer_id=actor_officer_id,
        )
    else:
        await type_access.backfill_shared_grants_if_empty(db, row.id)
    return row


async def resolve_or_ensure_type(
    db: AsyncSession,
    code: str,
    actor_officer_id: uuid.UUID | None = None,
    organization_id: uuid.UUID | None = None,
    *,
    unrestricted: bool = False,
) -> RecordType:
    from fastapi import HTTPException
    from app.modules.record.domain.map import TYPE_UI_DEFAULTS
    import app.modules.record.services.type_access as type_access

    if code in TYPE_UI_DEFAULTS:
        return await ensure_record_type(
            db,
            code,
            actor_officer_id,
            organization_id,
            unrestricted=unrestricted,
        )
    org_id = organization_id or await type_access.organization_id_for_officer(db, actor_officer_id)
    row = await type_access.resolve_type_by_code(
        db,
        code,
        organization_id=org_id,
        unrestricted=unrestricted or org_id is None,
    )
    if not row:
        raise HTTPException(404, "Record type not found")
    return row


def apply_core_fields(row: Record, payload: dict, lifecycle: str | None = None) -> None:
    if "title" in payload or "name" in payload:
        row.title = str(payload.get("title") or payload.get("name") or row.title or "")
    if "stage" in payload:
        row.stage = payload.get("stage")
    if "recordContent" in payload or "description" in payload or "body" in payload:
        row.record_content = payload.get("recordContent") or payload.get("description") or payload.get("body")
    tags = payload.get("recordTag") or payload.get("tags")
    if isinstance(tags, list):
        row.record_tag = ",".join(str(t) for t in tags)
    elif isinstance(tags, str):
        row.record_tag = tags
    parent = payload.get("parentRecord") or payload.get("parentId")
    if parent:
        try:
            row.parent_record = uuid.UUID(str(parent))
        except ValueError:
            pass
    elif "parentId" in payload or "parentRecord" in payload:
        row.parent_record = None
    row.record_time = extract_record_time(payload) or row.record_time or utcnow()
    if lifecycle:
        row.lifecycle = lifecycle
        row.status = LIFECYCLE_TO_STATUS.get(lifecycle, 1)
        if lifecycle == "archived":
            row.archived_at = utcnow()
        elif lifecycle == "active":
            row.archived_at = None
            row.deleted_at = None
        elif lifecycle == "deleted":
            row.deleted_at = utcnow()
