from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v2.deps import current_user, get_db
from app.core.authorization import require_permission
from app.core.cache import short_cache
from app.core.http_schemas import DataEnvelope
from typing import Any as User
from app.modules.reporting_support.services.dashboard import build_dashboard_summary

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def dashboard_cache_key(user: User) -> str:
    """Per-identity cache key: never serve one user's permission-filtered
    dashboard to another user (or to the same user after permission changes)."""
    permissions = tuple(sorted(user.permissions or []))
    return f"dashboard:summary:{user.id}:{user.role}:{hash(permissions) % 10**16}"


@router.get("/summary", response_model=DataEnvelope)
async def dashboard(db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    require_permission(user, "dashboard.view")
    key = dashboard_cache_key(user)
    cached = await short_cache.get(key)
    if cached and isinstance(cached.get("kpis"), list):
        return {"data": cached}
    data = await build_dashboard_summary(db, user)
    await short_cache.set(key, data, 30)
    return {"data": data}
