"""Telegram bot: period math, custom date range, keyboards, summaries."""

from datetime import datetime, timezone

from app.jobs import telegram_bot as bot
from app.modules.organization.model import Organization
from app.modules.people_access.model import Officer
from app.modules.record.model import Record


def _meeting(title: str = "Weekly Sync", **kwargs) -> Record:
    return Record(title=title, **kwargs)


# --- period math ------------------------------------------------------------
def test_period_bounds_today():
    now = datetime(2026, 9, 17, 14, 30, tzinfo=timezone.utc)
    start, end = bot.period_bounds("today", now)
    assert start == datetime(2026, 9, 17, 0, 0, tzinfo=timezone.utc)
    assert end == datetime(2026, 9, 18, 0, 0, tzinfo=timezone.utc)


def test_period_bounds_week_starts_monday():
    now = datetime(2026, 9, 17, 14, 30, tzinfo=timezone.utc)  # Thursday
    start, end = bot.period_bounds("week", now)
    assert start == datetime(2026, 9, 14, 0, 0, tzinfo=timezone.utc)
    assert end == datetime(2026, 9, 21, 0, 0, tzinfo=timezone.utc)


def test_period_bounds_month_and_all():
    now = datetime(2026, 9, 17, 14, 30, tzinfo=timezone.utc)
    assert bot.period_bounds("month", now) == (
        datetime(2026, 9, 1, 0, 0, tzinfo=timezone.utc),
        datetime(2026, 10, 1, 0, 0, tzinfo=timezone.utc),
    )
    assert bot.period_bounds("all") == (None, None)


# --- custom date range ------------------------------------------------------
def test_parse_date_range_dd_mm_yyyy():
    start, end = bot.parse_date_range("01/09/2026 17/09/2026")
    assert start == datetime(2026, 9, 1, tzinfo=timezone.utc)
    assert end == datetime(2026, 9, 18, tzinfo=timezone.utc)  # end day inclusive


def test_parse_date_range_iso_and_reversed_order():
    start, end = bot.parse_date_range("2026-09-17 2026-09-01")
    assert start == datetime(2026, 9, 1, tzinfo=timezone.utc)
    assert end == datetime(2026, 9, 18, tzinfo=timezone.utc)


def test_parse_date_range_invalid():
    assert bot.parse_date_range("hello") is None
    assert bot.parse_date_range("01/09/2026") is None
    assert bot.parse_date_range("32/13/2026 01/01/2026") is None


# --- keyboards + routing ----------------------------------------------------
def test_keyboards():
    main = {b["text"] for row in bot.main_keyboard()["keyboard"] for b in row}
    assert {bot.MEETINGS, bot.DOCUMENTS, bot.DEPARTMENTS, bot.OFFICERS, bot.HELP} == main
    period_rows = bot.period_keyboard()["keyboard"]
    periods = {b["text"] for row in period_rows for b in row}
    assert {bot.TODAY, bot.WEEK, bot.MONTH, bot.ALL, bot.CUSTOM, bot.BACK} == periods
    # Custom range and Back share the same line.
    assert [b["text"] for b in period_rows[-1]] == [bot.CUSTOM, bot.BACK]
    types = {b["text"] for row in bot.doctype_keyboard()["keyboard"] for b in row}
    assert {bot.INCOMING, bot.OUTGOING, bot.MASTER_LIST, bot.ALL_DOCS, bot.BACK} == types


def test_route_text_sections_and_periods():
    assert bot.route_text("/start", None) == ("welcome", None)
    assert bot.route_text(bot.MEETINGS, None) == ("flow", "meetings")
    assert bot.route_text(bot.DOCUMENTS, None) == ("flow", "documents")
    assert bot.route_text(bot.DEPARTMENTS, None) == ("departments", None)
    assert bot.route_text(bot.OFFICERS, None) == ("officers", None)
    assert bot.route_text(bot.HELP, None) == ("help", None)
    assert bot.route_text(bot.INCOMING, {"flow": "documents"}) == ("doctype", "incoming_document")
    assert bot.route_text(bot.MONTH, {"flow": "meetings"}) == ("result_meetings", "month")
    assert bot.route_text(bot.WEEK, {"flow": "documents", "doctype": "incoming_document"}) == (
        "result_docs", "incoming_document:week",
    )


