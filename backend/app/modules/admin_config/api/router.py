"""admin_config HTTP — configuration + app settings."""

from fastapi import APIRouter

from app.modules.admin_config.api import configuration, settings

router = APIRouter()
router.include_router(configuration.router)
router.include_router(settings.router)
