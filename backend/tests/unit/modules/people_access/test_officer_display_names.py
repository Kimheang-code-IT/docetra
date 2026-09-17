from app.modules.people_access.services.people import officer_to_payload
from app.modules.people_access.model import Officer
import uuid


def test_officer_payload_includes_display_names():
    officer = Officer(
        id=uuid.uuid4(),
        nam="kimheang",
        organization_id=uuid.uuid4(),
        role_id=uuid.uuid4(),
        is_active=1,
    )
    payload = officer_to_payload(
        officer,
        organization_name="Operations",
        role_name="Super Admin",
    )
    assert payload["organizationName"] == "Operations"
    assert payload["roleName"] == "Super Admin"
    assert payload["roleId"] == str(officer.role_id)
    assert payload["organizationId"] == str(officer.organization_id)
