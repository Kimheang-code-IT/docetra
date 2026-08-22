from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v2.deps import current_user, get_db
from app.core.authorization import require_permission
from app.db import User
from app.modules.reporting_support.services.search import search_entities

router = APIRouter(prefix="/search", tags=["search"])


@router.get("")
async def search(q: str = "", mode: str = "keyword", limit: int = 12, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    return {"data": await search_entities(db, user, query=q, limit=limit)}


@router.post("/ask")
async def ask(body: dict, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    citations = await search_entities(db, user, query=str(body.get("q") or ""), limit=5)
    titles = ", ".join(item.get("title") or "" for item in citations) or "no permitted sources"
    return {"data": {"answer": f"Summary for “{body.get('q', '')}” from {titles}. Open each citation to verify.", "citations": citations}}
