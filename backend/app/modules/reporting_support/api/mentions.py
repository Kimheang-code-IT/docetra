from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v2.deps import current_user, get_db
from app.core.http_schemas import DataEnvelope
from typing import Any as User
from app.modules.reporting_support.services.mentions import search_mentions

router = APIRouter(prefix="/mentions", tags=["mentions"])


@router.get("", response_model=DataEnvelope)
async def mentions(q: str = "", type: str = "officer", limit: int = 20, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    return {"data": await search_mentions(db, q, type, limit)}
