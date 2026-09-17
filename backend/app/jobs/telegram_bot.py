"""Interactive Telegram bot: stepped reply-keyboard menu + period filters.

Runs as a dedicated long-polling process/container (``python -m app.main
telegram``) so bot traffic never competes with worker jobs.

Flow (all on the Telegram reply keyboard):
  Main  →  📅 Meetings / 📄 Documents / 🏢 Departments / 👤 Officers
  Meetings   →  period (or custom date range)  →  result
  Documents  →  type → period (or custom range) →  result
  Departments / Officers  →  result

Only **private** chats get interactive replies (per-user messages); a group is
broadcast-only (meeting alerts pushed by the worker). Telegram only changes the
reply keyboard via a real message, so each step posts a short quiet label that
carries the next keyboard.

Telegram HTTP/envelope helpers live in ``app.integrations.telegram``; this
module owns the data queries and is allowed to import business models.
"""

from __future__ import annotations

import asyncio
import html
import json
import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func, select

from app.core.config import settings
from app.db import SessionLocal
from app.integrations.telegram import (
    chat_from_update,
    get_updates,
    remember_chat,
    send_message,
)
from app.modules.admin_config.service import runtime
from app.modules.organization.model import Organization
from app.modules.people_access.model import Officer
from app.modules.record.model import Record

log = logging.getLogger(__name__)

DOCUMENT_TYPES: list[tuple[str, str, str]] = [
    ("incoming_document", "📥", "Incoming"),
    ("outgoing_document", "📤", "Outgoing"),
    ("document", "📄", "Documents"),
    ("master_list_request", "📋", "Master list"),
]
DOCUMENT_TYPE_META = {code: (emoji, name) for code, emoji, name in DOCUMENT_TYPES}

# Reply-keyboard labels (tapping one sends this text to the bot).
MEETINGS = "📅 Meetings"
DOCUMENTS = "📄 Documents"
DEPARTMENTS = "🏢 Departments"
OFFICERS = "👤 Officers"
HELP = "ℹ️ Help"
BACK = "⬅️ Back"
TODAY = "📆 Today"
WEEK = "🗓️ This Week"
MONTH = "📅 This Month"
ALL = "♾️ All Time"
CUSTOM = "📅 Custom range"
INCOMING = "📥 Incoming"
OUTGOING = "📤 Outgoing"
MASTER_LIST = "📋 Master list"
ALL_DOCS = "📄 All documents"

PERIOD_BY_TEXT = {TODAY: "today", WEEK: "week", MONTH: "month", ALL: "all"}
DOC_TYPE_BY_TEXT = {
    INCOMING: "incoming_document",
    OUTGOING: "outgoing_document",
    MASTER_LIST: "master_list_request",
    ALL_DOCS: "all",
}
DOC_TYPE_LABEL = {code: label for label, code in DOC_TYPE_BY_TEXT.items()}
PERIOD_LABELS = {"today": "Today", "week": "This Week", "month": "This Month", "all": "All Time"}

LIST_LIMIT = 12
_DATE_TOKEN = re.compile(r"(\d{1,4})[/\-.](\d{1,2})[/\-.](\d{1,4})")


# --------------------------------------------------------------------------- #
# Pure helpers (unit tested)
# --------------------------------------------------------------------------- #
def period_bounds(period: str, now: datetime | None = None) -> tuple[datetime | None, datetime | None]:
    """UTC [start, end) bounds for a period key; ``None`` bounds mean all time."""
    now = now or datetime.now(timezone.utc)
    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    if period == "today":
        return midnight, midnight + timedelta(days=1)
    if period == "week":
        start = midnight - timedelta(days=now.weekday())
        return start, start + timedelta(days=7)
    if period == "month":
        start = midnight.replace(day=1)
        end = (start.replace(day=28) + timedelta(days=4)).replace(day=1)
        return start, end
    return None, None


def period_range_text(start: datetime | None, end: datetime | None) -> str:
    if not start or not end:
        return "All recorded data"
    return f"{start:%d/%m/%Y} – {(end - timedelta(days=1)):%d/%m/%Y}"


def _parse_date_token(groups: tuple[str, str, str]) -> datetime:
    first, second, third = groups
    if len(first) == 4:  # YYYY-MM-DD
        year, month, day = int(first), int(second), int(third)
    else:  # DD/MM/YYYY
        day, month, year = int(first), int(second), int(third)
    return datetime(year, month, day, tzinfo=timezone.utc)


