from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.organization.service import search_for_reporting as search_organizations
from app.modules.people_access.service import search_for_reporting as search_people


async def search_mentions(db: AsyncSession, q: str, mention_type: str, limit: int) -> list[dict]:
    cap = min(limit, 50)
    pattern = f"%{q}%"
    candidates = (
        await search_people(db, pattern, cap)
        if mention_type == "officer"
        else await search_organizations(db, pattern, cap)
    )
    expected = {"department": "departments", "company": "companies"}.get(mention_type)
    return [
        {"id": item["id"], "label": item["title"], "type": mention_type}
        for item in candidates
        if expected is None or item.get("resource") == expected
    ][:cap]
