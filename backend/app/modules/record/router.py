"""Public HTTP facade for Record."""

from app.modules.record.api.configuration import router as configuration_router
from app.modules.record.api.router import router

__all__ = ["configuration_router", "router"]
