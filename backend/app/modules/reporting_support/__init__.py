"""reporting_support — exports and reporting-ready data preparation."""

from __future__ import annotations

from typing import Any

__all__ = ["export_service", "search_service", "dashboard_service", "mention_service"]


def __getattr__(name: str) -> Any:
    if name == "export_service":
        from app.modules.reporting_support.services import export as export_service

        return export_service
    if name == "search_service":
        from app.modules.reporting_support.services import search as search_service

        return search_service
    if name == "dashboard_service":
        from app.modules.reporting_support.services import dashboard as dashboard_service

        return dashboard_service
    if name == "mention_service":
        from app.modules.reporting_support.services import mentions as mention_service

        return mention_service
    raise AttributeError(name)
