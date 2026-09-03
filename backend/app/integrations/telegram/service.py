import logging

import httpx
from app.core.config import settings

log = logging.getLogger(__name__)


async def _send(token: str, chat_id: str, text: str) -> dict:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.post(url, json={"chat_id": chat_id, "text": text})
        response.raise_for_status()
        return response.json()


async def send_meeting_alert(chat_id: str, text: str, *, bot: dict) -> dict:
    if not bot["enabled"] or not bot["botToken"]:
        log.info("Meeting Telegram bot disabled")
        return {"ok": False, "skipped": True}
    return await _send(bot["botToken"], chat_id, text)


async def test_bot(kind: str = "meeting", *, config: dict | None = None) -> dict:
    if kind != "meeting":
        token = str((config or {}).get("botToken") or settings.telegram_devops_bot_token)
        enabled = bool((config or {}).get("enabled", settings.telegram_devops_bot_enabled))
    elif config is not None:
        token = str(config.get("botToken") or settings.telegram_meeting_bot_token or "")
        enabled = bool(config.get("enabled", settings.telegram_meeting_bot_enabled))
    else:
        token = settings.telegram_meeting_bot_token or ""
        enabled = settings.telegram_meeting_bot_enabled
    if not enabled or not token:
        return {"status": "disabled", "message": "Telegram bot is not configured or enabled"}
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.get(f"https://api.telegram.org/bot{token}/getMe")
        response.raise_for_status()
    return {"status": "connected", "message": "Telegram bot reachable"}