def parse_date_range(raw: str) -> tuple[datetime, datetime] | None:
    """Parse ``start end`` dates (DD/MM/YYYY or YYYY-MM-DD) into a UTC
    [start, end+1day) window. Returns ``None`` when the input is not two dates."""
    matches = _DATE_TOKEN.findall(raw or "")
    if len(matches) < 2:
        return None
    parsed: list[datetime] = []
    for groups in matches[:2]:
        try:
            parsed.append(_parse_date_token(groups))
        except (ValueError, TypeError):
            return None
    start, end = min(parsed), max(parsed)
    return start, end + timedelta(days=1)


def _fmt_dt(value: datetime | None) -> str:
    if not value:
        return ""
    return value.astimezone(timezone.utc).strftime("%d/%m/%Y %H:%M")


def timestamp_footer(now: datetime | None = None) -> str:
    now = now or datetime.now(timezone.utc)
    return f"\n\n🕒 <i>{now:%d/%m/%Y %H:%M} UTC</i>"


def reply_keyboard(rows: list[list[str]], *, placeholder: str | None = None) -> dict[str, Any]:
    keyboard: dict[str, Any] = {
        "keyboard": [[{"text": label} for label in row] for row in rows],
        "resize_keyboard": True,
        "is_persistent": True,
    }
    if placeholder:
        keyboard["input_field_placeholder"] = placeholder
    return keyboard


def main_keyboard() -> dict[str, Any]:
    return reply_keyboard(
        [[MEETINGS, DOCUMENTS], [DEPARTMENTS, OFFICERS], [HELP]],
        placeholder="Choose a section…",
    )


def period_keyboard() -> dict[str, Any]:
    return reply_keyboard(
        [[TODAY, WEEK], [MONTH, ALL], [CUSTOM, BACK]],
        placeholder="Choose a period or custom range…",
    )


def doctype_keyboard() -> dict[str, Any]:
    return reply_keyboard(
        [[INCOMING, OUTGOING], [MASTER_LIST, ALL_DOCS], [BACK]],
        placeholder="Choose a document type…",
    )


def route_text(raw: str, state: dict | None) -> tuple[str, str | None]:
    """Map a keyboard tap / typed text to an action without touching the network."""
    state = state or {}
    text = (raw or "").strip()
    control_labels = {
        BACK, MEETINGS, DOCUMENTS, DEPARTMENTS, OFFICERS, HELP, CUSTOM,
        TODAY, WEEK, MONTH, ALL, INCOMING, OUTGOING, MASTER_LIST, ALL_DOCS,
    }
    # While waiting for a range, still honour other keyboard buttons (escape).
    if state.get("awaiting") == "range" and text not in control_labels and text not in {"/start", "/menu"}:
        parsed = parse_date_range(text)
        if not parsed:
            return "range_invalid", None
        start, end = parsed
        flow = state.get("flow") or "meetings"
        code = state.get("doctype") or "all"
        return "result_range", f"{flow}|{code}|{start.isoformat()}|{end.isoformat()}"
    if not text or text in {"/start", "/menu"}:
        return "welcome", None
    if text in {HELP, "/help"}:
        return "help", None
    if text == BACK:
        return "welcome", None
    if text == MEETINGS:
        return "flow", "meetings"
    if text == DOCUMENTS:
        return "flow", "documents"
    if text == DEPARTMENTS:
        return "departments", None
    if text == OFFICERS:
        return "officers", None
    if text == CUSTOM:
        return "await_range", None
    if text in DOC_TYPE_BY_TEXT:
        return "doctype", DOC_TYPE_BY_TEXT[text]
    period = PERIOD_BY_TEXT.get(text)
    if period:
        if state.get("flow") == "documents":
            return "result_docs", f"{state.get('doctype') or 'all'}:{period}"
        return "result_meetings", period
    return "welcome", None


def welcome_text() -> str:
    return "🏛️ <b>Docetra Assistant</b>"


def help_text() -> str:
    return (
        "ℹ️ <b>How to use</b>\n\n"
        "📅 <b>Meetings</b> → period (or custom range) → result\n"
        "📄 <b>Documents</b> → type → period → result\n"
        "🏢 <b>Departments</b> / 👤 <b>Officers</b> → instant result\n\n"
        "📅 <b>Custom range</b>: send two dates, e.g. <code>01/09/2026 17/09/2026</code>.\n"
        "Every result ends with the time it was generated."
    )


