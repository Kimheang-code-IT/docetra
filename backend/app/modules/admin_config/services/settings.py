from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.datetime import iso_utc
from app.core.secrets import MASK, mask_mapping, protect_mapping, reveal_mapping
from app.db import AppSetting
from app.shared.dicts import deep_merge

DEFAULT_APP_INFO = {
    "applicationName": "Docetra",
    "shortName": "Docetra",
    "organizationName": "General Department of Corporate Services",
    "description": "Document and record management system",
    "supportEmail": "support@example.com",
    "branding": {"primaryColor": "#e8472a", "secondaryColor": "#3a539f"},
    "footer": {"copyrightText": "© Docetra"},
}
DEFAULT_APP_CONFIG = {
    "general": {"defaultLandingPage": "/", "defaultPageSize": 20, "defaultRecordView": "table", "enableComments": True, "enableSharing": True, "enableExport": True, "maxUploadSizeMb": 25},
    "localization": {"defaultLanguage": "en", "availableLanguages": ["en", "km"], "timezone": "Asia/Phnom_Penh", "dateFormat": "dd/MM/yyyy", "timeFormat": "HH:mm", "firstDayOfWeek": 1, "numberFormat": "en-US", "currency": "KHR", "locale": "en"},
    "email": {"enabled": False, "smtpHost": "", "smtpPort": 587, "username": "", "password": "", "encryption": "starttls", "fromName": "Docetra", "fromEmail": "", "timeoutSeconds": 10, "connectionStatus": "not_tested"},
    "telegram": {"enabled": False, "botDisplayName": "Docetra", "botToken": "", "connectionMode": "bot_api", "messageLanguage": "en", "includeRecordLink": True, "includeOrganization": True, "includeAssignedOfficer": True, "connectionStatus": "not_tested", "destinations": [], "messageTemplate": "[{{record_type}}] {{record_number}}\n{{record_title}}"},
    "notifications": {
        "inAppEnabled": True,
        "emailEnabled": False,
        "telegramEnabled": False,
        "deliveryRetries": 3,
        "quietHoursEnabled": False,
        "language": "en",
        "rules": [],
        "meetingReminderOffsetsMinutes": [1440, 60, 15],
        "meetingRecurrenceHorizonDays": 90,
    },
    "security": {"sessionTimeoutMinutes": 480, "maxLoginAttempts": 5, "accountLockMinutes": 15, "passwordExpiryDays": 0, "requirePasswordChange": False, "allowedUploadExtensions": ["pdf", "doc", "docx", "xls", "xlsx", "png", "jpg", "jpeg"], "auditRetentionDays": 365, "frontendOnly": False},
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
        await db.commit()
        await db.refresh(row)
    value = mask_mapping(dict(row.value))
    value["updatedAt"] = iso_utc(row.updated_at)
    return {"data": value}


async def update_app_info(db: AsyncSession, body: dict) -> dict:
    row = await db.get(AppSetting, "app-info") or AppSetting(key="app-info", value=DEFAULT_APP_INFO)
    row.value = merge_setting(row.value or DEFAULT_APP_INFO, body)
    row.updated_at = datetime.now(timezone.utc)
    db.add(row)
    await db.commit()
    return await get_setting(db, "app-info", DEFAULT_APP_INFO)


async def reset_app_info(db: AsyncSession) -> dict:
    row = await db.get(AppSetting, "app-info") or AppSetting(key="app-info", value={})
    row.value = DEFAULT_APP_INFO
    row.updated_at = datetime.now(timezone.utc)
    db.add(row)
    await db.commit()
    return await get_setting(db, "app-info", DEFAULT_APP_INFO)


async def update_app_config(db: AsyncSession, body: dict) -> dict:
    row = await db.get(AppSetting, "app-config") or AppSetting(key="app-config", value=protect_mapping(DEFAULT_APP_CONFIG))
    current = reveal_mapping(row.value or DEFAULT_APP_CONFIG)
    row.value = protect_mapping(merge_setting(current, body))
    row.updated_at = datetime.now(timezone.utc)
    db.add(row)
    await db.commit()
    from app.modules.admin_config.services.runtime import invalidate_app_config_cache

    await invalidate_app_config_cache()
    return await get_setting(db, "app-config", DEFAULT_APP_CONFIG)
