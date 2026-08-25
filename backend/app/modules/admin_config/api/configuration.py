import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v2.deps import current_user, get_db
from app.api.v2.entities import router_for
from app.core.authorization import require_permission
from app.core.http_schemas import DataEnvelope
from app.core.privileged import is_unrestricted
from app.db import User
from app.models.organization import Organization
from app.models.record import RecordType
from app.modules.record.domain.map import permission_prefix_for_type_code, resolve_type_code
import app.modules.admin_config.services.configuration as record_schema
import app.modules.record.services.type_access as type_access

router = APIRouter(tags=["configuration"])
router.include_router(router_for("configuration/record-types", "record-types"))
router.include_router(router_for("configuration/record-attributes", "record-attributes"))


class ShareRecordTypeBody(BaseModel):
    organizationId: str


def _authorize_schema_read(user: User, type_code: str) -> None:
    if is_unrestricted(user):
        return
    perms = set(user.permissions or [])
    if "configuration.record_types.view" in perms:
        return
    prefix = permission_prefix_for_type_code(type_code)
    if f"{prefix}.view" in perms:
        return
    require_permission(user, "configuration.record_types.view")


def _authorize_type_share(user: User) -> None:
    if is_unrestricted(user):
        return
    perms = set(user.permissions or [])
    if "configuration.record_types.edit" in perms or "configuration.record_types.configure" in perms:
        return
    require_permission(user, "configuration.record_types.edit")


def _as_uuid(value: str, label: str) -> uuid.UUID:
    try:
        return uuid.UUID(str(value))
    except (ValueError, TypeError, AttributeError) as exc:
        raise HTTPException(404, f"{label} not found") from exc


async def _type_or_404(db: AsyncSession, entity_id: str) -> RecordType:
    row = await db.get(RecordType, _as_uuid(entity_id, "Record type"))
    if not row:
        raise HTTPException(404, "Record type not found")
    return row


@router.get("/configuration/record-types/by-code/{code}/schema", response_model=DataEnvelope)
async def schema_by_code(code: str, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    resolved = resolve_type_code(code)
    _authorize_schema_read(user, resolved)
    return {"data": await record_schema.schema_by_code(db, resolved, user)}


@router.get("/configuration/record-types/{entity_id}/schema", response_model=DataEnvelope)
async def schema_by_id(entity_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    data = await record_schema.schema_by_id(db, entity_id, user)
    _authorize_schema_read(user, data["recordType"]["code"])
    return {"data": data}


@router.get("/configuration/record-types/{entity_id}/permissions", response_model=DataEnvelope)
async def list_type_permissions(
    entity_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    row = await _type_or_404(db, entity_id)
    await type_access.require_type_access(db, row, user)
    _authorize_schema_read(user, row.code)
    rows = await type_access.list_permissions(db, row.id)
    return {"data": [type_access.permission_row_payload(item) for item in rows]}


@router.post("/configuration/record-types/{entity_id}/permissions", response_model=DataEnvelope)
async def share_record_type(
    entity_id: str,
    body: ShareRecordTypeBody,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    _authorize_type_share(user)
    row = await _type_or_404(db, entity_id)
    await type_access.require_owner_access(db, row, user)
    org_id = _as_uuid(body.organizationId, "Organization")
    organization = await db.get(Organization, org_id)
    if not organization:
        raise HTTPException(404, "Organization not found")
    from app.modules.people_access.services.people import ensure_officer_for_user

    officer = await ensure_officer_for_user(db, user)
    granted = await type_access.grant(
        db,
        row.id,
        org_id,
        permission_kind=type_access.SHARED,
        actor_officer_id=officer.id,
    )
    await db.commit()
    await db.refresh(granted)
    return {"data": type_access.permission_row_payload(granted)}


@router.delete("/configuration/record-types/{entity_id}/permissions/{organization_id}", response_model=DataEnvelope)
async def unshare_record_type(
    entity_id: str,
    organization_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    _authorize_type_share(user)
    row = await _type_or_404(db, entity_id)
    await type_access.require_owner_access(db, row, user)
    await type_access.revoke(db, row.id, _as_uuid(organization_id, "Organization"))
    await db.commit()
    return {"data": {"organizationId": organization_id}}
