"""Public application-service facade for Admin Config."""

from app.modules.admin_config.services import runtime, settings
from app.modules.admin_config.services.settings import merge_setting

__all__ = ["merge_setting", "runtime", "settings"]
