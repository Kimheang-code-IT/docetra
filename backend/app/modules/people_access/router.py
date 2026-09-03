"""Public HTTP facade for People Access."""

from app.modules.people_access.api.router import router

__all__ = ["router"]
