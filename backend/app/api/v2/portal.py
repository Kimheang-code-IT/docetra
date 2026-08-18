from fastapi import APIRouter
from app.api.v2.entities import router_for
from app.api.v2.special import routes_for

router = APIRouter()
router.include_router(routes_for("/portal"))
for path, resource in {"portal/file-uploads":"file-uploads","portal/google-drive-sync":"google-drive-sync","portal/logs":"portal-logs"}.items():
    router.include_router(router_for(path, resource))
