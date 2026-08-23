"""User payloads must not carry authoritative role names or permission arrays."""

from types import SimpleNamespace

from app.core.privileged import is_unrestricted_role_name
from app.modules.people_access.services.identity import parse_role_level, strip_user_authority


def test_strip_user_authority_drops_client_privilege_fields():
    cleaned = strip_user_authority({
        "email": "a@b.com",
        "name": "Pat",
        "roleId": "role-1",
        "roleName": "Admin",
        "role": "SuperAdmin",
        "permissions": ["users.users.purge"],
        "permissionRows": [{"documentType": "user", "actions": ["purge"]}],
        "password": "secret-pass",
    })
    assert cleaned["email"] == "a@b.com"
    assert cleaned["roleId"] == "role-1"
    assert "roleName" not in cleaned
    assert "role" not in cleaned
    assert "permissions" not in cleaned
    assert "permissionRows" not in cleaned
    assert cleaned["password"] == "secret-pass"


def test_protected_role_names():
    assert is_unrestricted_role_name("SuperAdmin")
    assert is_unrestricted_role_name("Admin")
    assert is_unrestricted_role_name("super admin")
    assert not is_unrestricted_role_name("User")
    assert not is_unrestricted_role_name("Administrator-Assistant")


def test_parse_role_level_preserves_zero():
    assert parse_role_level(0) == 0
    assert parse_role_level(None) == 1
    assert parse_role_level("") == 1
    assert parse_role_level(5) == 5


def test_limited_user_namespace_is_not_admin():
    user = SimpleNamespace(role="User", permissions=["users.users.create"])
    from app.core.privileged import is_unrestricted

    assert not is_unrestricted(user)
