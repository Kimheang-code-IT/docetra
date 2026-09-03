"""Thin entity router wiring — delegates to services layer."""

from app.modules.record.service import router_for

__all__ = ["router_for"]
