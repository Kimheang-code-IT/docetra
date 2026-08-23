from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v2.deps import current_user, get_db
from app.core.authorization import require_permission
from app.core.http_schemas import DataEnvelope
from app.db import User
from app.modules.reporting_support.domain.schemas import AskRequest
from app.modules.reporting_support.services.search import search_entities

router = APIRouter(prefix="/search", tags=["search"])


@router.get("", response_model=DataEnvelope)
async def search(q: str = "", mode: str = "keyword", limit: int = 12, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    return {"data": await search_entities(db, user, query=q, limit=limit)}


@router.post("/ask", response_model=DataEnvelope)
async def ask(body: AskRequest, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    citations = await search_entities(db, user, query=body.q, limit=5)
    titles = ", ".join(item.get("title") or "" for item in citations) or "no permitted sources"
    return {"data": {"answer": f"Summary for “{body.q}” from {titles}. Open each citation to verify.", "citations": citations}}
