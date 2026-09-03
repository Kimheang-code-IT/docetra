"""Reporting Support HTTP — dashboard, search, and mentions."""

from fastapi import APIRouter

from app.modules.reporting_support.api import dashboard, mentions, search

router = APIRouter()
router.include_router(dashboard.router)
router.include_router(search.router)
router.include_router(mentions.router)
