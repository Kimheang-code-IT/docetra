"""Organization access to record types.

Join types by `record_type.id`. `code` is informational and is resolved only
inside the caller's permitted set. A creator org owns a type; sharing inserts
additional `record_type_permission` rows for other organizations.
"""

from __future__ import annotations

import uuid
from typing import Iterable

from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.datetime import iso_utc
from app.core.privileged import is_unrestricted
from typing import Any as User
from app.modules.record.model import Record, RecordOrganization, RecordType, RecordTypePermission
from app.modules.organization.service import service as organization_service
from app.modules.people_access.service import ensure_officer_for_user, officer_ids_for_organization, officer_organization_id

OWNER = "owner"
SHARED = "shared"


def pick_type_for_code(
    candidates: Iterable[tuple[RecordType, str]],
    code: str,
) -> RecordType | None:
    """Prefer the owner grant, then oldest type, among rows with this code."""
    matched = [(row, kind) for row, kind in candidates if row.code == code]
    if not matched:
        return None
    owners = [row for row, kind in matched if kind == OWNER]
    pool = owners or [row for row, _ in matched]
    return sorted(pool, key=lambda row: (row.created_at or row.id, str(row.id)))[0]


async def organization_id_for_officer(db: AsyncSession, officer_id: uuid.UUID | None) -> uuid.UUID | None:
    return await officer_organization_id(db, officer_id)


async def actor_organization_id(db: AsyncSession, user: User | None) -> uuid.UUID | None:
    if user is None:
        return None
    officer = await ensure_officer_for_user(db, user)
    return officer.organization_id


async def list_permissions(db: AsyncSession, record_type_id: uuid.UUID) -> list[RecordTypePermission]:
    return list(
        (await db.scalars(
            select(RecordTypePermission)
            .where(RecordTypePermission.record_type_id == record_type_id)
            .order_by(RecordTypePermission.created_at)
        )).all()
    )


async def permitted_type_ids(db: AsyncSession, organization_id: uuid.UUID | None) -> list[uuid.UUID]:
    if organization_id is None:
        return []
    rows = (await db.scalars(
        select(RecordTypePermission.record_type_id).where(
            RecordTypePermission.organization_id == organization_id,
        )
    )).all()
    return list(rows)


async def org_can_access_type(
    db: AsyncSession,
    record_type_id: uuid.UUID,
    organization_id: uuid.UUID | None,
    *,
    unrestricted: bool = False,
) -> bool:
    if unrestricted:
        return True
    if organization_id is None:
        return False
    row = await db.scalar(
        select(RecordTypePermission.id).where(
            RecordTypePermission.record_type_id == record_type_id,
            RecordTypePermission.organization_id == organization_id,
        )
    )
    return row is not None


async def org_owns_type(
    db: AsyncSession,
    record_type_id: uuid.UUID,
    organization_id: uuid.UUID | None,
    *,
    unrestricted: bool = False,
) -> bool:
    if unrestricted:
        return True
    if organization_id is None:
        return False
    row = await db.scalar(
        select(RecordTypePermission.id).where(
            RecordTypePermission.record_type_id == record_type_id,
            RecordTypePermission.organization_id == organization_id,
            RecordTypePermission.permission_kind == OWNER,
        )
    )
    return row is not None


async def grant(
    db: AsyncSession,
    record_type_id: uuid.UUID,
    organization_id: uuid.UUID,
    *,
    permission_kind: str = SHARED,
    actor_officer_id: uuid.UUID | None = None,
) -> RecordTypePermission:
    kind = permission_kind if permission_kind in {OWNER, SHARED} else SHARED
    if kind == OWNER:
        other = await db.scalar(
            select(RecordTypePermission.id).where(
                RecordTypePermission.record_type_id == record_type_id,
                RecordTypePermission.permission_kind == OWNER,
                RecordTypePermission.organization_id != organization_id,
            )
        )
        if other:
            raise HTTPException(409, "Record type already has an owner organization")
    existing = await db.scalar(
        select(RecordTypePermission).where(
            RecordTypePermission.record_type_id == record_type_id,
            RecordTypePermission.organization_id == organization_id,
        )
    )
    if existing:
        if kind == OWNER and existing.permission_kind != OWNER:
            existing.permission_kind = OWNER
            existing.updated_by = actor_officer_id
        return existing
    row = RecordTypePermission(
        organization_id=organization_id,
        record_type_id=record_type_id,
        permission_kind=kind,
        created_by=actor_officer_id,
        updated_by=actor_officer_id,
    )
    db.add(row)
    await db.flush()
    return row


async def share_builtin_types(
    db: AsyncSession,
    organization_id: uuid.UUID,
    actor_officer_id: uuid.UUID | None = None,
) -> None:
    """Grant the oldest built-in type of each code to a newly created organization."""
    from app.modules.record.domain.map import TYPE_UI_DEFAULTS

    for code in TYPE_UI_DEFAULTS:
        row = await db.scalar(
            select(RecordType).where(RecordType.code == code).order_by(RecordType.created_at, RecordType.id)
        )
        if row:
            await grant(db, row.id, organization_id, permission_kind=SHARED, actor_officer_id=actor_officer_id)


