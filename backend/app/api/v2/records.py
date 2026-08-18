from fastapi import APIRouter
from app.api.v2.entities import router_for

router = APIRouter()
for path, resource in {
 "records/incoming-documents":"incoming-documents", "records/outgoing-documents":"outgoing-documents",
 "records/documents":"documents", "records/master-list-requests":"master-list-requests", "records/logs":"record-logs"}.items():
    router.include_router(router_for(path, resource))
