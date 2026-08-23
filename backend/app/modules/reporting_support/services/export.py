import csv
import json
import uuid
from datetime import datetime, timedelta, timezone
from io import StringIO

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import Entity
from app.models.access import Role
from app.models.audit import AuditLog
from app.models.organization import Organization, OrganizationPurpose, OrganizationSector
from app.models.people import Officer, User
from app.models.record import Record, RecordAttribute, RecordType
from app.models.storage import File
import app.modules.organization.services.service as org_service
import app.modules.people_access.services.people as people
from app.modules.organization.domain.map import ORG_RESOURCES
from app.modules.record.domain.map import RECORD_RESOURCES
import app.modules.record.services.serializer as record_ser
from app.modules.storage_integration.services.storage import put_bytes

RESOURCE_MAP = {
    "meetingTopics": "meeting-topics",
    "meetingHistory": "meeting-history",
    "incomingDocuments": "incoming-documents",
    "outgoingDocuments": "outgoing-documents",
    "documents": "documents",
    "masterListRequests": "master-list-requests",
    "recordLogs": "record-logs",
    "departments": "departments",
    "companies": "companies",
    "purposes": "purposes",
    "sectors": "sectors",
    "officers": "officers",
    "roles": "roles",
    "users": "users",
    "recordTypes": "record-types",
    "recordAttributes": "record-attributes",
    "fileUploads": "file-uploads",
    "googleDriveSync": "google-drive-sync",
    "portalLogs": "portal-logs",
    "systemLogs": "system-logs",
}


def _cell(value):
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, default=str)
    return str(value)


def _parse_ids(selected: list) -> list[uuid.UUID]:
    ids: list[uuid.UUID] = []
    for raw in selected[:5000]:
        try:
            ids.append(uuid.UUID(str(raw)))
        except ValueError:
            pass
    return ids


