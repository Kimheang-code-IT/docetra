"""Shared pagination / id helpers (app.shared)."""

from app.shared import page_meta, parse_limit
from app.shared.dicts import deep_merge
from app.shared.filters import parse_list_query
from app.shared.responses import data_envelope, list_envelope
from app.shared.validators import is_email, nonempty, require_email
import pytest


def test_parse_limit_defaults():
    assert parse_limit(None) == 20
    assert parse_limit("all") == 100
    assert parse_limit("5") == 5
    assert parse_limit("999") == 100


def test_page_meta():
    meta = page_meta(1, 20, 45)
    assert meta["totalPages"] == 3
    assert meta["total"] == 45


def test_deep_merge_nested():
    base = {"a": {"x": 1, "y": 2}, "b": 1}
    overlay = {"a": {"y": 9}, "c": 3}
    assert deep_merge(base, overlay) == {"a": {"x": 1, "y": 9}, "b": 1, "c": 3}


def test_list_envelope():
    body = list_envelope([{"id": "1"}], page=1, limit=20, total=1)
    assert body["data"][0]["id"] == "1"
    assert body["meta"]["total"] == 1


def test_data_envelope_errors():
    body = data_envelope(None, errors=[{"code": "X"}])
    assert body["errors"][0]["code"] == "X"


def test_validators():
    assert nonempty("  hi ") == "hi"
    with pytest.raises(ValueError):
        nonempty("  ")
    assert is_email("a@b.com")
    assert not is_email("bad")
    assert require_email("user@example.com") == "user@example.com"
    with pytest.raises(ValueError):
        require_email("nope")


def test_parse_list_query():
    q = parse_list_query({"page": "2", "limit": "10", "q": " hello ", "status": "active", "extra": 1})
    assert q["page"] == 2
    assert q["limit"] == 10
    assert q["q"] == "hello"
    assert q["status"] == "active"
