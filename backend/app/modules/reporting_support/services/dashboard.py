from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.datetime import iso_utc
from app.core.frontend_contract import DASHBOARD_KPIS, RECORD_RESOURCES, user_can_view_resource
from app.modules.record.service import RECORD_RESOURCES as RECORD_TYPE_BY_RESOURCE, dashboard_read


STAGE_TYPE_CODES = tuple(
    RECORD_TYPE_BY_RESOURCE[resource]
    for resource in RECORD_RESOURCES
    if resource in RECORD_TYPE_BY_RESOURCE
)


async def build_dashboard_summary(db: AsyncSession, user: object) -> dict:
    now = datetime.now(timezone.utc)
    data = await dashboard_read(db, now, STAGE_TYPE_CODES)
    updated_at = iso_utc(now)
    kpis = []
    for resource, label_key, href in DASHBOARD_KPIS:
        if not user_can_view_resource(user, resource):
            continue
        code = RECORD_TYPE_BY_RESOURCE.get(resource)
        kpis.append(
            {
                "id": resource,
                "labelKey": label_key,
                "value": data["countsByCode"].get(code, 0) if code else 0,
                "href": href,
                "updatedAt": updated_at,
            }
        )
    return {
        "kpis": kpis,
        "workByStage": data["workByStage"],
        "recordsOverTime": data["recordsOverTime"],
        "events": data["events"] if user_can_view_resource(user, "meeting-history") else [],
    }