def range_prompt(topic: str) -> str:
    label = "Meetings" if topic == "meetings" else "Documents"
    return (
        f"📅 <b>{label} — custom range</b>\n\n"
        "Send start and end date:\n"
        "<code>DD/MM/YYYY DD/MM/YYYY</code>\n"
        "Example: <code>01/09/2026 17/09/2026</code>"
    )


def render_meetings(rows: list[Record], label: str, range_text: str, total: int) -> str:
    lines = [
        f"📅 <b>Meetings — {label}</b>",
        f"<i>{range_text}</i>",
        "",
        f"📊 Total: <b>{total}</b> meeting(s)",
        "",
    ]
    if not rows:
        lines.append("🫙 <i>No meetings in this period.</i>")
        return "\n".join(lines)
    for index, row in enumerate(rows, 1):
        lines.append(f"<b>{index}. {html.escape(row.title or 'Untitled')}</b>")
        meta = []
        when = _fmt_dt(row.record_time)
        if when:
            meta.append(f"🕒 {when}")
        if row.stage:
            meta.append(f"🏷️ {html.escape(str(row.stage))}")
        if meta:
            lines.append("   " + "   ·   ".join(meta))
        lines.append("")
    if total > len(rows):
        lines.append(f"<i>… showing {len(rows)} of {total}</i>")
    return "\n".join(lines).strip()


def render_documents(counts: dict[str, int], label: str, range_text: str, total: int, recent: list[Record]) -> str:
    lines = [
        f"📄 <b>Documents — {label}</b>",
        f"<i>{range_text}</i>",
        "",
        f"📊 Total: <b>{total}</b> document(s)",
        "",
    ]
    for code, emoji, name in DOCUMENT_TYPES:
        lines.append(f"{emoji} {name}: <b>{counts.get(code, 0)}</b>")
    if recent:
        lines += ["", "🆕 <b>Latest</b>"]
        for row in recent:
            emoji, _name = DOCUMENT_TYPE_META.get(str(row.record_type_code), ("📄", "Document"))
            lines.append(f"• {emoji} {html.escape(row.title or 'Untitled')}")
    if total == 0:
        lines += ["", "🫙 <i>No documents in this period.</i>"]
    return "\n".join(lines).strip()


def render_document_type(code: str, label: str, range_text: str, total: int, recent: list[Record]) -> str:
    emoji, name = DOCUMENT_TYPE_META.get(code, ("📄", "Document"))
    lines = [
        f"{emoji} <b>{name} — {label}</b>",
        f"<i>{range_text}</i>",
        "",
        f"📊 Total: <b>{total}</b>",
    ]
    if recent:
        lines += ["", "🆕 <b>Latest</b>"]
        for row in recent:
            lines.append(f"• {html.escape(row.title or 'Untitled')}")
    if total == 0:
        lines += ["", "🫙 <i>None in this period.</i>"]
    return "\n".join(lines).strip()


def render_departments(rows: list[Organization], total: int) -> str:
    lines = ["🏢 <b>Departments</b>", "", f"📊 Total: <b>{total}</b> active department(s)", ""]
    if not rows:
        lines.append("🫙 <i>No departments found.</i>")
    for index, row in enumerate(rows, 1):
        lines.append(f"{index}. {html.escape(row.nam or 'Untitled')}")
    if total > len(rows):
        lines += ["", f"<i>… showing {len(rows)} of {total}</i>"]
    return "\n".join(lines).strip()


def render_officers(rows: list[Officer], total: int) -> str:
    lines = ["👤 <b>Officers</b>", "", f"📊 Total: <b>{total}</b> active officer(s)", ""]
    if not rows:
        lines.append("🫙 <i>No officers found.</i>")
    for index, row in enumerate(rows, 1):
        lines.append(f"{index}. {html.escape(row.nam or 'Untitled')}")
    if total > len(rows):
        lines += ["", f"<i>… showing {len(rows)} of {total}</i>"]
    return "\n".join(lines).strip()


# --------------------------------------------------------------------------- #
# Data queries
# --------------------------------------------------------------------------- #
async def _meetings(start: datetime | None, end: datetime | None) -> tuple[list[Record], int]:
    conditions = [Record.record_type_code == "meeting_history", Record.lifecycle == "active"]
    if start and end:
        conditions += [Record.record_time >= start, Record.record_time < end]
    async with SessionLocal() as db:
        total = await db.scalar(select(func.count()).select_from(Record).where(*conditions))
        rows = (
            await db.scalars(
                select(Record).where(*conditions).order_by(Record.record_time.desc().nullslast()).limit(LIST_LIMIT)
            )
        ).all()
    return list(rows), int(total or 0)


