"""Record-owned type schemas for document boards and dynamic forms.

Record types live on the relational `record_type` table. The frontend still
calls `/configuration/record-types/.../schema`, so this module serializes that
table into the RecordType / ResolvedRecordTypeSchema shape the UI expects.
"""

from __future__ import annotations

import uuid

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.datetime import iso_utc
from app.modules.record.model import RecordAttribute, RecordStageTemplate, RecordTemplate, RecordType
from app.modules.record.domain.map import (
    DEFAULT_RECORD_TYPE_FEATURES,
    TYPE_UI_DEFAULTS,
    default_numbering_for_type,
    merge_type_ui_payload,
    normalize_workflow_stages,
    resolve_type_code,
    sequential_transitions,
)
from app.modules.record.services.serializer import ensure_record_type


def _as_uuid(value) -> uuid.UUID | None:
    try:
        return uuid.UUID(str(value))
    except (ValueError, TypeError, AttributeError):
        return None


def _normalize_assigned(item: dict, order: int) -> dict:
    code = str(item.get("attributeCode") or item.get("code") or "")
    return {
        "attributeId": str(item.get("attributeId") or item.get("id") or code),
        "attributeCode": code,
        "attributeLabel": str(item.get("attributeLabel") or item.get("label") or item.get("name") or code),
        "dataType": item.get("dataType") or "short_text",
        "required": bool(item.get("required")),
        "readOnly": bool(item.get("readOnly")),
        "visible": item.get("visible", True) is not False,
        "searchable": bool(item.get("searchable", True)),
        "filterable": bool(item.get("filterable", False)),
        "showInList": bool(item.get("showInList", False)),
        "stageCode": item.get("stageCode"),
        "section": item.get("section"),
        "columnWidth": item.get("columnWidth"),
        "order": int(item["order"]) if item.get("order") is not None else order,
    }


def serialize_record_attribute(row: RecordAttribute) -> dict:
    payload = dict(row.payload or {})
    name = row.nam or payload.get("label") or payload.get("name") or row.code
    return {
        "id": str(row.id),
        "code": row.code,
        "label": payload.get("label") or name,
        "name": name,
        "description": payload.get("description"),
        "helpText": payload.get("helpText"),
        "dataType": row.data_type or payload.get("dataType") or "short_text",
        "placeholder": payload.get("placeholder"),
        "defaultValue": payload.get("defaultValue"),
        "required": bool(payload.get("required", False)),
        "unique": bool(payload.get("unique", False)),
        "readOnly": bool(payload.get("readOnly", False)),
        "searchable": bool(payload.get("searchable", True)),
        "filterable": bool(payload.get("filterable", False)),
        "sortable": bool(payload.get("sortable", False)),
        "showInList": bool(payload.get("showInList", False)),
        "validation": payload.get("validation"),
        "options": payload.get("options") or [],
        "visibility": payload.get("visibility"),
        "usedByCount": int(payload.get("usedByCount") or 0),
        "status": payload.get("status") or "active",
        "version": 1,
        "createdAt": iso_utc(row.created_at),
        "updatedAt": iso_utc(row.updated_at),
    }


def serialize_record_type(row: RecordType) -> dict:
    payload = merge_type_ui_payload(row.code, dict(row.payload or {}))
    stages = normalize_workflow_stages(payload.get("stages") or payload.get("workflowStages"))
    features = {**DEFAULT_RECORD_TYPE_FEATURES, **(payload.get("features") or {})}
    numbering = {**default_numbering_for_type(row.code), **(payload.get("numbering") or {})}
    assigned = [
        _normalize_assigned(item, index)
        for index, item in enumerate(payload.get("attributes") or [])
        if isinstance(item, dict)
    ]
    extras = {
        key: payload[key]
        for key in (
            "uiSurface",
            "slug",
            "menuOrder",
            "isCreatable",
            "supportsStages",
            "supportsTopicContainer",
            "tabs",
            "fields",
        )
        if key in payload
    }
    return {
        "id": str(row.id),
        "code": row.code,
        "name": row.nam or row.code.replace("_", " ").title(),
        "description": row.description,
        "status": "active" if row.is_active else "inactive",
        "icon": payload.get("icon"),
        "color": payload.get("color"),
        "features": features,
        "numbering": numbering,
        "attributes": assigned,
        "stages": stages,
        "transitions": payload.get("transitions") or sequential_transitions(stages),
        "attributeCount": len(assigned),
        "workflowEnabled": bool(features.get("enableWorkflow") and stages),
        "deletable": bool(getattr(row, "deletable", 1)),
        "createdAt": iso_utc(row.created_at),
        "updatedAt": iso_utc(row.updated_at),
        "version": 1,
        **extras,
    }


