from app.core.concurrency import parse_version_token, require_matching_version
from app.core.errors import DomainError


def test_parse_version_from_if_match_and_query():
    assert parse_version_token(None, '"3"', None) == 3
    assert parse_version_token(None, None, "4") == 4
    assert parse_version_token(2, "99", "100") == 2
    assert parse_version_token(None, None, None) is None


def test_require_matching_version_conflict():
    try:
        require_matching_version(1, None)
        assert False, "expected VERSION_REQUIRED"
    except DomainError as exc:
        assert exc.status_code == 428
        assert exc.code == "VERSION_REQUIRED"

    try:
        require_matching_version(2, 1)
        assert False, "expected VERSION_CONFLICT"
    except DomainError as exc:
        assert exc.status_code == 409
        assert exc.code == "VERSION_CONFLICT"

    assert require_matching_version(5, 5) == 5
