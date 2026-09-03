"""organization module — API types, government-structure mapping, permission prefixes."""

from app.modules.organization.domain.map import (
    ORG_TYPE_META,
    ORG_TYPES,
    RESERVED_ORG_SEGMENTS,
    RESOURCE_FOR_DB_ORG_TYPE,
    db_org_type_for,
    is_valid_org_type,
    permission_prefix_for_org_type,
)


def test_org_types():
    assert is_valid_org_type("department")
    assert is_valid_org_type("company")
    assert not is_valid_org_type("sectors")
    assert not is_valid_org_type("officers")
    assert not is_valid_org_type("government")
    assert set(ORG_TYPES) == {"department", "company"}


def test_department_is_government_structure():
    assert ORG_TYPES["department"] == "government"
    assert db_org_type_for("department") == "government"
    assert db_org_type_for("company") == "company"
    assert ORG_TYPE_META["department"]["kind"] == "government_structure"
    assert ORG_TYPE_META["company"]["kind"] == "company"
    assert RESOURCE_FOR_DB_ORG_TYPE["government"] == "departments"
    assert "officers" in RESERVED_ORG_SEGMENTS


def test_permission_prefixes():
    assert permission_prefix_for_org_type("department") == "organizations.departments"
    assert permission_prefix_for_org_type("company") == "organizations.companies"


def test_classification_http_is_top_level():
    from app.application.organization_router import router

    paths = {route.path for route in router.routes}
    assert "/sector" in paths
    assert "/purpose" in paths
