"""Comment mutation is author-or-unrestricted."""

from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.modules.record.services.collaboration import assert_comment_author_or_unrestricted


def test_author_can_modify_own_comment():
    author = SimpleNamespace(id="11111111-1111-1111-1111-111111111111", role="User")
    row = SimpleNamespace(author_id=author.id)
    assert_comment_author_or_unrestricted(row, author)


def test_other_user_cannot_modify_comment():
    author_id = "11111111-1111-1111-1111-111111111111"
    other = SimpleNamespace(id="22222222-2222-2222-2222-222222222222", role="User")
    row = SimpleNamespace(author_id=author_id)
    with pytest.raises(HTTPException) as exc:
        assert_comment_author_or_unrestricted(row, other)
    assert exc.value.status_code == 403


def test_superadmin_can_moderate_comment():
    admin = SimpleNamespace(id="22222222-2222-2222-2222-222222222222", role="SuperAdmin")
    row = SimpleNamespace(author_id="11111111-1111-1111-1111-111111111111")
    assert_comment_author_or_unrestricted(row, admin)
