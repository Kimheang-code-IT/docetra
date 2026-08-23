from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v2.deps import current_user, get_db
from app.core.authorization import require_permission
from app.core.config import settings
from app.core.http_schemas import AppSettingsBody, DataEnvelope
from app.core.security import now_iso
from app.db import AppSetting, User
from app.core.secrets import reveal_mapping
import app.modules.admin_config.services.settings as admin_settings

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/app-info", response_model=DataEnvelope)
async def app_info(db: AsyncSession = Depends(get_db)):
    """Public read — branding on login; secrets are not stored in app-info."""
    return await admin_settings.get_setting(db, "app-info", admin_settings.DEFAULT_APP_INFO)


@router.patch("/app-info", response_model=DataEnvelope)
@router.put("/app-info", response_model=DataEnvelope)
async def update_app_info(body: AppSettingsBody, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    require_permission(user, "settings.app_info.edit")
    return await admin_settings.update_app_info(db, body.model_dump(exclude_unset=True))


@router.post("/app-info/reset", response_model=DataEnvelope)
async def reset_app_info(db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    require_permission(user, "settings.app_info.configure")
    return await admin_settings.reset_app_info(db)


@router.get("/app-config", response_model=DataEnvelope)
async def app_config(db: AsyncSession = Depends(get_db)):
    """Public read — localization/branding defaults; secrets remain masked."""
    return await admin_settings.get_setting(db, "app-config", admin_settings.DEFAULT_APP_CONFIG)


@router.patch("/app-config", response_model=DataEnvelope)
async def update_app_config(body: AppSettingsBody, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    require_permission(user, "settings.app_config.edit")
    return await admin_settings.update_app_config(db, body.model_dump(exclude_unset=True))


@router.post("/app-config/email/test-connection", response_model=DataEnvelope)
@router.post("/app-config/email/send-test", response_model=DataEnvelope)
@router.post("/app-config/telegram/test-connection", response_model=DataEnvelope)
@router.post("/app-config/telegram/send-test", response_model=DataEnvelope)
async def test_connection(request: Request, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    require_permission(user, "settings.app_config.configure")
    path = request.url.path
    saved = await db.get(AppSetting, "app-config")
    config = reveal_mapping((saved.value if saved else {}) or {})
    if "email" in path:
        from app.integrations.email import send_test_email

        email_cfg = config.get("email") or {}
        to_addr = str(email_cfg.get("fromEmail") or settings.email_from_address or user.email)
        result = await send_test_email(to_addr, smtp=email_cfg, db=db)
        return {"data": {**result, "testedAt": now_iso()}}
    if "telegram" in path:
        from app.integrations.telegram import test_bot

        result = await test_bot("meeting", config=config.get("telegram") or {}, db=db)
        return {"data": {**result, "testedAt": now_iso()}}
    return {"data": {"status": "connected", "message": "Configuration accepted", "testedAt": now_iso()}}
