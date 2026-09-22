import logging

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v2.deps import current_user, get_db
from app.core.authorization import require_permission
from app.core.config import settings
from app.core.http_schemas import AppSettingsBody, DataEnvelope, TelegramTestBody
from app.core.security import now_iso
from app.modules.admin_config.model import AppSetting
from typing import Any as User
from app.core.secrets import reveal_mapping
import app.modules.admin_config.services.settings as admin_settings

log = logging.getLogger(__name__)

router = APIRouter(prefix="/settings", tags=["settings"])


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
async def email_test_connection(db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    require_permission(user, "settings.app_config.configure")
    from app.integrations.email import send_test_email

    saved = await db.get(AppSetting, "app-config")
    config = reveal_mapping((saved.value if saved else {}) or {})
    email_cfg = config.get("email") or {}
    to_addr = str(settings.email_from_address or user.email)
    result = await send_test_email(to_addr, smtp=email_cfg)
    return {"data": {**result, "testedAt": now_iso()}}


def _telegram_config(config: dict) -> dict:
    from app.modules.admin_config.service import runtime

    return runtime.telegram_meeting(config)


@router.post("/app-config/telegram/test-connection", response_model=DataEnvelope)
async def telegram_test_connection(db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    require_permission(user, "settings.app_config.configure")
    from app.integrations.telegram import test_bot

    saved = await db.get(AppSetting, "app-config")
    config = reveal_mapping((saved.value if saved else {}) or {})
    result = await test_bot("meeting", config=config.get("telegram") or {})
    return {"data": {**result, "testedAt": now_iso()}}


@router.post("/app-config/telegram/send-test", response_model=DataEnvelope)
async def telegram_send_test(body: TelegramTestBody, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    require_permission(user, "settings.app_config.configure")
    from app.integrations.telegram import send_message

    saved = await db.get(AppSetting, "app-config")
    config = reveal_mapping((saved.value if saved else {}) or {})
    bot = _telegram_config(config)
    token = bot["botToken"]
    if not bot["enabled"] or not token:
        return {"data": {"status": "disabled", "message": "Telegram bot is not configured or enabled", "testedAt": now_iso()}}

    destinations = bot["destinations"] or []
    targets: list[str] = []
    if body.chatId and str(body.chatId).strip():
        targets = [str(body.chatId).strip()]
    elif body.destinationId:
        match = next((d for d in destinations if str(d.get("id")) == str(body.destinationId)), None)
        if match and match.get("chatId"):
            targets = [str(match["chatId"])]
    else:
        targets = [str(d["chatId"]) for d in destinations if d.get("enabled", True) and d.get("chatId")]

    if not targets:
        return {"data": {"status": "failed", "message": "No Telegram chat ID configured", "testedAt": now_iso()}}

    text = (
        "🧪 <b>Docetra test notification</b>\n"
        "\n"
        "✅ Telegram delivery is working.\n"
        "\n"
        f"🕒 <i>{now_iso()}</i>"
    )
    sent: list[str] = []
    errors: list[str] = []
    for chat_id in targets:
        try:
            await send_message(token, chat_id, text)
            sent.append(chat_id)
        except Exception as exc:  # noqa: BLE001 - report a safe message per destination
            request = getattr(exc, "request", None)
            detail = str(request.url) if request is not None else ""
            errors.append(f"{chat_id}: {exc}" + (f" ({detail})" if detail else ""))

    status = "connected" if sent else "failed"
    message = f"Test message sent to {len(sent)} chat(s)" if sent else f"Failed to send test message: {errors[0] if errors else 'unknown error'}"
    await admin_settings.record_telegram_destinations(db, verified_chat_ids=sent)
    return {"data": {"status": status, "message": message, "sent": sent, "errors": errors, "testedAt": now_iso()}}


@router.post("/app-config/telegram/discover-chats", response_model=DataEnvelope)
async def telegram_discover_chats(db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    require_permission(user, "settings.app_config.configure")
    from app.integrations.telegram import discover_chat_ids, known_chats

    saved = await db.get(AppSetting, "app-config")
    config = reveal_mapping((saved.value if saved else {}) or {})
    bot = _telegram_config(config)
    token = bot["botToken"]
    if not bot["enabled"] or not token:
        return {"data": {"status": "disabled", "message": "Telegram bot is not configured or enabled", "chats": []}}
    try:
        chats = await known_chats()
        if not chats:
            chats = await discover_chat_ids(token)
    except Exception as exc:  # noqa: BLE001 - return a UI-safe error
        log.warning("Telegram discover chats failed: %s", exc)
        return {"data": {"status": "failed", "message": "Could not read recent chats from Telegram", "chats": []}}
    return {"data": {"status": "connected", "message": f"{len(chats)} chat(s) found", "chats": chats}}
