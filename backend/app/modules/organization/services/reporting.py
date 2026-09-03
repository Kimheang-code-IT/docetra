"""Organization-owned reporting read methods."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.organization.domain.map import ORG_RESOURCES
from app.modules.organization.model import Organization, OrganizationPurpose, OrganizationSector
from app.modules.organization.services import service


def _range(column, start: datetime | None, end: datetime | None) -> list:
    return ([column >= start] if start else []) + ([column <= end] if end else [])


async def read_for_reporting(
    db: AsyncSession,
    resource: str,
    ids: list[uuid.UUID] | None,
    start: datetime | None,
    end: datetime | None,
) -> list[dict] | None:
    if resource in ORG_RESOURCES:
        stmt = select(Organization).where(
            Organization.organization_type == ORG_RESOURCES[resource],
            Organization.is_active != 0,
            *_range(Organization.created_at, start, end),
        )
        model, serializer = Organization, service.org_to_payload
    elif resource == "sectors":
        stmt = select(OrganizationSector).where(
            OrganizationSector.is_active != 0,
            *_range(OrganizationSector.created_at, start, end),
        )
        model, serializer = OrganizationSector, service.sector_to_payload
    elif resource == "purposes":
        stmt = select(OrganizationPurpose).where(
            OrganizationPurpose.is_active != 0,
            *_range(OrganizationPurpose.created_at, start, end),
        )
        model, serializer = OrganizationPurpose, service.purpose_to_payload
    else:
        return None
    if ids is not None:
        stmt = stmt.where(model.id.in_(ids or [uuid.uuid4()]))
    rows = (await db.scalars(stmt.order_by(model.updated_at.desc()).limit(10000))).all()
    return [serializer(row) for row in rows]


async def search_for_reporting(db, pattern: str, limit: int) -> list[dict]:
    rows = (await db.scalars(
        select(Organization)
        .where(Organization.is_active == 1, Organization.nam.ilike(pattern))
        .order_by(Organization.updated_at.desc())
        .limit(limit)
    )).all()
    from app.modules.organization.domain.map import RESOURCE_FOR_DB_ORG_TYPE

    return [
        {
            "resource": RESOURCE_FOR_DB_ORG_TYPE.get(row.organization_type),
            "id": str(row.id),
            "title": row.nam or str(row.id),
            "description": row.description or row.nam,
            "updatedAt": row.updated_at,
        }
        for row in rows
        if RESOURCE_FOR_DB_ORG_TYPE.get(row.organization_type)
    ]
