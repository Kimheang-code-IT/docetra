"""Public application-service facade for Record."""

from app.modules.record.services.service import CollectionService
from app.modules.record.services import collaboration, serializer, type_access
from app.modules.record.services.router_factory import router_for
from app.modules.record.services.stamp import entity_by_id, entity_or_404, stamp
from app.modules.record.domain.map import RECORD_RESOURCES
from app.modules.record.domain.map import TYPE_UI_DEFAULTS, permission_prefix_for_type_code
from app.modules.record.services.serializer import details_as_dict, ensure_record_type
from app.modules.record.services.reporting import dashboard_read, read_for_reporting, search_for_reporting
from app.modules.people_access.service import people
from app.modules.record.services import entity_bags


def permission_prefixes() -> list[tuple[str, str]]:
    return [(code, permission_prefix_for_type_code(code)) for code in TYPE_UI_DEFAULTS]


async def actor_officer_id(db, user):
    return (await people.ensure_officer_for_user(db, user)).id

__all__ = [
    "CollectionService",
    "RECORD_RESOURCES",
    "actor_officer_id",
    "collaboration",
    "details_as_dict",
    "dashboard_read",
    "entity_by_id",
    "entity_bags",
    "entity_or_404",
    "ensure_record_type",
    "permission_prefixes",
    "read_for_reporting",
    "search_for_reporting",
    "router_for",
    "serializer",
    "stamp",
    "type_access",
]