def test_route_text_custom_range_flow():
    assert bot.route_text(bot.CUSTOM, {"flow": "meetings"}) == ("await_range", None)
    action, payload = bot.route_text("01/09/2026 17/09/2026", {"flow": "meetings", "awaiting": "range"})
    assert action == "result_range"
    assert payload == "meetings|all|2026-09-01T00:00:00+00:00|2026-09-18T00:00:00+00:00"
    assert bot.route_text("nope", {"flow": "meetings", "awaiting": "range"}) == ("range_invalid", None)


def test_route_text_escape_from_range_state():
    # Known buttons still work while waiting for dates.
    assert bot.route_text(bot.BACK, {"flow": "meetings", "awaiting": "range"}) == ("welcome", None)
    assert bot.route_text(bot.MEETINGS, {"flow": "meetings", "awaiting": "range"}) == ("flow", "meetings")


# --- rendering --------------------------------------------------------------
def test_render_meetings_formats_and_escapes():
    rows = [_meeting("Weekly <Sync>", record_time=datetime(2026, 9, 10, 9, 0, tzinfo=timezone.utc), stage="intake")]
    text = bot.render_meetings(rows, "This Month", "01/09/2026 – 30/09/2026", 5)
    assert "📅" in text and "📊" in text
    assert "Weekly &lt;Sync&gt;" in text
    assert "🕒 10/09/2026 09:00" in text
    assert "🏷️ intake" in text
    assert "showing 1 of 5" in text


def test_render_documents_lists_type_counts():
    counts = {"incoming_document": 4, "outgoing_document": 2, "document": 5}
    recent = [_meeting("Budget 2026", record_type_code="incoming_document")]
    text = bot.render_documents(counts, "This Week", "14/09/2026 – 20/09/2026", 11, recent)
    assert "📥 Incoming: <b>4</b>" in text
    assert "📤 Outgoing: <b>2</b>" in text
    assert "📋 Master list: <b>0</b>" in text
    assert "📊 Total: <b>11</b>" in text
    assert "Budget 2026" in text


def test_render_document_type_filters_to_type():
    recent = [_meeting("Invoice 12", record_type_code="incoming_document")]
    text = bot.render_document_type("incoming_document", "Custom range", "01/09/2026 – 17/09/2026", 1, recent)
    assert "📥" in text and "Incoming" in text
    assert "📊 Total: <b>1</b>" in text
    assert "Invoice 12" in text


def test_render_departments_and_officers():
    assert "Ministry A" in bot.render_departments([Organization(nam="Ministry A")], 3)
    assert "Dara" in bot.render_officers([Officer(nam="Dara")], 1)


def test_timestamp_footer_has_utc_time():
    footer = bot.timestamp_footer(datetime(2026, 9, 17, 15, 30, tzinfo=timezone.utc))
    assert "17/09/2026 15:30 UTC" in footer


# --- authorization ----------------------------------------------------------
def test_is_allowed_uses_env_and_destinations(monkeypatch):
    monkeypatch.setattr(bot.settings, "telegram_meeting_allowed_chat_ids", ["111"])
    config = {"telegram": {"destinations": [{"chatId": "222", "enabled": True}]}}
    assert bot.is_allowed(111, config) is True
    assert bot.is_allowed("222", config) is True
    assert bot.is_allowed(999, config) is False


def test_is_allowed_false_when_nothing_configured(monkeypatch):
    monkeypatch.setattr(bot.settings, "telegram_meeting_allowed_chat_ids", [])
    assert bot.is_allowed(1, {"telegram": {"destinations": []}}) is False