async def _rows_for_resource(db: AsyncSession, resource: str, payload: dict) -> list[dict]:
    selected = payload.get("selectedIds") or []
    scope_selected = payload.get("scope") == "selected"
    ids = _parse_ids(selected) if scope_selected else []

    if resource in RECORD_RESOURCES:
        type_code = RECORD_RESOURCES[resource]
        stmt = select(Record).where(Record.record_type_code == type_code, Record.lifecycle != "deleted")
        if scope_selected:
            stmt = stmt.where(Record.id.in_(ids or [uuid.uuid4()]))
        rows = (await db.scalars(stmt.order_by(Record.updated_at.desc()).limit(10000))).all()
        return await record_ser.serialize_records(db, rows)

    if resource in ORG_RESOURCES:
        org_type = ORG_RESOURCES[resource]
        stmt = select(Organization).where(Organization.organization_type == org_type, Organization.is_active != 0)
        if scope_selected:
            stmt = stmt.where(Organization.id.in_(ids or [uuid.uuid4()]))
        rows = (await db.scalars(stmt.order_by(Organization.updated_at.desc()).limit(10000))).all()
        return [org_service.org_to_payload(row) for row in rows]

    if resource == "sectors":
        stmt = select(OrganizationSector).where(OrganizationSector.is_active != 0)
        if scope_selected:
            stmt = stmt.where(OrganizationSector.id.in_(ids or [uuid.uuid4()]))
        rows = (await db.scalars(stmt.limit(10000))).all()
        return [org_service.sector_to_payload(row) for row in rows]

    if resource == "purposes":
        stmt = select(OrganizationPurpose).where(OrganizationPurpose.is_active != 0)
        if scope_selected:
            stmt = stmt.where(OrganizationPurpose.id.in_(ids or [uuid.uuid4()]))
        rows = (await db.scalars(stmt.limit(10000))).all()
        return [org_service.purpose_to_payload(row) for row in rows]

    if resource == "officers":
        stmt = select(Officer).where(Officer.is_active != 0)
        if scope_selected:
            stmt = stmt.where(Officer.id.in_(ids or [uuid.uuid4()]))
        rows = (await db.scalars(stmt.limit(10000))).all()
        return [people.officer_to_payload(row) for row in rows]

    if resource == "roles":
        stmt = select(Role).where(Role.is_active != 0)
        if scope_selected:
            stmt = stmt.where(Role.id.in_(ids or [uuid.uuid4()]))
        rows = (await db.scalars(stmt.limit(10000))).all()
        out = []
        for row in rows:
            out.append(people.role_to_payload(row, await people.permissions_for_role_id(db, row.id)))
        return out

    if resource == "users":
        stmt = select(User).where(User.status != "deleted")
        if scope_selected:
            stmt = stmt.where(User.id.in_(ids or [uuid.uuid4()]))
        rows = (await db.scalars(stmt.limit(10000))).all()
        return [people.user_to_payload(row) for row in rows]

    if resource == "record-types":
        stmt = select(RecordType)
        if scope_selected:
            stmt = stmt.where(RecordType.id.in_(ids or [uuid.uuid4()]))
        rows = (await db.scalars(stmt.limit(10000))).all()
        return [{"id": str(r.id), "code": r.code, "name": r.nam or r.code, "description": r.description, **(r.payload or {})} for r in rows]

    if resource == "record-attributes":
        stmt = select(RecordAttribute)
        if scope_selected:
            stmt = stmt.where(RecordAttribute.id.in_(ids or [uuid.uuid4()]))
        rows = (await db.scalars(stmt.limit(10000))).all()
        return [{"id": str(r.id), "code": r.code, "name": r.nam or r.code, "dataType": r.data_type, **(r.payload or {})} for r in rows]

    if resource == "file-uploads":
        stmt = select(File).where(File.status != "deleted")
        if scope_selected:
            stmt = stmt.where(File.id.in_(ids or [uuid.uuid4()]))
        rows = (await db.scalars(stmt.limit(10000))).all()
        return [{"id": str(r.id), "name": r.nam, "objectKey": r.path, "sizeBytes": r.file_size, "mimeType": r.mime_type, "status": r.status} for r in rows]

    if resource in {"record-logs", "portal-logs", "system-logs"}:
        source = {"portal-logs": "portal", "system-logs": "system"}.get(resource, "record")
        filters = [AuditLog.source_log == source] if source != "record" else [AuditLog.source_log.in_(("record", "api", "unknown"))]
        rows = (await db.scalars(select(AuditLog).where(*filters).order_by(AuditLog.created_at.desc()).limit(10000))).all()
        return [{
            "id": str(row.id),
            "summary": row.message or row.action_code,
            "action": row.action_code,
            "entityType": row.table_name,
            "occurredAt": row.created_at.isoformat() if row.created_at else None,
            "status": row.status_code,
        } for row in rows]

    # Remaining portal bags still on Entity (drive sync / export metadata)
    stmt = select(Entity).where(Entity.resource == resource, Entity.status != "deleted")
    if scope_selected:
        stmt = stmt.where(Entity.id.in_(ids or [uuid.uuid4()]))
    rows = (await db.scalars(stmt.order_by(Entity.updated_at.desc()).limit(10000))).all()
    return [
        {"id": str(row.id), **(row.payload or {}), "status": row.status, "stage": row.stage,
         "createdAt": row.created_at.isoformat() if row.created_at else None,
         "updatedAt": row.updated_at.isoformat() if row.updated_at else None}
        for row in rows
    ]


async def generate_export(db: AsyncSession, job: Entity) -> None:
    payload = dict(job.payload or {})
    resource = RESOURCE_MAP.get(str(payload.get("resource")), str(payload.get("resource") or ""))
    if not resource:
        raise ValueError("Export resource is required")
    values_list = await _rows_for_resource(db, resource, payload)
    fields = [str(x) for x in payload.get("fieldCodes") or [] if str(x) not in {"password", "passwordHash", "secret", "token", "objectKey"}]
    if not fields:
        fields = sorted({key for row in values_list for key in row.keys() if key not in {"password", "passwordHash", "secret", "token", "objectKey"}})
    fields = ["id", *[f for f in fields if f != "id"]]
    output = StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    for values in values_list:
        writer.writerow({key: _cell(values.get(key)) for key in fields})
    data = output.getvalue().encode("utf-8-sig")
    filename = f"{resource}-{datetime.now(timezone.utc):%Y%m%d-%H%M%S}.csv"
    key = f"exports/{job.id}/{filename}"
    await put_bytes(key, data, "text/csv; charset=utf-8")
    payload.update({
        "status": "completed",
        "objectKey": key,
        "fileName": filename,
        "mimeType": "text/csv",
        "sizeBytes": len(data),
        "downloadUrl": f"/api/v2/files/{job.id}",
        "completedAt": datetime.now(timezone.utc).isoformat(),
        "expiresAt": (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat(),
    })
    job.payload = payload
