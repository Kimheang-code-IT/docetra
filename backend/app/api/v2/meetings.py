from fastapi import APIRouter
from app.api.v2.entities import router_for
from app.api.v2.special import routes_for

router = APIRouter()
router.include_router(routes_for("/meetings"))
router.include_router(router_for("meetings/topics", "meeting-topics"))
router.include_router(router_for("meetings/history", "meeting-history"))
