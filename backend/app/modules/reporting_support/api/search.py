from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v2.deps import current_user, get_db
from app.core.authorization import require_permission
from app.core.http_schemas import DataEnvelope
from typing import Any as User
from app.modules.reporting_support.domain.schemas import AskRequest
from app.modules.reporting_support.services.search import search_entities

router = APIRouter(prefix="/search", tags=["search"])


@router.get("", response_model=DataEnvelope)
async def search(q: str = "", mode: str = "keyword", limit: int = 12, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    # No approved semantic/AI provider exists in this deployment. Only keyword
    # search is served; the meta block states this honestly so the frontend
    # cannot present keyword hits as semantic results.
    hits = await search_entities(db, user, query=q, limit=limit)
    return {"data": hits, "meta": {"mode": "keyword", "semanticAvailable": False}}


@router.post("/ask", response_model=DataEnvelope)
async def ask(body: AskRequest, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    # Honest placeholder: no AI provider is approved, so no generated answer is
    # produced. Citations are real keyword matches the user can open.
    citations = await search_entities(db, user, query=body.q, limit=5)
    return {
        "data": {
            "available": False,
            "answer": None,
            "message": "Ask AI is not available yet — no AI provider is configured.",
            "citations": citations,
        }
    }
