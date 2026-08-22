"""storage_integration HTTP — portal, files, storage settings."""

from fastapi import APIRouter

from app.modules.storage_integration.api import files, portal, settings_storage

router = APIRouter()
router.include_router(portal.router)
router.include_router(files.router)
router.include_router(settings_storage.router)
