from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.datetime import iso_utc
from app.core.secrets import MASK, mask_mapping, protect_mapping, reveal_mapping
from app.modules.admin_config.model import AppSetting
from app.shared.dicts import deep_merge

DEFAULT_APP_CONFIG = {
    "general": {"defaultLandingPage": "/", "defaultPageSize": 20, "defaultRecordView": "table", "enableComments": True, "enableSharing": True, "enableExport": True, "maxUploadSizeMb": 25},
    "localization": {"defaultLanguage": "en", "timezone": "Asia/Phnom_Penh", "dateFormat": "dd/MM/yyyy", "timeFormat": "HH:mm"},
    "email": {"enabled": False, "smtpHost": "", "smtpPort": 587, "username": "", "password": "", "encryption": "starttls", "timeoutSeconds": 10},
    "telegram": {"enabled": False, "botToken": "", "connectionMode": "bot_api", "messageLanguage": "en", "includeOrganization": True, "destinations": []},
    "security": {"sessionTimeoutMinutes": 480, "maxLoginAttempts": 5, "accountLockMinutes": 15, "passwordExpiryDays": 0, "requirePasswordChange": False, "auditRetentionDays": 365, "frontendOnly": False},
    "system": {"maintenanceMode": False, "readOnlyMode": False, "paginationDefault": 20, "configurationVersion": "1.0.0", "environment": "development", "cacheStatus": "healthy", "backgroundJobStatus": "idle"},
    "display": {"cardFields": {}, "cardFooterAlign": {}},
}


def merge_setting(current: dict, incoming: dict) -> dict:
    """Deep-merge settings while preserving masked secrets."""
    cleaned = {k: v for k, v in incoming.items() if k != "updatedAt"}
    merged = deep_merge(current, cleaned)
    for key, value in cleaned.items():
        if not isinstance(value, dict) or not isinstance(current.get(key), dict):
            continue
        prior = current[key]
        nested = merged[key]
        if nested.get("password") in {"", MASK}:
            nested["password"] = prior.get("password")
        if nested.get("botToken") in {"", MASK}:
            nested["botToken"] = prior.get("botToken")
    return merged


async def get_setting(db: AsyncSession, key: str, default: dict) -> dict:
    row = await db.get(AppSetting, key)
    if not row:
        row = AppSetting(key=key, value=protect_mapping(default))
        db.add(row)
        await db.flush()
        await db.refresh(row)
    value = mask_mapping(dict(row.value))
    value["updatedAt"] = iso_utc(row.updated_at)
    return {"data": value}


async def update_app_config(db: AsyncSession, body: dict) -> dict:
    row = await db.get(AppSetting, "app-config") or AppSetting(key="app-config", value=protect_mapping(DEFAULT_APP_CONFIG))
    current = reveal_mapping(row.value or DEFAULT_APP_CONFIG)
    row.value = protect_mapping(merge_setting(current, body))
    row.updated_at = datetime.now(timezone.utc)
    db.add(row)
    await db.flush()
    from app.modules.admin_config.services.runtime import invalidate_app_config_cache

    await invalidate_app_config_cache()
    return await get_setting(db, "app-config", DEFAULT_APP_CONFIG)


async def record_telegram_destinations(
    db: AsyncSession,
    *,
    verified_chat_ids: list[str] | None = None,
) -> dict:
    """Persist Telegram destination verification on the live app-config row.

    When a test message succeeds, matching destinations are marked verified so
    meeting reminders can be delivered to them.
    """
    row = await db.get(AppSetting, "app-config") or AppSetting(key="app-config", value=protect_mapping(DEFAULT_APP_CONFIG))
    current = reveal_mapping(row.value or DEFAULT_APP_CONFIG)
    telegram = dict(current.get("telegram") or {})
    tested_at = iso_utc(datetime.now(timezone.utc))
    if verified_chat_ids:
        verified = {str(chat_id) for chat_id in verified_chat_ids}
        telegram["destinations"] = [
            {**dest, "verified": True, "status": "connected", "lastTestedAt": tested_at}
            if str(dest.get("chatId")) in verified
            else dest
            for dest in (telegram.get("destinations") or [])
        ]
    current["telegram"] = telegram
    row.value = protect_mapping(current)
    row.updated_at = datetime.now(timezone.utc)
    db.add(row)
    await db.flush()
    from app.modules.admin_config.services.runtime import invalidate_app_config_cache

    await invalidate_app_config_cache()
    return await get_setting(db, "app-config", DEFAULT_APP_CONFIG)
