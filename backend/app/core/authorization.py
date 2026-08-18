from fastapi import Depends, HTTPException, Request
from app.core.security import current_user
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import Entity, Role, User, get_db
from app.core.permissions import TYPE_TO_PREFIX

RESOURCE_PREFIX={
 "meeting-topics":"meetings.topics","meeting-history":"meetings.history",
 "incoming-documents":"records.incoming_documents","outgoing-documents":"records.outgoing_documents",
 "documents":"records.documents","master-list-requests":"records.master_list_requests","record-logs":"records.logs",
 "departments":"organizations.departments","companies":"organizations.companies","company-purposes":"organizations.company_purposes",
 "company-sectors":"organizations.company_sectors","officers":"organizations.officers","roles":"users.roles","users":"users.users",
 "record-types":"configuration.record_types","record-attributes":"configuration.record_attributes","file-uploads":"portal.file_upload",
 "google-drive-sync":"portal.google_drive_sync","portal-logs":"portal.logs","system-logs":"system.logs"}

def require_permission(user:User,key:str)->None:
    if user.role not in {"SuperAdmin","Admin"} and key not in (user.permissions or []):
        raise HTTPException(403,f"Missing permission: {key}")

async def creator_only(db: AsyncSession, user: User, resource: str) -> bool:
    if user.role in {"SuperAdmin", "Admin"} or not user.role_id:
        return False
    role = await db.get(Role, user.role_id)
    prefix = RESOURCE_PREFIX.get(resource)
    document_type = next((key for key, value in TYPE_TO_PREFIX.items() if value == prefix), None)
    for row in ((role.payload if role else {}) or {}).get("permissionRows") or []:
        if row.get("documentType") == document_type:
            return bool(row.get("onlyIfCreator"))
    return False

def authorize_resource(resource:str):
    async def dependency(request:Request,user:User=Depends(current_user),db:AsyncSession=Depends(get_db)):
        if user.role in {"SuperAdmin","Admin"}: return
        prefix=RESOURCE_PREFIX.get(resource)
        if not prefix: return
        path=request.url.path; method=request.method
        action="view" if method=="GET" else "create" if method=="POST" and path.rstrip("/").endswith(request.scope["route"].path.rstrip("/").split("/{")[0].split("/api/v2/")[-1]) else "edit"
        if path.endswith("/archive"): action="archive"
        elif path.endswith("/restore"): action="restore"
        elif path.endswith("/purge"): action="purge"
        elif path.endswith("/bulk-delete"): action="delete"
        elif "/comments" in path: action="comment"
        elif path.endswith("/stage"): action="transition"
        elif method=="DELETE": action="delete"
        elif method=="POST" and "/{" not in request.scope["route"].path: action="create"
        require_permission(user,f"{prefix}.{action}")
        entity_id = request.path_params.get("entity_id")
        if entity_id and await creator_only(db, user, resource):
            try:
                import uuid
                row = await db.get(Entity, uuid.UUID(str(entity_id)))
            except ValueError:
                row = None
            if row and row.created_by != user.id:
                raise HTTPException(403, "This role is limited to records created by the current user")
    return dependency
