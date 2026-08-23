"""User payloads must not carry authoritative role names or permission arrays."""

from types import SimpleNamespace

from app.core.errors import DomainError
from app.core.privileged import is_unrestricted_role_name
from app.modules.people_access.services.identity import parse_role_level, strip_user_authority, validate_user_password
from app.modules.people_access.services.people import user_to_payload


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


def test_validate_user_password_required_on_create():
    validate_user_password("long-enough", required=True)
    validate_user_password("", required=False)
    try:
        validate_user_password("", required=True)
        raise AssertionError("expected password required")
    except DomainError as exc:
        assert exc.status_code == 422
        assert "required" in exc.message.lower()
    try:
        validate_user_password("short", required=True)
        raise AssertionError("expected password too short")
    except DomainError as exc:
        assert exc.status_code == 422
        assert "8" in exc.message


def test_user_to_payload_includes_officer_and_omits_password():
    officer_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    user = SimpleNamespace(
        id="bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
        name="Pat",
        email="pat@example.com",
        role="User",
        role_id="cccccccc-cccc-cccc-cccc-cccccccccccc",
        officer_id=officer_id,
        avatar=None,
        permissions=[],
        status="active",
        active=True,
        created_at=None,
        updated_at=None,
        version=1,
    )
    payload = user_to_payload(user, officer_name="Kimheang")
    assert payload["officerId"] == officer_id
    assert payload["officerName"] == "Kimheang"
    assert "password" not in payload
    assert "passwordHash" not in payload


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
