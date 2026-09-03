"""Runtime App Config resolver — AppSetting preferred, env as bootstrap fallback."""

from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import short_cache
from app.core.config import settings
from app.core.secrets import reveal_mapping
from app.modules.admin_config.model import AppSetting
from app.modules.admin_config.services.settings import DEFAULT_APP_CONFIG, merge_setting

CACHE_KEY = "runtime:app-config"
CACHE_TTL = 45


def _deep_merge_defaults(stored: dict) -> dict:
    return merge_setting(DEFAULT_APP_CONFIG, stored or {})


async def invalidate_app_config_cache() -> None:
    try:
        await short_cache.redis.delete(f"{short_cache.prefix}:{CACHE_KEY}")
    except Exception:
        pass


async def load_app_config(db: AsyncSession | None = None) -> dict[str, Any]:
    cached = None
    try:
        cached = await short_cache.get(CACHE_KEY)
    except Exception:
        cached = None
    if isinstance(cached, dict):
        return cached

    raw: dict = {}
    if db is not None:
        row = await db.get(AppSetting, "app-config")
        if row and row.value:
            raw = reveal_mapping(dict(row.value))
    else:
        from app.db.session import SessionLocal

        async with SessionLocal() as session:
            row = await session.get(AppSetting, "app-config")
            if row and row.value:
                raw = reveal_mapping(dict(row.value))

    config = _deep_merge_defaults(raw)
    try:
        await short_cache.set(CACHE_KEY, config, CACHE_TTL)
    except Exception:
        pass
    return config


def email_smtp(config: dict | None = None) -> dict[str, Any]:
    section = dict((config or {}).get("email") or {})
    encryption = str(section.get("encryption") or "starttls").lower()
    use_tls = encryption in {"starttls", "tls", "ssl"} if section.get("encryption") is not None else settings.smtp_use_tls
    enabled = bool(section.get("enabled")) if "enabled" in section else bool(settings.smtp_host)
    host = str(section.get("smtpHost") or settings.smtp_host or "")
    return {
        "enabled": enabled and bool(host),
        "smtpHost": host,
        "smtpPort": int(section.get("smtpPort") or settings.smtp_port or 587),
        "username": str(section.get("username") or settings.smtp_username or ""),
        "password": str(section.get("password") or settings.smtp_password or ""),
        "useTls": use_tls,
        "fromName": str(section.get("fromName") or "Docetra"),
        "fromEmail": str(section.get("fromEmail") or settings.email_from_address or ""),
        "timeoutSeconds": int(section.get("timeoutSeconds") or 10),
    }


def telegram_meeting(config: dict | None = None) -> dict[str, Any]:
    section = dict((config or {}).get("telegram") or {})
    token = str(section.get("botToken") or settings.telegram_meeting_bot_token or "")
    enabled = bool(section.get("enabled")) if "enabled" in section else bool(settings.telegram_meeting_bot_enabled)
    return {
        "enabled": enabled and bool(token),
        "botToken": token,
        "botDisplayName": str(section.get("botDisplayName") or "Docetra"),
        "destinations": list(section.get("destinations") or []),
        "messageTemplate": str(
            section.get("messageTemplate")
            or "[{{record_type}}] {{record_number}}\n{{record_title}}"
        ),
        "includeRecordLink": bool(section.get("includeRecordLink", True)),
        "includeOrganization": bool(section.get("includeOrganization", True)),
        "includeAssignedOfficer": bool(section.get("includeAssignedOfficer", True)),
    }


def upload_policy(config: dict | None = None) -> dict[str, Any]:
    general = dict((config or {}).get("general") or {})
    security = dict((config or {}).get("security") or {})
    max_mb = int(general.get("maxUploadSizeMb") or settings.max_upload_size_mb or 25)
    extensions = security.get("allowedUploadExtensions")
    if not isinstance(extensions, list) or not extensions:
        extensions = list(settings.allowed_upload_extensions)
    return {
        "maxUploadSizeMb": max_mb,
        "allowedUploadExtensions": [str(ext).lower().lstrip(".") for ext in extensions],
    }


def security_policy(config: dict | None = None) -> dict[str, Any]:
    security = dict((config or {}).get("security") or {})
    return {
        "sessionTimeoutMinutes": int(
            security.get("sessionTimeoutMinutes") or settings.session_timeout_minutes or settings.jwt_access_minutes or 480
        ),
        "maxLoginAttempts": int(security.get("maxLoginAttempts") or settings.max_login_failures or 5),
        "accountLockMinutes": int(security.get("accountLockMinutes") or settings.account_lock_minutes or 15),
        "allowedUploadExtensions": upload_policy(config)["allowedUploadExtensions"],
    }


def meeting_reminders(config: dict | None = None) -> dict[str, Any]:
    notifications = dict((config or {}).get("notifications") or {})
    offsets = notifications.get("meetingReminderOffsetsMinutes")
    if not isinstance(offsets, list) or not offsets:
        offsets = list(settings.meeting_reminder_offsets_minutes)
    horizon = notifications.get("meetingRecurrenceHorizonDays")
    if horizon is None:
        horizon = settings.meeting_recurrence_horizon_days
    return {
        "meetingReminderOffsetsMinutes": [int(x) for x in offsets],
        "meetingRecurrenceHorizonDays": int(horizon),
    }


def general_defaults(config: dict | None = None) -> dict[str, Any]:
    general = dict((config or {}).get("general") or {})
    system = dict((config or {}).get("system") or {})
    page_size = int(general.get("defaultPageSize") or system.get("paginationDefault") or 20)
    return {
        "defaultPageSize": max(1, min(100, page_size)),
        "defaultLandingPage": str(general.get("defaultLandingPage") or "/"),
        "defaultRecordView": str(general.get("defaultRecordView") or "table"),
        "enableComments": bool(general.get("enableComments", True)),
        "enableSharing": bool(general.get("enableSharing", True)),
        "enableExport": bool(general.get("enableExport", True)),
        "maxUploadSizeMb": upload_policy(config)["maxUploadSizeMb"],
        "maintenanceMode": bool(system.get("maintenanceMode", False)),
        "readOnlyMode": bool(system.get("readOnlyMode", False)),
    }


def render_telegram_template(template: str, *, title: str, kind: str, record_type: str = "meeting", record_number: str = "") -> str:
    text = template
    replacements = {
        "{{record_type}}": record_type,
        "{{record_number}}": record_number or kind,
        "{{record_title}}": title,
        "{{title}}": title,
        "{{kind}}": kind,
    }
    for key, value in replacements.items():
        text = text.replace(key, str(value))
    return text
