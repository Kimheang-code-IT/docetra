"""organization HTTP — classification collections + dynamic `/organizations/{org_type}`."""

from fastapi import APIRouter

from app.modules.organization.api import dynamic_organizations, purposes, sectors

router = APIRouter()
# Top-level `/sector` and `/purpose` must register before `{org_type}`.
router.include_router(sectors.router)
router.include_router(purposes.router)
router.include_router(dynamic_organizations.router)
