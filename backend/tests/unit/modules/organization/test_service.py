"""organization module — payload helpers and link field maps."""

from types import SimpleNamespace
from uuid import uuid4

from app.modules.organization.services.record_links import (
    COMPANY_FIELD_ROLES,
    DEPARTMENT_FIELD_ROLES,
    _as_list,
)
from app.modules.organization.services.service import org_to_payload, purpose_to_payload, sector_to_payload
from app.modules.organization.domain.schemas import OrganizationPayload


def test_as_list_normalizes():
    assert _as_list(None) == []
    assert _as_list("") == []
    assert _as_list("x") == ["x"]
    assert _as_list(["a", "b"]) == ["a", "b"]


def test_department_and_company_link_fields():
    assert "officeInCharge" in DEPARTMENT_FIELD_ROLES
    assert "externalUnits" in COMPANY_FIELD_ROLES


def test_org_to_payload():
    oid = uuid4()
    row = SimpleNamespace(
        id=oid,
        nam="Dept A",
        code="DA",
        description="d",
        parent_id=None,
        sector_id=None,
        organization_purpose_id=None,
        organization_type="government",
        tax_id=None,
        address=None,
        contact_info=None,
        email=None,
        phone=None,
        logo_url=None,
        lvl=1,
        is_active=True,
        created_at=None,
        updated_at=None,
    )
    payload = org_to_payload(row)
    assert payload["id"] == str(oid)
    assert payload["name"] == "Dept A"
    assert payload["status"] == "active"
    assert payload["organizationType"] == "government"


def test_sector_purpose_payload():
    sid = uuid4()
    sector = SimpleNamespace(
        id=sid,
        nam="Sec",
        parent_id=None,
        description=None,
        is_active=True,
        created_at=None,
        updated_at=None,
    )
    assert sector_to_payload(sector)["name"] == "Sec"
    purpose = SimpleNamespace(
        id=sid,
        nam="Pur",
        description=None,
        is_active=False,
        created_at=None,
        updated_at=None,
    )
    assert purpose_to_payload(purpose)["status"] == "inactive"


def test_organization_schema():
    body = OrganizationPayload(name="X", code="X1")
    assert body.name == "X"
