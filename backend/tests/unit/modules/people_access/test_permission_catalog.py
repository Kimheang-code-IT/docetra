"""people_access — permission catalog and auth schemas."""

from app.application.people_router import router as people_router
from app.modules.people_access.domain.schemas import AuthUser, LoginRequest
from app.modules.people_access.services.permission_catalog import permission_catalog


def test_permission_catalog_rows():
    rows = permission_catalog()
    assert isinstance(rows, list)
    assert len(rows) > 0


def test_auth_user_schema():
    user = AuthUser(name="Admin", email="a@b.com", permissions=["dashboard.view"])
    assert user.email == "a@b.com"
    assert "dashboard.view" in user.permissions


def test_login_request():
    req = LoginRequest(email="a@b.com", password="secret")
    assert req.password == "secret"


def test_officers_http_is_top_level():
    assert any(route.path == "/officers" for route in people_router.routes)
