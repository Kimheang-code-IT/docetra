from fastapi import APIRouter
from app.api.v2.entities import router_for

router = APIRouter()
for path, resource in {
 "organizations/departments":"departments", "organizations/companies":"companies",
 "organizations/company-purposes":"company-purposes", "organizations/company-sectors":"company-sectors",
 "organizations/officers":"officers"}.items():
    router.include_router(router_for(path, resource))
