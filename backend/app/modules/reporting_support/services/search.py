from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.datetime import iso_utc
from app.core.frontend_contract import RESOURCE_SOURCE_LABEL, entity_url, search_entity_type, user_can_view_resource, view_permission
from app.modules.organization.service import search_for_reporting as search_organizations
from app.modules.people_access.service import search_for_reporting as search_people
from app.modules.record.service import search_for_reporting as search_records
from app.modules.storage_integration.service import search_for_reporting as search_storage


def build_search_hit(*, resource: str, entity_id: str, title: str, description: str | None = None, updated_at: datetime | None = None) -> dict[str, Any]:
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


async def search_entities(db: AsyncSession, user: object, *, query: str, limit: int = 12) -> list[dict]:
    needle = query.strip()
    if not needle:
        return []
    cap = min(limit, 50)
    pattern = f"%{needle}%"
    candidates: list[dict] = []
    for reader in (search_records, search_organizations, search_people, search_storage):
        candidates.extend(await reader(db, pattern, cap))
    hits = [
        build_search_hit(
            resource=item["resource"],
            entity_id=item["id"],
            title=item["title"],
            description=item.get("description"),
            updated_at=item.get("updatedAt"),
        )
        for item in candidates
        if item.get("resource") and user_can_view_resource(user, item["resource"])
    ]
    hits.sort(key=lambda item: item.get("updatedAt") or "", reverse=True)
    return hits[:cap]
