"""admin_config — record types, record attributes, app configuration, and system settings."""

from __future__ import annotations

from typing import Any

__all__ = ["configuration_service", "settings_service", "runtime_settings"]


def __getattr__(name: str) -> Any:
    if name == "configuration_service":
        from app.modules.admin_config.services import configuration as configuration_service

        return configuration_service
    if name == "settings_service":
        from app.modules.admin_config.services import settings as settings_service

        return settings_service
    if name == "runtime_settings":
        from app.modules.admin_config.services import runtime as runtime_settings

        return runtime_settings
    raise AttributeError(name)
