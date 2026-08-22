"""Sync record_organization rows from known record detail fields."""

from __future__ import annotations

import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.record import RecordOrganization
import app.modules.organization.services.service as org_service

# detail field → role_type for department-like orgs
DEPARTMENT_FIELD_ROLES = {
    "officeInCharge": "owner",
    "internalUnits": "participant",
}

# detail field → role_type for company-like orgs
COMPANY_FIELD_ROLES = {
    "externalUnits": "participant",
    "documentType": "observer",  # often a company name/id on document forms
}


def _as_list(value) -> list:
    if value is None or value == "":
        return []
    if isinstance(value, list):
        return value
    return [value]


async def sync_record_organizations(
    db: AsyncSession,
    record_id: uuid.UUID,
    payload: dict,
    actor_officer_id: uuid.UUID | None,
) -> None:
    """Replace record_organization links derived from payload detail fields."""
    links: list[tuple[uuid.UUID, str]] = []

    for field, role in DEPARTMENT_FIELD_ROLES.items():
        if field not in payload:
            continue
        for org_id in await org_service.resolve_organization_ids(db, _as_list(payload.get(field))):
            links.append((org_id, role))

    for field, role in COMPANY_FIELD_ROLES.items():
        if field not in payload:
            continue
        for org_id in await org_service.resolve_organization_ids(db, _as_list(payload.get(field))):
            links.append((org_id, role))

    # De-dupe by (org_id, role) preferring first occurrence
    seen: set[tuple[uuid.UUID, str]] = set()
    unique: list[tuple[uuid.UUID, str]] = []
    for org_id, role in links:
        key = (org_id, role)
        if key not in seen:
            seen.add(key)
            unique.append(key)

    await db.execute(delete(RecordOrganization).where(RecordOrganization.record_id == record_id))
    for org_id, role in unique:
        db.add(
            RecordOrganization(
                record_id=record_id,
                organization_id=org_id,
                role_type=role,
                created_by=actor_officer_id,
                updated_by=actor_officer_id,
            )
        )
