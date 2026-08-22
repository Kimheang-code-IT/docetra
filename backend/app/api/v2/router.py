from fastapi import APIRouter, Depends

from app.api.v2.deps import csrf_protect
from app.api.v2.endpoints import health, system
from app.modules.admin_config.api.router import router as admin_config_router
from app.modules.organization.api.router import router as organization_router
from app.modules.people_access.api.router import router as people_access_router
from app.modules.record.api.router import router as record_router
from app.modules.reporting_support.api.router import router as reporting_support_router
from app.modules.storage_integration.api.router import router as storage_integration_router

router = APIRouter(prefix="/api/v2", dependencies=[Depends(csrf_protect)])
router.include_router(people_access_router)
router.include_router(record_router)
router.include_router(organization_router)
router.include_router(admin_config_router)
router.include_router(storage_integration_router)
router.include_router(reporting_support_router)
router.include_router(system.router)
router.include_router(health.router)