async def _documents(
    start: datetime | None, end: datetime | None, code: str | None = None
) -> tuple[dict[str, int], int, list[Record]]:
    timestamp = func.coalesce(Record.record_time, Record.created_at)
    codes = [code] if code else [item for item, _e, _n in DOCUMENT_TYPES]
    conditions = [Record.record_type_code.in_(codes), Record.lifecycle == "active"]
    if start and end:
        conditions += [timestamp >= start, timestamp < end]
    async with SessionLocal() as db:
        grouped = (await db.execute(select(Record.record_type_code, func.count()).where(*conditions).group_by(Record.record_type_code))).all()
        recent = (await db.scalars(select(Record).where(*conditions).order_by(timestamp.desc()).limit(5))).all()
    counts = {str(row_code): int(count) for row_code, count in grouped}
    return counts, sum(counts.values()), list(recent)


async def _departments() -> tuple[list[Organization], int]:
    conditions = [Organization.organization_type == "government", Organization.is_active == 1]
    async with SessionLocal() as db:
        total = await db.scalar(select(func.count()).select_from(Organization).where(*conditions))
        rows = (await db.scalars(select(Organization).where(*conditions).order_by(Organization.nam).limit(20))).all()
    return list(rows), int(total or 0)


async def _officers() -> tuple[list[Officer], int]:
    conditions = [Officer.is_active == 1]
    async with SessionLocal() as db:
        total = await db.scalar(select(func.count()).select_from(Officer).where(*conditions))
        rows = (await db.scalars(select(Officer).where(*conditions).order_by(Officer.nam).limit(20))).all()
    return list(rows), int(total or 0)


# --------------------------------------------------------------------------- #
# Authorization + session state
# --------------------------------------------------------------------------- #
def allowed_chat_ids(config: dict) -> set[str]:
    allowed = {str(item) for item in (settings.telegram_meeting_allowed_chat_ids or [])}
    bot = runtime.telegram_meeting(config)
    for destination in bot.get("destinations") or []:
        if destination.get("chatId"):
            allowed.add(str(destination["chatId"]))
    return allowed


def is_allowed(chat_id: Any, config: dict) -> bool:
    allowed = allowed_chat_ids(config)
    return bool(allowed) and str(chat_id) in allowed


async def _redis():
    from app.core.security import redis

    return redis


async def _get_state(chat_id: Any) -> dict:
    try:
        redis = await _redis()
        raw = await redis.get(f"telegram:bot:state:{chat_id}")
        return json.loads(raw) if raw else {}
    except Exception:  # noqa: BLE001 - state is best-effort
        return {}


async def _set_state(chat_id: Any, state: dict) -> None:
    try:
        redis = await _redis()
        await redis.setex(f"telegram:bot:state:{chat_id}", 3600, json.dumps(state))
    except Exception:  # noqa: BLE001
        log.debug("Could not persist bot state", exc_info=True)


async def _clear_state(chat_id: Any) -> None:
    try:
        redis = await _redis()
        await redis.delete(f"telegram:bot:state:{chat_id}")
    except Exception:  # noqa: BLE001
        log.debug("Could not clear bot state", exc_info=True)


# --------------------------------------------------------------------------- #
# Handlers
# --------------------------------------------------------------------------- #
async def _step_keyboard(token: str, chat_id: int, label: str, keyboard: dict) -> None:
    """Show the next step's keyboard on a minimal label message (sent quietly)."""
    await send_message(token, chat_id, f"{label}{timestamp_footer()}", reply_markup=keyboard, disable_notification=True)


async def _result(token: str, chat_id: int, text: str) -> None:
    """Send a final result; the main keyboard rides along with it."""
    await send_message(token, chat_id, f"{text}{timestamp_footer()}", reply_markup=main_keyboard())


