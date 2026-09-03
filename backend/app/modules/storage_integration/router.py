"""Public HTTP facade for Storage Integration."""

from app.modules.storage_integration.api.router import router

__all__ = ["router"]
