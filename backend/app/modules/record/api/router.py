"""record HTTP — dynamic /records/{type_code}."""

from fastapi import APIRouter

from app.modules.record.api import dynamic_records

router = APIRouter()
router.include_router(dynamic_records.router)
