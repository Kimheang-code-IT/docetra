"""Public HTTP facades for Reporting Support."""

from app.modules.reporting_support.api.dashboard import router as dashboard_router
from app.modules.reporting_support.api.mentions import router as mentions_router
from app.modules.reporting_support.api.search import router as search_router

__all__ = ["dashboard_router", "mentions_router", "search_router"]
