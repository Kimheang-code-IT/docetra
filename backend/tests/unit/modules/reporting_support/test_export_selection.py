from datetime import datetime, timezone

from app.modules.reporting_support.services.export import date_bounds, select_fields


def test_date_bounds_parses_bare_dates_with_end_of_day():
    start, end = date_bounds({"startDate": "2026-08-01", "endDate": "2026-08-15"})
    assert start == datetime(2026, 8, 1, 0, 0, tzinfo=timezone.utc)
    assert end == datetime(2026, 8, 15, 23, 59, 59, tzinfo=timezone.utc)


def test_date_bounds_missing_or_invalid_returns_none():
    assert date_bounds({}) == (None, None)
    start, end = date_bounds({"startDate": "not-a-date", "endDate": ""})
    assert start is None and end is None


def test_select_fields_honors_codes_and_strips_secrets():
    fields = select_fields(["title", "password", "token", "recordTime"], [{"id": "1", "title": "T"}])
    assert fields == ["id", "title", "recordTime"]


def test_select_fields_falls_back_to_union_of_rows():
    rows = [{"id": "1", "title": "T", "secret": "x"}, {"status": "active"}]
    assert select_fields([], rows) == ["id", "status", "title"]


def test_select_fields_always_puts_id_first_and_deduplicates():
    assert select_fields(["status", "id"], [{"id": "1"}]) == ["id", "status"]
