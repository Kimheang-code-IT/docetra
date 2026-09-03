from fastapi import APIRouter, Depends

from app.api.v2.deps import csrf_protect
from app.api.v2.endpoints import health, system
from app.application.organization_router import router as organization_workflow_router
from app.application.attachment_router import router as attachment_workflow_router
from app.application.export_router import router as export_workflow_router
from app.application.people_router import router as people_workflow_router
from app.integrations.objectstore import configure_objectstore
from app.core.permissions import configure_record_permissions
from app.modules.admin_config.router import router as admin_config_router
from app.modules.organization.router import router as organization_router
from app.modules.people_access.router import router as people_access_router
from app.modules.record.router import configuration_router as record_configuration_router
from app.modules.record.router import router as record_router
from app.modules.record.service import permission_prefixes
from app.modules.reporting_support.router import dashboard_router, mentions_router, search_router
from app.modules.storage_integration.router import router as storage_integration_router
from app.modules.storage_integration.service import storage as storage_service

configure_objectstore(storage_service.resolve_storage)
configure_record_permissions(permission_prefixes())

router = APIRouter(prefix="/api/v2", dependencies=[Depends(csrf_protect)])
router.include_router(people_access_router)
router.include_router(people_workflow_router)
router.include_router(record_router)
router.include_router(attachment_workflow_router)
router.include_router(organization_workflow_router)
router.include_router(organization_router)
router.include_router(record_configuration_router)
router.include_router(admin_config_router)
router.include_router(storage_integration_router)
router.include_router(dashboard_router)
router.include_router(search_router)
router.include_router(export_workflow_router)
router.include_router(mentions_router)
router.include_router(system.router)
router.include_router(health.router)
