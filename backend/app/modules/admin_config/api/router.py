"""Admin Config HTTP — general application settings."""

from fastapi import APIRouter

from app.modules.admin_config.api import settings

router = APIRouter()
router.include_router(settings.router)