async def backfill_shared_grants_if_empty(db: AsyncSession, record_type_id: uuid.UUID) -> None:
    """Legacy global types (no owner) become visible to every current organization."""
    count = await db.scalar(
        select(func.count()).select_from(RecordTypePermission).where(
            RecordTypePermission.record_type_id == record_type_id,
        )
    )
    if count:
        return
    org_ids = await organization_service.list_organization_ids(db)
    for org_id in org_ids:
        await grant(db, record_type_id, org_id, permission_kind=SHARED)


async def revoke(
    db: AsyncSession,
    record_type_id: uuid.UUID,
    organization_id: uuid.UUID,
) -> None:
    row = await db.scalar(
        select(RecordTypePermission).where(
            RecordTypePermission.record_type_id == record_type_id,
            RecordTypePermission.organization_id == organization_id,
        )
    )
    if not row:
        raise HTTPException(404, "Record type permission not found")
    if row.permission_kind == OWNER:
        raise HTTPException(409, "Cannot remove the owner organization from a record type")
    await db.delete(row)
    await db.flush()


async def resolve_type_by_code(
    db: AsyncSession,
    code: str,
    *,
    organization_id: uuid.UUID | None = None,
    unrestricted: bool = False,
) -> RecordType | None:
    if organization_id is not None:
        pairs = (await db.execute(
            select(RecordType, RecordTypePermission.permission_kind)
            .join(RecordTypePermission, RecordTypePermission.record_type_id == RecordType.id)
            .where(
                RecordType.code == code,
                RecordTypePermission.organization_id == organization_id,
            )
        )).all()
        picked = pick_type_for_code([(row, kind) for row, kind in pairs], code)
        if picked:
            return picked
        if not unrestricted:
            return None
    if unrestricted:
        rows = list(
            (await db.scalars(
                select(RecordType).where(RecordType.code == code).order_by(RecordType.created_at)
            )).all()
        )
        return rows[0] if rows else None
    return None


async def permission_payload(db: AsyncSession, type_ids: list[uuid.UUID]) -> dict[uuid.UUID, dict]:
    payload = {
        type_id: {"ownerOrganizationId": None, "organizationIds": []}
        for type_id in type_ids
    }
    if not type_ids:
        return payload
    rows = (await db.scalars(
        select(RecordTypePermission).where(RecordTypePermission.record_type_id.in_(type_ids))
    )).all()
    for row in rows:
        entry = payload.setdefault(row.record_type_id, {"ownerOrganizationId": None, "organizationIds": []})
        entry["organizationIds"].append(str(row.organization_id))
        if row.permission_kind == OWNER:
            entry["ownerOrganizationId"] = str(row.organization_id)
    return payload


async def require_type_access(
    db: AsyncSession,
    record_type: RecordType,
    user: User | None,
) -> None:
    if user is None or is_unrestricted(user):
        return
    org_id = await actor_organization_id(db, user)
    # Accounts not attached to an organization are governed by their explicit
    # role permissions. Organization grants only narrow organization-scoped users.
    if org_id is None:
        return
    if not await org_can_access_type(db, record_type.id, org_id):
        raise HTTPException(404, "Record type not found")


async def require_owner_access(
    db: AsyncSession,
    record_type: RecordType,
    user: User | None,
) -> None:
    if user is None or is_unrestricted(user):
        return
    org_id = await actor_organization_id(db, user)
    if not await org_owns_type(db, record_type.id, org_id):
        raise HTTPException(403, "Only the owner organization can change this record type")


async def record_in_organization(db: AsyncSession, organization_id: uuid.UUID):
    officer_ids = await officer_ids_for_organization(db, organization_id)
    created_in_org = Record.created_by.in_(officer_ids)
    linked = Record.id.in_(
        select(RecordOrganization.record_id).where(RecordOrganization.organization_id == organization_id)
    )
    return or_(created_in_org, linked)


async def record_visible_to_user(db: AsyncSession, row: Record, user: User | None) -> bool:
    if user is None or is_unrestricted(user):
        return True
    org_id = await actor_organization_id(db, user)
    if org_id is None:
        return True
    if row.created_by:
        creator_org_id = await officer_organization_id(db, row.created_by)
        if creator_org_id == org_id:
            return True
    linked = await db.scalar(
        select(RecordOrganization.id).where(
            RecordOrganization.record_id == row.id,
            RecordOrganization.organization_id == org_id,
        )
    )
    return linked is not None


def permission_row_payload(row: RecordTypePermission) -> dict:
    return {
        "id": str(row.id),
        "organizationId": str(row.organization_id),
        "recordTypeId": str(row.record_type_id),
        "permissionKind": row.permission_kind,
        "createdAt": iso_utc(row.created_at),
        "updatedAt": iso_utc(row.updated_at),
    }
