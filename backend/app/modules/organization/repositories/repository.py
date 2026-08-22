"""Organization repository."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.organization import Organization, OrganizationPurpose, OrganizationSector
from app.shared import get_or_404, paginate


async def get_organization(db: AsyncSession, org_id: str | uuid.UUID) -> Organization:
    return await get_or_404(db, Organization, org_id)


async def list_by_type(db: AsyncSession, organization_type: str, *, page: int = 1, limit: int = 20, filters: list | None = None):
    stmt = select(Organization).where(Organization.organization_type == organization_type)
    for clause in filters or []:
        stmt = stmt.where(clause)
    stmt = stmt.order_by(Organization.updated_at.desc(), Organization.id)
    rows, total = await paginate(db, stmt, page=page, limit=limit)
    return list(rows), total


async def list_sectors(db: AsyncSession) -> list[OrganizationSector]:
    return list((await db.scalars(select(OrganizationSector).order_by(OrganizationSector.updated_at.desc()))).all())


async def list_purposes(db: AsyncSession) -> list[OrganizationPurpose]:
    return list((await db.scalars(select(OrganizationPurpose).order_by(OrganizationPurpose.updated_at.desc()))).all())
