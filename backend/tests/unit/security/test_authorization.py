"""Authorization and permission gate helpers (no DB)."""

import pytest
from fastapi import HTTPException

pytestmark = pytest.mark.security

from types import SimpleNamespace

from app.core.authorization import RESOURCE_PREFIX, require_permission
from app.core.permissions import catalog_rows, expand_permission_rows
from app.core.rate_limit import safe_key, settings_account_lock_seconds, settings_max_login_failures


def _user(*, role: str = "User", permissions: list[str] | None = None):
    return SimpleNamespace(role=role, permissions=permissions or [])


def test_require_permission_allows_superadmin():
    require_permission(_user(role="SuperAdmin"), "records.documents.delete")


def test_require_permission_allows_admin_name_only_when_stored():
    require_permission(_user(role="Admin"), "records.documents.delete")


def test_document_manager_is_not_unrestricted():
    from app.core.privileged import is_unrestricted

    assert not is_unrestricted(_user(role="Document Manager"))
    assert not is_unrestricted(_user(role="User", permissions=["records.documents.purge"]))


def test_require_permission_allows_listed_key():
    require_permission(_user(permissions=["records.documents.view"]), "records.documents.view")


def test_require_permission_denies_missing_key():
    with pytest.raises(HTTPException) as exc:
        require_permission(_user(permissions=["records.documents.view"]), "records.documents.delete")
    assert exc.value.status_code == 403
    assert "Missing permission" in str(exc.value.detail)


def test_resource_prefix_covers_core_collections():
    assert RESOURCE_PREFIX["incoming-documents"] == "records.incoming_documents"
    assert RESOURCE_PREFIX["departments"] == "organizations.departments"
    assert RESOURCE_PREFIX["meeting-history"] == "records.meeting_history"
    assert "meetings." not in RESOURCE_PREFIX["meeting-history"]


def test_permission_catalog_non_empty():
    rows = catalog_rows()
    assert isinstance(rows, list) and rows
    assert all("documentType" in row and "actions" in row for row in rows[:3])


def test_expand_permission_rows_builds_flat_keys():
    keys = expand_permission_rows([{"documentType": "document", "actions": ["view", "edit"]}])
    assert "records.documents.view" in keys
    assert "records.documents.edit" in keys


def test_rate_limit_safe_key_is_stable_hash():
    assert safe_key("Admin@Example.com") == safe_key("admin@example.com")
    assert safe_key("a") != safe_key("b")
    assert len(safe_key("x")) == 64


def test_lock_settings_positive():
    assert settings_account_lock_seconds() >= 60
    assert settings_max_login_failures() >= 1
