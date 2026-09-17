import json
import logging
from typing import Any

import httpx
from app.core.config import settings

log = logging.getLogger(__name__)

_API_BASE = "https://api.telegram.org/bot{token}/{method}"
_KNOWN_CHATS_KEY = "telegram:known-chats"


class TelegramAPIError(RuntimeError):
    """Telegram rejected the request or was unreachable."""


def _url(token: str, method: str) -> str:
    return _API_BASE.format(token=token, method=method)


async def _request(
    method: str,
    token: str,
    *,
    payload: dict | None = None,
    params: dict | None = None,
    attempts: int = 2,
    timeout: float = 20,
) -> dict:
    """Call a Bot API method with one retry for transient network failures.

    ``method`` is the Telegram method name (e.g. ``sendMessage``); the HTTP verb
    is POST when a JSON payload is present, otherwise GET.
    """
    url = _url(token, method)
    http_method = "POST" if payload is not None else "GET"
    last_exc: Exception | None = None
    for attempt in range(attempts):
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                if http_method == "GET":
                    response = await client.get(url, params=params)
                else:
                    response = await client.post(url, json=payload)
            if response.status_code >= 400:
                detail = ""
                try:
                    detail = str((response.json() or {}).get("description") or "").strip()
                except Exception:  # noqa: BLE001 - error body may not be JSON
                    detail = ""
                raise TelegramAPIError(f"HTTP {response.status_code}: {detail or 'request rejected'}")
            return response.json()
        except TelegramAPIError:
            raise
        except Exception as exc:  # noqa: BLE001 - network/timeout; retry once
            last_exc = exc
            if attempt + 1 >= attempts:
                break
    name = type(last_exc).__name__ if last_exc else "unknown"
    raise TelegramAPIError(f"Could not reach Telegram ({name})") from last_exc


async def get_me(token: str) -> dict:
    return await _request("getMe", token)


async def get_updates(token: str, *, offset: int | None = None, timeout: int = 25) -> list[dict]:
    params: dict[str, Any] = {"timeout": timeout, "allowed_updates": '["message"]'}
    if offset is not None:
        params["offset"] = offset
    data = await _request("getUpdates", token, params=params, timeout=timeout + 10)
    return list(data.get("result") or [])


async def send_message(
    token: str,
    chat_id: str | int,
    text: str,
    *,
    reply_markup: dict | None = None,
    parse_mode: str | None = "HTML",
    disable_notification: bool = False,
) -> dict:
    payload: dict[str, Any] = {"chat_id": chat_id, "text": text}
    if parse_mode:
        payload["parse_mode"] = parse_mode
    if reply_markup:
        payload["reply_markup"] = reply_markup
    if disable_notification:
        payload["disable_notification"] = True
    return await _request("sendMessage", token, payload=payload)


async def discover_chat_ids(token: str) -> list[dict[str, Any]]:
    """Return chats that recently messaged the bot (via getUpdates).

    Used as a fallback when the polling bot has not recorded a chat yet.
    """
    data = await _request("getUpdates", token, params={"limit": 100, "allowed_updates": '["message","channel_post","edited_message","my_chat_member"]'})
    return _chats_from_updates(data.get("result") or [])


def _chats_from_updates(updates: list) -> list[dict[str, Any]]:
    seen: dict[str, dict[str, Any]] = {}
    for update in updates:
        if not isinstance(update, dict):
            continue
        container = update.get("message") or update.get("channel_post") or update.get("edited_message")
        chat = (container or {}).get("chat") if isinstance(container, dict) else None
        if not isinstance(chat, dict) or chat.get("id") is None:
            continue
        chat_id = str(chat["id"])
        title = chat.get("title") or " ".join(filter(None, [chat.get("first_name"), chat.get("last_name")])) or chat.get("username") or chat_id
        seen[chat_id] = {
            "chatId": chat_id,
            "title": title,
            "type": str(chat.get("type") or "chat"),
            "username": str(chat.get("username") or ""),
        }
    return list(seen.values())


def chat_from_update(update: dict) -> dict[str, Any] | None:
    """Normalize the chat of a message/callback update, if present."""
    container = update.get("message") or update.get("edited_message") or update.get("channel_post")
    if not isinstance(container, dict):
        callback = update.get("callback_query")
        container = (callback or {}).get("message") if isinstance(callback, dict) else None
    chat = (container or {}).get("chat") if isinstance(container, dict) else None
    if not isinstance(chat, dict) or chat.get("id") is None:
        return None
    chat_id = str(chat["id"])
    title = chat.get("title") or " ".join(filter(None, [chat.get("first_name"), chat.get("last_name")])) or chat.get("username") or chat_id
    return {
        "chatId": chat_id,
        "title": title,
        "type": str(chat.get("type") or "chat"),
        "username": str(chat.get("username") or ""),
    }


async def remember_chat(chat: dict[str, Any]) -> None:
    """Track chats the bot has seen so discovery still works while polling."""
    try:
        from app.core.security import redis

        await redis.hset(_KNOWN_CHATS_KEY, str(chat["chatId"]), json.dumps(chat))
    except Exception:  # noqa: BLE001 - redis is best-effort here
        log.debug("Could not persist known Telegram chat", exc_info=True)


async def known_chats() -> list[dict[str, Any]]:
    try:
        from app.core.security import redis

        raw = await redis.hgetall(_KNOWN_CHATS_KEY)
    except Exception:  # noqa: BLE001 - fall back to live getUpdates
        return []
    chats = []
    for value in (raw or {}).values():
        try:
            chats.append(json.loads(value))
        except (TypeError, ValueError):
            continue
    return chats


async def _send(token: str, chat_id: str, text: str) -> dict:
    return await send_message(token, chat_id, text)


async def send_meeting_alert(chat_id: str, text: str, *, bot: dict) -> dict:
    if not bot.get("enabled") or not bot.get("botToken"):
        log.info("Meeting Telegram bot disabled")
        return {"ok": False, "skipped": True}
    return await _send(bot["botToken"], chat_id, text)


def _resolve_bot(kind: str, config: dict | None) -> tuple[str, bool]:
    config = config or {}
    if kind != "meeting":
        token = str(config.get("botToken") or settings.telegram_devops_bot_token or "")
        enabled = bool(config.get("enabled", settings.telegram_devops_bot_enabled))
    else:
        token = str(config.get("botToken") or settings.telegram_meeting_bot_token or "")
        enabled = bool(config.get("enabled", settings.telegram_meeting_bot_enabled))
    return token, enabled


async def test_bot(kind: str = "meeting", *, config: dict | None = None) -> dict:
    """Validate the bot token via getMe. Never raises for network/API errors."""
    token, enabled = _resolve_bot(kind, config)
    if not enabled or not token:
        return {"status": "disabled", "message": "Telegram bot is not configured or enabled"}
    try:
        data = await get_me(token)
    except TelegramAPIError as exc:
        log.warning("Telegram getMe failed: %s", exc)
        return {"status": "failed", "message": f"Telegram bot check failed: {exc}"}
    result = data.get("result") or {}
    username = str(result.get("username") or "")
    return {
        "status": "connected",
        "message": f"Connected to @{username}" if username else "Telegram bot reachable",
        "bot": {
            "id": result.get("id"),
            "username": username,
            "name": str(result.get("first_name") or result.get("name") or ""),
        },
    }
