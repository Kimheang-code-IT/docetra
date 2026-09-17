"""Meeting alert formatting — icon-led, HTML-escaped, spaced."""

from datetime import datetime, timezone
from types import SimpleNamespace

from app.jobs.consumers import _format_meeting_alert


def test_reminder_format_has_icons_and_escapes_user_text():
    meeting = SimpleNamespace(record_time=datetime(2026, 9, 17, 8, 30, tzinfo=timezone.utc), stage="intake")

    text = _format_meeting_alert(meeting, "Weekly <Sync>", "reminder", {"location": "Room <A>"})

    assert "🔔" in text and "Meeting Reminder" in text
    assert "Weekly &lt;Sync&gt;" in text
    assert "🕒 17/09/2026 08:30" in text
    assert "📍 Room &lt;A&gt;" in text
    assert "🏷️ intake" in text
    assert "🏛️" in text


def test_start_and_end_headers():
    meeting = SimpleNamespace(record_time=None, stage=None)
    assert "Meeting Starting" in _format_meeting_alert(meeting, "x", "start", {})
    assert "Meeting Ended" in _format_meeting_alert(meeting, "x", "end", {})
    assert "Meeting Update" in _format_meeting_alert(meeting, "x", "other", {})
