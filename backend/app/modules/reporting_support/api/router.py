"""reporting_support HTTP — dashboard, search, exports, mentions."""

from fastapi import APIRouter

from app.modules.reporting_support.api import dashboard, exports, mentions, search

router = APIRouter()
router.include_router(dashboard.router)
router.include_router(search.router)
router.include_router(exports.router)
router.include_router(mentions.router)