async def _handle_message(message: dict, token: str, config: dict) -> None:
    chat = message.get("chat") or {}
    chat_id = chat.get("id")
    if chat_id is None:
        return
    # Interactive menu is private-only: each user gets their own messages.
    # Groups are broadcast-only (meeting alerts) and never answered here.
    if str(chat.get("type") or "") != "private":
        return
    if not is_allowed(chat_id, config):
        await send_message(
            token,
            chat_id,
            f"⛔ <b>Not authorized</b>\nAsk an administrator to add this chat in Docetra settings.{timestamp_footer()}",
            reply_markup=main_keyboard(),
        )
        return

    state = await _get_state(chat_id)
    action, payload = route_text(str(message.get("text") or ""), state)

    if action == "help":
        await _clear_state(chat_id)
        await _result(token, chat_id, help_text())
        return
    if action == "flow" and payload:
        await _set_state(chat_id, {"flow": payload})
        if payload == "documents":
            await _step_keyboard(token, chat_id, DOCUMENTS, doctype_keyboard())
        else:
            await _step_keyboard(token, chat_id, MEETINGS, period_keyboard())
        return
    if action == "doctype" and payload:
        await _set_state(chat_id, {"flow": "documents", "doctype": payload})
        await _step_keyboard(token, chat_id, DOC_TYPE_LABEL.get(payload, DOCUMENTS), period_keyboard())
        return
    if action == "await_range":
        flow = state.get("flow") or "meetings"
        await _set_state(chat_id, {**state, "flow": flow, "awaiting": "range"})
        await _step_keyboard(token, chat_id, range_prompt(flow), period_keyboard())
        return
    if action == "range_invalid":
        await _step_keyboard(token, chat_id, "⚠️ Send two dates like <code>01/09/2026 17/09/2026</code>", period_keyboard())
        return
    if action == "result_meetings" and payload:
        start, end = period_bounds(payload)
        rows, total = await _meetings(start, end)
        await _clear_state(chat_id)
        await _result(token, chat_id, render_meetings(rows, PERIOD_LABELS.get(payload, payload), period_range_text(start, end), total))
        return
    if action == "result_docs" and payload:
        code, _, period = payload.partition(":")
        start, end = period_bounds(period)
        selected = None if code == "all" else code
        counts, total, recent = await _documents(start, end, selected)
        label = PERIOD_LABELS.get(period, period)
        range_text = period_range_text(start, end)
        text = render_documents(counts, label, range_text, total, recent) if selected is None else render_document_type(selected, label, range_text, total, recent)
        await _clear_state(chat_id)
        await _result(token, chat_id, text)
        return
    if action == "result_range" and payload:
        flow, _, remainder = payload.partition("|")
        code, _, dates = remainder.partition("|")
        start_iso, _, end_iso = dates.partition("|")
        try:
            start, end = datetime.fromisoformat(start_iso), datetime.fromisoformat(end_iso)
        except ValueError:
            await _clear_state(chat_id)
            await _result(token, chat_id, "⚠️ Could not read those dates. Please try again from the menu.")
            return
        range_text = period_range_text(start, end)
        if flow == "documents":
            selected = None if code == "all" else code
            counts, total, recent = await _documents(start, end, selected)
            text = (
                render_documents(counts, "Custom range", range_text, total, recent)
                if selected is None
                else render_document_type(selected, "Custom range", range_text, total, recent)
            )
        else:
            rows, total = await _meetings(start, end)
            text = render_meetings(rows, "Custom range", range_text, total)
        await _clear_state(chat_id)
        await _result(token, chat_id, text)
        return
    if action == "departments":
        await _clear_state(chat_id)
        rows, total = await _departments()
        await _result(token, chat_id, render_departments(rows, total))
        return
    if action == "officers":
        await _clear_state(chat_id)
        rows, total = await _officers()
        await _result(token, chat_id, render_officers(rows, total))
        return
    await _clear_state(chat_id)
    await _result(token, chat_id, welcome_text())


async def _handle_update(update: dict, token: str, config: dict) -> None:
    chat = chat_from_update(update)
    if chat:
        await remember_chat(chat)
    if update.get("message"):
        await _handle_message(update["message"], token, config)


async def _load_bot() -> tuple[dict, dict]:
    async with SessionLocal() as db:
        config = await runtime.load_app_config(db)
    return config, runtime.telegram_meeting(config)


async def run_telegram_bot() -> None:
    """Long-poll the Bot API and answer keyboard taps. Never raises out."""
    offset: int | None = None
    while True:
        try:
            config, bot = await _load_bot()
            token = str(bot.get("botToken") or "")
            if not bot.get("enabled") or not token:
                await asyncio.sleep(15)
                continue
            updates = await get_updates(token, offset=offset, timeout=25)
            for update in updates:
                try:
                    offset = int(update.get("update_id", 0)) + 1
                except (TypeError, ValueError):
                    continue
                await _handle_update(update, token, config)
        except asyncio.CancelledError:
            raise
        except Exception:  # noqa: BLE001 - keep the polling loop alive
            log.exception("Telegram bot loop error")
            await asyncio.sleep(5)
