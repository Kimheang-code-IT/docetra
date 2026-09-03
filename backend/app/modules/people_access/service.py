"""Public application-service facade for People Access."""

from app.modules.people_access.services import identity, identity_sync, people
from app.modules.people_access.services.identity import ensure_admin_entity, normalize_identity_payload, strip_secrets
from app.modules.people_access.services.people import ensure_officer_for_user, ensure_superadmin_role, officer_ids_for_organization, officer_names_by_ids, officer_organization_id, public_users_by_ids, seed_menus
from app.modules.people_access.services.identity_collections import IdentityApplicationService
from app.modules.people_access.services.reporting import read_for_reporting, search_for_reporting
from app.modules.people_access.services.collection import PeopleCollectionService

__all__ = ["IdentityApplicationService", "PeopleCollectionService", "ensure_admin_entity", "ensure_officer_for_user", "ensure_superadmin_role", "identity", "identity_sync", "normalize_identity_payload", "officer_ids_for_organization", "officer_names_by_ids", "officer_organization_id", "people", "public_users_by_ids", "read_for_reporting", "search_for_reporting", "seed_menus", "strip_secrets"]