def build_resolved_schema(row: RecordType, *, assigned: list[dict] | None = None, catalog: list[dict] | None = None) -> dict:
    public = serialize_record_type(row)
    if assigned is not None:
        public["attributes"] = assigned
        public["attributeCount"] = len(assigned)
    fields = public.get("fields") or public["attributes"]
    return {
        "recordType": public,
        "attributes": catalog if catalog is not None else [],
        "tabs": public.get("tabs") or [],
        "fields": fields,
        "workflowStages": public["stages"],
        "version": public.get("updatedAt") or "1",
    }


def _stages_from_templates(templates: list[RecordStageTemplate]) -> list[dict]:
    stages = []
    for index, tmpl in enumerate(templates):
        code = f"stage_{tmpl.ordering if tmpl.ordering is not None else index + 1}"
        stages.append({
            "id": str(tmpl.id),
            "code": code,
            "name": tmpl.nam or code,
            "isInitial": index == 0,
            "isFinal": bool(tmpl.is_final),
            "order": tmpl.ordering if tmpl.ordering is not None else index + 1,
        })
    return normalize_workflow_stages(stages)


async def _persist_merged_payload(db: AsyncSession, row: RecordType) -> RecordType:
    merged = merge_type_ui_payload(row.code, dict(row.payload or {}))
    if dict(row.payload or {}) != merged:
        row.payload = merged
        db.add(row)
        await db.flush()
        await db.refresh(row)
    return row


async def _assigned_attributes(db: AsyncSession, row: RecordType) -> list[dict]:
    templates = (
        await db.scalars(
            select(RecordTemplate)
            .where(RecordTemplate.record_type_id == row.id)
            .order_by(RecordTemplate.ordering)
        )
    ).all()
    if not templates:
        payload = merge_type_ui_payload(row.code, dict(row.payload or {}))
        return [
            _normalize_assigned(item, index)
            for index, item in enumerate(payload.get("attributes") or [])
            if isinstance(item, dict)
        ]

    attr_ids = [tmpl.record_attribute_id for tmpl in templates]
    attrs = {
        attr.id: attr
        for attr in (await db.scalars(select(RecordAttribute).where(RecordAttribute.id.in_(attr_ids)))).all()
    }
    assigned = []
    for index, tmpl in enumerate(templates):
        attr = attrs.get(tmpl.record_attribute_id)
        assigned.append({
            "attributeId": str(tmpl.record_attribute_id),
            "attributeCode": attr.code if attr else str(tmpl.record_attribute_id),
            "attributeLabel": (attr.nam or attr.code) if attr else "",
            "dataType": (attr.data_type if attr else None) or "short_text",
            "required": bool(tmpl.is_require),
            "readOnly": False,
            "visible": True,
            "searchable": True,
            "filterable": False,
            "showInList": False,
            "order": tmpl.ordering if tmpl.ordering is not None else index,
        })
    return assigned


