"""Thin entity router wiring — delegates to services layer."""

from app.modules.record.services.stamp import entity_or_404, stamp
from app.modules.record.services.router_factory import router_for

__all__ = ["entity_or_404", "router_for", "stamp"]
