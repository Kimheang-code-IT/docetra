"""Typed organization collections — companies, departments, sectors, purposes."""

from __future__ import annotations

import math
import uuid

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.datetime import utcnow
from app.modules.organization.model import Organization, OrganizationPurpose, OrganizationSector
from typing import Any as User
import app.modules.organization.services.service as org_service


class OrganizationApplicationService:
    def __init__(self, host):
        self.host = host

    def kind(self) -> str:
        return self.host.kind()

    async def list_items(self, db: AsyncSession, user: User, params: dict, page: int, limit: int, q, status) -> dict:
        kind = self.kind()
        if kind == "organization":
            org_type = self.host.resolve_db_org_type()
            filters = [Organization.organization_type == org_type]
            if not status or status in {"all", "all-status"}:
                filters.append(Organization.is_active == 1)
            elif "inactive" in (status or ""):
                filters.append(Organization.is_active == 0)
            else:
                filters.append(Organization.is_active == 1)
            if q:
                filters.append(Organization.nam.ilike(f"%{q}%"))
            parent_id = params.get("parentId")
            if parent_id:
                try:
                    filters.append(Organization.parent_id == uuid.UUID(str(parent_id)))
                except ValueError:
                    filters.append(Organization.id == None)  # noqa: E711
            elif str(params.get("rootsOnly") or "").lower() in {"1", "true", "yes"}:
                filters.append(Organization.parent_id.is_(None))
            from app.shared.list_query import date_filters, order_clause

            filters.extend(date_filters(params, Organization.updated_at))
            total = await db.scalar(select(func.count()).select_from(Organization).where(*filters)) or 0
            rows = (await db.scalars(select(Organization).where(*filters).order_by(order_clause(params, Organization)).offset((page - 1) * limit).limit(limit))).all()
            return {"data": [org_service.org_to_payload(row) for row in rows], "meta": {"page": page, "limit": limit, "total": total, "totalPages": max(1, math.ceil(total / limit))}}

        if kind == "sector":
            filters = []
            if not status or status in {"all", "all-status"}:
                filters.append(OrganizationSector.is_active == 1)
            if q:
                filters.append(OrganizationSector.nam.ilike(f"%{q}%"))
            rows = (await db.scalars(select(OrganizationSector).where(*filters).order_by(OrganizationSector.updated_at.desc()).limit(limit))).all() if filters else (await db.scalars(select(OrganizationSector).order_by(OrganizationSector.updated_at.desc()).offset((page - 1) * limit).limit(limit))).all()
            total = len(rows)
            return {"data": [org_service.sector_to_payload(row) for row in rows], "meta": {"page": page, "limit": limit, "total": total, "totalPages": 1}}

        rows = (await db.scalars(select(OrganizationPurpose).order_by(OrganizationPurpose.updated_at.desc()).offset((page - 1) * limit).limit(limit))).all()
        return {"data": [org_service.purpose_to_payload(row) for row in rows], "meta": {"page": page, "limit": limit, "total": len(rows), "totalPages": 1}}

    async def get_item(self, db: AsyncSession, entity_id: str) -> dict:
        uid = uuid.UUID(entity_id)
        kind = self.kind()
        if kind == "organization":
            row = await self.host.get_org_row_or_404(db, entity_id)
            return org_service.org_to_payload(row)
        if kind == "sector":
            row = await db.get(OrganizationSector, uid)
            if not row:
                raise HTTPException(404, "Not found")
            return org_service.sector_to_payload(row)
        row = await db.get(OrganizationPurpose, uid)
        if not row:
            raise HTTPException(404, "Not found")
        return org_service.purpose_to_payload(row)

    async def create(self, db: AsyncSession, user: User, payload: dict) -> dict:
        officer_id = await self.host.actor_officer_id(db, user)
        kind = self.kind()
        if kind == "organization":
            db_type = self.host.resolve_db_org_type()
            is_company = db_type == "company"
            parent = payload.get("parentId")
            if is_company and parent:
                parent = None
            await org_service.validate_org_parent(db, None, parent, organization_type=db_type if not is_company else None)
            sector_id, purpose_id = await org_service.resolve_sector_purpose_ids(db, payload, require_company=is_company)
            lvl = 1
            if not is_company:
                lvl = await org_service.resolve_org_level(db, parent)
            row = Organization(
                nam=str(payload.get("name") or ""),
                code=payload.get("code"),
                description=payload.get("description"),
                organization_type=db_type,
                parent_id=uuid.UUID(str(parent)) if parent else None,
                sector_id=sector_id,
                organization_purpose_id=purpose_id,
                lvl=lvl,
                tax_id=payload.get("taxId"),
                address=payload.get("address"),
                email=payload.get("email"),
                phone=payload.get("phone"),
                logo_url=payload.get("logoUrl"),
                is_active=0 if payload.get("status") == "inactive" else 1,
                created_by=officer_id,
                updated_by=officer_id,
            )
            db.add(row)
            await db.flush()
            await self.host.after_organization_created(db, row.id, officer_id)
            await db.flush()
            await db.refresh(row)
            return org_service.org_to_payload(row)
        if kind == "sector":
            row = OrganizationSector(nam=str(payload.get("name") or ""), description=payload.get("description"), is_active=1, created_by=officer_id, updated_by=officer_id)
            if payload.get("parentId"):
                row.parent_id = uuid.UUID(str(payload["parentId"]))
            db.add(row)
            await db.flush()
            await db.refresh(row)
            return org_service.sector_to_payload(row)
        row = OrganizationPurpose(nam=str(payload.get("name") or ""), description=payload.get("description"), is_active=1, created_by=officer_id, updated_by=officer_id)
        db.add(row)
        await db.flush()
        await db.refresh(row)
        return org_service.purpose_to_payload(row)

    async def update(self, db: AsyncSession, user: User, entity_id: str, body: dict) -> dict:
        officer_id = await self.host.actor_officer_id(db, user)
        kind = self.kind()
        if kind == "organization":
            row = await self.host.get_org_row_or_404(db, entity_id)
            db_type = self.host.resolve_db_org_type()
            is_company = db_type == "company"
            parent_value = body.get("parentId", row.parent_id)
            if is_company:
                parent_value = None
            await org_service.validate_org_parent(
                db,
                row.id,
                parent_value,
                organization_type=db_type if not is_company else None,
            )
            if "name" in body:
                row.nam = str(body["name"])
            for attr, key in [("code", "code"), ("description", "description"), ("tax_id", "taxId"), ("address", "address"), ("email", "email"), ("phone", "phone"), ("logo_url", "logoUrl")]:
                if key in body:
                    setattr(row, attr, body[key])
            if "parentId" in body or not is_company:
                if is_company:
                    row.parent_id = None
                    row.lvl = 1
                else:
                    row.parent_id = uuid.UUID(str(parent_value)) if parent_value else None
                    row.lvl = await org_service.resolve_org_level(db, row.parent_id)
            if any(k in body for k in ("sectorId", "purposeId", "organizationPurposeId")):
                sector_id, purpose_id = await org_service.resolve_sector_purpose_ids(
                    db,
                    {
                        "sectorId": body.get("sectorId", row.sector_id),
                        "purposeId": body.get("purposeId", body.get("organizationPurposeId", row.organization_purpose_id)),
                    },
                    require_company=is_company,
                )
                row.sector_id = sector_id
                row.organization_purpose_id = purpose_id
            if "status" in body:
                row.is_active = 0 if body["status"] == "inactive" else 1
            row.updated_by = officer_id
            row.updated_at = utcnow()
            await db.flush()
            await db.refresh(row)
            return org_service.org_to_payload(row)
        row = await self.host._get_model(db, kind, entity_id)
        if kind == "sector" and "name" in body:
            row.nam = str(body["name"])
        elif kind == "purpose" and "name" in body:
            row.nam = str(body["name"])
        row.updated_by = officer_id
        row.updated_at = utcnow()
        await db.flush()
        return await self.get_item(db, entity_id)

    async def soft_delete(self, db: AsyncSession, entity_id: str) -> dict:
        if self.kind() == "organization":
            row = await self.host.get_org_row_or_404(db, entity_id)
            row.is_active = 0
            await db.flush()
            return {"id": entity_id}
        return await self.purge(db, entity_id)

    async def purge(self, db: AsyncSession, entity_id: str) -> dict:
        if self.kind() == "organization":
            row = await self.host.get_org_row_or_404(db, entity_id)
            await db.delete(row)
            await db.flush()
            return {"id": entity_id}
        row = await self.host._get_model(db, self.kind(), entity_id)
        await db.delete(row)
        await db.flush()
        return {"id": entity_id}