async def _catalog_for_assigned(db: AsyncSession, assigned: list[dict]) -> list[dict]:
    ids = []
    codes = []
    for item in assigned:
        uid = _as_uuid(item.get("attributeId"))
        if uid:
            ids.append(uid)
        code = str(item.get("attributeCode") or "").strip()
        if code:
            codes.append(code)

    rows: list[RecordAttribute] = []
    if ids:
        rows.extend((await db.scalars(select(RecordAttribute).where(RecordAttribute.id.in_(ids)))).all())
    if codes:
        rows.extend((await db.scalars(select(RecordAttribute).where(RecordAttribute.code.in_(codes)))).all())

    seen: set[uuid.UUID] = set()
    catalog = []
    for row in rows:
        if row.id in seen:
            continue
        seen.add(row.id)
        catalog.append(serialize_record_attribute(row))

    known_ids = {item["id"] for item in catalog}
    known_codes = {item["code"] for item in catalog}
    for item in assigned:
        if item["attributeId"] in known_ids or item["attributeCode"] in known_codes:
            continue
        catalog.append({
            "id": item["attributeId"],
            "code": item["attributeCode"],
            "label": item["attributeLabel"],
            "name": item["attributeLabel"],
            "dataType": item.get("dataType") or "short_text",
            "required": bool(item.get("required")),
            "unique": False,
            "readOnly": bool(item.get("readOnly")),
            "searchable": bool(item.get("searchable", True)),
            "filterable": bool(item.get("filterable", False)),
            "sortable": False,
            "showInList": bool(item.get("showInList", False)),
            "options": [],
            "usedByCount": 0,
            "status": "active",
            "version": 1,
        })
    return catalog


async def resolved_schema(db: AsyncSession, row: RecordType) -> dict:
    import app.modules.record.services.type_access as type_access

    public = serialize_record_type(row)
    access = await type_access.permission_payload(db, [row.id])
    public.update(access.get(row.id, {}))
    if not public["stages"]:
        templates = (
            await db.scalars(
                select(RecordStageTemplate)
                .where(RecordStageTemplate.record_type_id == row.id)
                .order_by(RecordStageTemplate.ordering)
            )
        ).all()
        tmpl_stages = _stages_from_templates(list(templates))
        if tmpl_stages:
            public["stages"] = tmpl_stages
            public["transitions"] = sequential_transitions(tmpl_stages)
            public["features"] = {**public["features"], "enableWorkflow": True}
            public["workflowEnabled"] = True

    assigned = await _assigned_attributes(db, row)
    catalog = await _catalog_for_assigned(db, assigned)
    public["attributes"] = assigned
    public["attributeCount"] = len(assigned)
    return {
        "recordType": public,
        "attributes": catalog,
        "tabs": public.get("tabs") or [],
        "fields": public.get("fields") or assigned,
        "workflowStages": public["stages"],
        "version": public.get("updatedAt") or "1",
    }


async def schema_by_code(db: AsyncSession, code: str, user=None) -> dict:
    import app.modules.record.services.type_access as type_access
    from app.core.privileged import is_unrestricted

    resolved = resolve_type_code(code)
    if not resolved:
        raise HTTPException(404, "Record type not found")
    org_id = await type_access.actor_organization_id(db, user) if user else None
    unrestricted = user is None or is_unrestricted(user)
    if resolved in TYPE_UI_DEFAULTS:
        row = await ensure_record_type(
            db,
            resolved,
            organization_id=org_id,
            unrestricted=unrestricted,
        )
        await db.flush()
        await db.refresh(row)
    else:
        row = await type_access.resolve_type_by_code(
            db,
            resolved,
            organization_id=org_id,
            unrestricted=unrestricted,
        )
        if not row:
            raise HTTPException(404, "Record type not found")
        row = await _persist_merged_payload(db, row)
    await type_access.require_type_access(db, row, user)
    return await resolved_schema(db, row)


async def schema_by_id(db: AsyncSession, entity_id: str, user=None) -> dict:
    import app.modules.record.services.type_access as type_access

    uid = _as_uuid(entity_id)
    if not uid:
        raise HTTPException(404, "Record type not found")
    row = await db.get(RecordType, uid)
    if not row:
        raise HTTPException(404, "Record type not found")
    await type_access.require_type_access(db, row, user)
    row = await _persist_merged_payload(db, row)
    return await resolved_schema(db, row)
