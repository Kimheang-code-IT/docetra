"""Organization domain helpers for draft relational tables."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import DomainError
from app.modules.organization.model import Organization, OrganizationPurpose, OrganizationSector
from app.modules.organization.repository import OrganizationRepository


def org_to_payload(row: Organization) -> dict:
    purpose_id = str(row.organization_purpose_id) if row.organization_purpose_id else None
    return {
        "id": str(row.id),
        "name": row.nam,
        "code": row.code,
        "description": row.description,
        "parentId": str(row.parent_id) if row.parent_id else None,
        "sectorId": str(row.sector_id) if row.sector_id else None,
        "organizationPurposeId": purpose_id,
        "purposeId": purpose_id,
        "organizationType": row.organization_type,
        "taxId": row.tax_id,
        "address": row.address,
        "contactInfo": row.contact_info,
        "email": row.email,
        "phone": row.phone,
        "logoUrl": row.logo_url,
        "lvl": row.lvl,
        "status": "active" if row.is_active else "inactive",
        "createdAt": row.created_at.isoformat() if row.created_at else None,
        "updatedAt": row.updated_at.isoformat() if row.updated_at else None,
        "version": 1,
    }


def sector_to_payload(row: OrganizationSector) -> dict:
    return {
        "id": str(row.id),
        "name": row.nam,
        "parentId": str(row.parent_id) if row.parent_id else None,
        "description": row.description,
        "status": "active" if row.is_active else "inactive",
        "createdAt": row.created_at.isoformat() if row.created_at else None,
        "updatedAt": row.updated_at.isoformat() if row.updated_at else None,
        "version": 1,
    }


def purpose_to_payload(row: OrganizationPurpose) -> dict:
    return {
        "id": str(row.id),
        "name": row.nam,
        "description": row.description,
        "status": "active" if row.is_active else "inactive",
        "createdAt": row.created_at.isoformat() if row.created_at else None,
        "updatedAt": row.updated_at.isoformat() if row.updated_at else None,
        "version": 1,
    }


async def validate_org_parent(
    db: AsyncSession,
    entity_id: uuid.UUID | None,
    parent_id,
    *,
    organization_type: str | None = None,
) -> Organization | None:
    """Validate parent for hierarchy. When organization_type is set, parent must match."""
    if not parent_id:
        return None
    if entity_id and str(parent_id) == str(entity_id):
        raise DomainError("VALIDATION_ERROR", "An organization cannot be its own parent", 422)
    try:
        parent_uid = uuid.UUID(str(parent_id))
    except ValueError as exc:
        raise DomainError("VALIDATION_ERROR", "Invalid parent organization", 422) from exc

    parent = await db.get(Organization, parent_uid)
    if not parent:
        raise DomainError("VALIDATION_ERROR", "Parent organization not found", 422)
    if organization_type and parent.organization_type != organization_type:
        raise DomainError("VALIDATION_ERROR", "Parent must be the same organization type", 422)

    seen = {str(entity_id)} if entity_id else set()
    current = str(parent_id)
    for _ in range(50):
        if current in seen:
            raise DomainError("VALIDATION_ERROR", "Organization hierarchy would create a cycle", 422)
        seen.add(current)
        try:
            row = await db.get(Organization, uuid.UUID(current))
        except ValueError as exc:
            raise DomainError("VALIDATION_ERROR", "Invalid parent organization", 422) from exc
        if not row:
            break
        current = str(row.parent_id or "")
        if not current:
            break
    return parent


async def resolve_org_level(db: AsyncSession, parent_id) -> int:
    if not parent_id:
        return 1
    parent = await validate_org_parent(db, None, parent_id)
    return int(parent.lvl or 1) + 1 if parent else 1


async def resolve_sector_purpose_ids(
    db: AsyncSession,
    payload: dict,
    *,
    require_company: bool,
) -> tuple[uuid.UUID | None, uuid.UUID | None]:
    """Parse and validate sector/purpose FKs for company writes."""
    sector_raw = payload.get("sectorId")
    purpose_raw = payload.get("purposeId") if payload.get("purposeId") is not None else payload.get("organizationPurposeId")

    if not require_company:
        if sector_raw or purpose_raw:
            raise DomainError("VALIDATION_ERROR", "Sector and purpose apply only to companies", 422)
        return None, None

    sector_id = None
    purpose_id = None
    if sector_raw:
        try:
            sector_id = uuid.UUID(str(sector_raw))
        except ValueError as exc:
            raise DomainError("VALIDATION_ERROR", "Invalid sectorId", 422) from exc
        sector = await db.get(OrganizationSector, sector_id)
        if not sector or not sector.is_active:
            raise DomainError("VALIDATION_ERROR", "Sector not found or inactive", 422)
    if purpose_raw:
        try:
            purpose_id = uuid.UUID(str(purpose_raw))
        except ValueError as exc:
            raise DomainError("VALIDATION_ERROR", "Invalid purposeId", 422) from exc
        purpose = await db.get(OrganizationPurpose, purpose_id)
        if not purpose or not purpose.is_active:
            raise DomainError("VALIDATION_ERROR", "Purpose not found or inactive", 422)
    return sector_id, purpose_id


async def get_org(db: AsyncSession, org_id: str) -> Organization:
    try:
        uid = uuid.UUID(org_id)
    except ValueError as exc:
        raise DomainError("NOT_FOUND", "Not found", 404) from exc
    row = await OrganizationRepository(db).get(uid)
    if not row:
        raise DomainError("NOT_FOUND", "Not found", 404)
    return row


async def list_organization_ids(db: AsyncSession) -> list[uuid.UUID]:
    return await OrganizationRepository(db).ids()


async def organization_exists(db: AsyncSession, organization_id: uuid.UUID) -> bool:
    return await OrganizationRepository(db).get(organization_id) is not None


async def resolve_organization_ids(db: AsyncSession, values: list) -> list[uuid.UUID]:
    """Resolve UUID or name values to organization ids (legacy name support)."""
    ids: list[uuid.UUID] = []
    for raw in values:
        if raw in {None, ""}:
            continue
        text = str(raw).strip()
        try:
            uid = uuid.UUID(text)
            row = await db.get(Organization, uid)
            if row:
                ids.append(row.id)
            continue
        except ValueError:
            pass
        row = await db.scalar(select(Organization).where(Organization.nam == text).limit(1))
        if row:
            ids.append(row.id)
    # de-dupe preserve order
    seen: set[uuid.UUID] = set()
    out: list[uuid.UUID] = []
    for uid in ids:
        if uid not in seen:
            seen.add(uid)
            out.append(uid)
    return out
