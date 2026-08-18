from fastapi import APIRouter, Depends
from app.core.csrf import csrf_protect
from app.api.v2.auth import router as auth_router
from app.api.v2 import configuration, dashboard, exports, files, health, meetings, mentions, organizations, portal, records, search, settings, system, users

router = APIRouter(prefix="/api/v2", dependencies=[Depends(csrf_protect)])
router.include_router(auth_router)
for family in (dashboard, meetings, records, organizations, users, configuration, settings, portal, system, search, exports, mentions, files, health):
    router.include_router(family.router)
