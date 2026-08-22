from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.datetime import iso_utc
from app.core.frontend_contract import (
    RESOURCE_SOURCE_LABEL,
    entity_url,
    search_entity_type,
    user_can_view_resource,
    view_permission,
)
from app.models.organization import Organization
from app.models.people import Officer, User
from app.models.record import Record
from app.models.storage import File
from app.modules.organization.domain.map import RESOURCE_FOR_DB_ORG_TYPE
from app.modules.record.domain.map import RECORD_RESOURCES

CODE_TO_RESOURCE = {code: resource for resource, code in RECORD_RESOURCES.items()}


def build_search_hit(
    *,
    resource: str,
    entity_id: str,
    title: str,
    description: str | None = None,
    updated_at: datetime | None = None,
) -> dict[str, Any]:
    text = str(description or title)
    return {
        "id": entity_id,
        "entityId": entity_id,
        "entityType": search_entity_type(resource),
        "title": title,
        "text": text,
        "snippet": text[:220],
        "url": entity_url(resource, entity_id),
        "permission": view_permission(resource),
        "updatedAt": iso_utc(updated_at),
        "score": 1,
        "sourceLabel": RESOURCE_SOURCE_LABEL.get(resource, resource.replace("-", " ").title()),
    }


async def search_entities(
    db: AsyncSession,
    user: User,
    *,
    query: str,
    limit: int = 12,
) -> list[dict]:
    needle = query.strip()
    if not needle:
        return []
    pattern = f"%{needle}%"
    cap = min(limit, 50)
    hits: list[dict] = []

    records = (
        await db.scalars(
            select(Record)
            .where(
                Record.lifecycle.notin_(("archived", "deleted")),
                or_(Record.title.ilike(pattern), Record.record_content.ilike(pattern)),
            )
            .order_by(Record.updated_at.desc())
            .limit(cap)
        )
    ).all()
    for row in records:
        resource = CODE_TO_RESOURCE.get(row.record_type_code or "")
        if not resource or not user_can_view_resource(user, resource):
            continue
        hits.append(
            build_search_hit(
                resource=resource,
                entity_id=str(row.id),
                title=row.title or str(row.id),
                description=row.record_content or row.title,
                updated_at=row.updated_at,
            )
        )

    orgs = (
        await db.scalars(
            select(Organization)
            .where(Organization.is_active == 1, Organization.nam.ilike(pattern))
            .order_by(Organization.updated_at.desc())
            .limit(cap)
        )
    ).all()
    for row in orgs:
        resource = RESOURCE_FOR_DB_ORG_TYPE.get(row.organization_type)
        if not resource or not user_can_view_resource(user, resource):
            continue
        hits.append(
            build_search_hit(
                resource=resource,
                entity_id=str(row.id),
                title=row.nam or str(row.id),
                description=row.description or row.nam,
                updated_at=row.updated_at,
            )
        )

    if user_can_view_resource(user, "officers"):
        officers = (
            await db.scalars(
                select(Officer)
                .where(Officer.is_active == 1, or_(Officer.nam.ilike(pattern), Officer.email.ilike(pattern)))
                .order_by(Officer.updated_at.desc())
                .limit(cap)
            )
        ).all()
        for row in officers:
            hits.append(
                build_search_hit(
                    resource="officers",
                    entity_id=str(row.id),
                    title=row.nam or str(row.id),
                    description=row.email or row.nam,
                    updated_at=row.updated_at,
                )
            )

    if user_can_view_resource(user, "file-uploads"):
        files = (
            await db.scalars(
                select(File)
                .where(File.status != "deleted", File.nam.ilike(pattern))
                .order_by(File.updated_at.desc())
                .limit(cap)
            )
        ).all()
        for row in files:
            hits.append(
                build_search_hit(
                    resource="file-uploads",
                    entity_id=str(row.id),
                    title=row.nam or str(row.id),
                    description=row.nam,
                    updated_at=row.updated_at,
                )
            )

    hits.sort(key=lambda item: item.get("updatedAt") or "", reverse=True)
    return hits[:cap]
