import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import String, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.authorization import RESOURCE_PREFIX, require_permission
from app.core.permissions import catalog_rows
from app.core.security import current_user, now_iso
from app.core.datetime import iso_utc
from app.db import AppSetting, Entity, Outbox, User, get_db
from app.api.v2.entities import entity_or_404, stamp
from app.core.secrets import MASK, mask_mapping, protect_mapping, reveal_mapping

router = APIRouter(tags=["application"])

def routes_for(*prefixes: str) -> APIRouter:
    """Return a router containing this module's routes for one API family."""
    selected = APIRouter()
    selected.routes.extend(route for route in router.routes if any(route.path.startswith(p) for p in prefixes))
    return selected
DEFAULT_APP_INFO = {"applicationName":"Docetra","shortName":"Docetra","organizationName":"General Department of Corporate Services","description":"Document and record management system","supportEmail":"support@example.com","branding":{"primaryColor":"#e8472a","secondaryColor":"#3a539f"},"footer":{"copyrightText":"© Docetra"}}
DEFAULT_APP_CONFIG = {
 "general":{"defaultLandingPage":"/","defaultPageSize":20,"defaultRecordView":"table","enableComments":True,"enableSharing":True,"enableExport":True,"maxUploadSizeMb":25},
 "localization":{"defaultLanguage":"en","availableLanguages":["en","km"],"timezone":"Asia/Phnom_Penh","dateFormat":"dd/MM/yyyy","timeFormat":"HH:mm","firstDayOfWeek":1,"numberFormat":"en-US","currency":"KHR","locale":"en"},
 "email":{"enabled":False,"smtpHost":"","smtpPort":587,"username":"","password":"","encryption":"starttls","fromName":"Docetra","fromEmail":"","timeoutSeconds":10,"connectionStatus":"not_tested"},
 "telegram":{"enabled":False,"botDisplayName":"Docetra","botToken":"","connectionMode":"bot_api","messageLanguage":"en","includeRecordLink":True,"includeOrganization":True,"includeAssignedOfficer":True,"connectionStatus":"not_tested","destinations":[],"messageTemplate":"[{{record_type}}] {{record_number}}\n{{record_title}}"},
 "notifications":{"inAppEnabled":True,"emailEnabled":False,"telegramEnabled":False,"deliveryRetries":3,"quietHoursEnabled":False,"language":"en","rules":[]},
 "security":{"sessionTimeoutMinutes":480,"maxLoginAttempts":5,"accountLockMinutes":15,"passwordExpiryDays":0,"requirePasswordChange":False,"allowedUploadExtensions":["pdf","doc","docx","xls","xlsx","png","jpg","jpeg"],"auditRetentionDays":365,"frontendOnly":False},
 "system":{"maintenanceMode":False,"readOnlyMode":False,"paginationDefault":20,"configurationVersion":"1.0.0","environment":"development","cacheStatus":"healthy","backgroundJobStatus":"idle"},
 "display":{"cardFields":{},"cardFooterAlign":{}}}

def merge_setting(current: dict, incoming: dict) -> dict:
    merged = dict(current)
    for key, value in incoming.items():
        if key == "updatedAt":
            continue
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            nested = {**merged[key], **value}
            if nested.get("password") in {"", MASK}:
                nested["password"] = merged[key].get("password")
            if nested.get("botToken") in {"", MASK}:
                nested["botToken"] = merged[key].get("botToken")
            merged[key] = nested
        else:
            merged[key] = value
    return merged

async def get_setting(db, key, default):
    row = await db.get(AppSetting, key)
    if not row:
        row = AppSetting(key=key, value=protect_mapping(default))
        db.add(row)
        await db.commit()
        await db.refresh(row)
    value = mask_mapping(dict(row.value))
    value["updatedAt"] = iso_utc(row.updated_at)
    return {"data": value}

@router.get("/users/permission-catalog")
async def permission_catalog(user: User = Depends(current_user)):
    require_permission(user,"users.roles.view")
    return {"data": catalog_rows()}

def resolved_schema(row):
    p=stamp(row); return {"recordType":p,"tabs":p.get("tabs",[]),"fields":p.get("fields") or p.get("attributes",[]),"workflowStages":p.get("workflowStages",[]),"version":row.version}
@router.get("/configuration/record-types/by-code/{code}/schema")
async def schema_by_code(code:str,db:AsyncSession=Depends(get_db),user:User=Depends(current_user)):
    require_permission(user,"configuration.record_types.view")
    row=await db.scalar(select(Entity).where(Entity.resource=="record-types",Entity.payload["code"].as_string()==code))
    if not row: raise HTTPException(404,"Record type not found")
    return {"data":resolved_schema(row)}
@router.get("/configuration/record-types/{entity_id}/schema")
async def schema_by_id(entity_id:str,db:AsyncSession=Depends(get_db),user:User=Depends(current_user)):
    require_permission(user,"configuration.record_types.view")
    return {"data":resolved_schema(await entity_or_404(db,"record-types",entity_id))}

@router.post("/meetings/history/{meeting_id}/assign-topic")
async def assign_topic(meeting_id:str,body:dict,db:AsyncSession=Depends(get_db),user:User=Depends(current_user)):
    require_permission(user,"meetings.history.assign")
    row=await entity_or_404(db,"meeting-history",meeting_id); row.payload={**row.payload,"topicId":body.get("topicId"),"topicTitle":body.get("topicTitle"),"sortOrder":body.get("sortOrder")}; await db.commit(); await db.refresh(row); return {"data":stamp(row)}
@router.post("/meetings/reorder")
async def reorder(body:dict,db:AsyncSession=Depends(get_db),user:User=Depends(current_user)):
    require_permission(user,"meetings.history.edit")
    ids=body.get("orderedMeetingIds",[])
    for i,item_id in enumerate(ids):
        row=await entity_or_404(db,"meeting-history",item_id); row.payload={**row.payload,"topicId":body.get("topicId"),"sortOrder":i}
    await db.commit(); return {"data":{"topicId":body.get("topicId"),"orderedMeetingIds":ids}}
@router.post("/meetings/history/{meeting_id}/attachments/link")
async def link_drive(meeting_id:str,body:dict,db:AsyncSession=Depends(get_db),user:User=Depends(current_user)):
    require_permission(user,"meetings.history.edit")
    row=await entity_or_404(db,"meeting-history",meeting_id); file={"id":str(uuid.uuid4()),"name":body.get("displayName") or "Drive file","mimeType":body.get("mimeType","application/octet-stream"),"sizeBytes":body.get("sizeBytes",0),"url":body.get("webViewLink"),"uploadedAt":now_iso(),"storageSource":"google_drive","driveFileId":body.get("driveFileId")}; row.payload={**row.payload,"attachments":[file,*row.payload.get("attachments",[])]}; await db.commit(); return {"data":file}
@router.get("/portal/drive-files")
async def drive_files(request:Request,db:AsyncSession=Depends(get_db),user:User=Depends(current_user)):
    require_permission(user,"portal.google_drive_sync.view")
    rows=(await db.scalars(select(Entity).where(Entity.resource.in_(["drive-files","google-drive-sync"]),Entity.status=="active").limit(min(200,int(request.query_params.get("limit",50)))))).all(); return {"data":[stamp(x) for x in rows],"meta":{"page":1,"limit":50,"total":len(rows)}}

@router.post("/portal/google-drive-sync/sources", status_code=201)
async def create_drive_source(body: dict, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    require_permission(user, "portal.google_drive_sync.edit")
    if not body.get("folderId") and not settings.google_drive_folder_id:
        raise HTTPException(422, "folderId is required")
    row = Entity(resource="google-drive-sync", payload=protect_mapping({**body, "kind": "source", "syncStatus": "not_tested"}), status="active", created_by=user.id, updated_by=user.id)
    db.add(row); await db.commit(); await db.refresh(row)
    return {"data": {**stamp(row), **mask_mapping(row.payload or {})}}

@router.post("/portal/google-drive-sync/sources/{source_id}/sync", status_code=202)
async def start_drive_sync(source_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    require_permission(user, "portal.google_drive_sync.edit")
    source = await entity_or_404(db, "google-drive-sync", source_id)
    if (source.payload or {}).get("kind") != "source": raise HTTPException(404, "Drive source not found")
    existing = await db.scalar(select(Entity).where(Entity.resource == "google-drive-sync", Entity.payload["kind"].as_string() == "job", Entity.payload["sourceId"].as_string() == source_id, Entity.payload["status"].as_string().in_(["queued", "processing"])))
    if existing: return {"data": stamp(existing)}
    job = Entity(resource="google-drive-sync", payload={"kind": "job", "sourceId": source_id, "status": "queued", "attempts": 0, "createdAt": now_iso()}, status="active", created_by=user.id, updated_by=user.id)
    db.add(job); await db.flush(); db.add(Outbox(topic="drive.sync", payload={"jobId": str(job.id)})); await db.commit(); await db.refresh(job)
    return {"data": stamp(job)}

@router.get("/portal/google-drive-sync/jobs/{job_id}")
async def drive_sync_status(job_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    require_permission(user, "portal.google_drive_sync.view")
    row = await entity_or_404(db, "google-drive-sync", job_id)
    if (row.payload or {}).get("kind") != "job": raise HTTPException(404, "Drive sync job not found")
    return {"data": stamp(row)}

@router.get("/settings/app-info")
async def app_info(db:AsyncSession=Depends(get_db),user:User=Depends(current_user)):
    require_permission(user,"settings.app_info.view"); return await get_setting(db,"app-info",DEFAULT_APP_INFO)
@router.patch("/settings/app-info")
@router.put("/settings/app-info")
async def update_app_info(body:dict,db:AsyncSession=Depends(get_db),user:User=Depends(current_user)):
    require_permission(user,"settings.app_info.edit")
    row=await db.get(AppSetting,"app-info") or AppSetting(key="app-info",value=DEFAULT_APP_INFO); row.value=merge_setting(row.value or DEFAULT_APP_INFO, body); row.updated_at=datetime.now(timezone.utc); db.add(row); await db.commit(); return await get_setting(db,"app-info",DEFAULT_APP_INFO)
@router.post("/settings/app-info/reset")
async def reset_app_info(db:AsyncSession=Depends(get_db),user:User=Depends(current_user)):
    require_permission(user,"settings.app_info.configure")
    row=await db.get(AppSetting,"app-info") or AppSetting(key="app-info",value={}); row.value=DEFAULT_APP_INFO; row.updated_at=datetime.now(timezone.utc); db.add(row); await db.commit(); return await get_setting(db,"app-info",DEFAULT_APP_INFO)
@router.get("/settings/app-config")
async def app_config(db:AsyncSession=Depends(get_db),user:User=Depends(current_user)):
    require_permission(user,"settings.app_config.view"); return await get_setting(db,"app-config",DEFAULT_APP_CONFIG)
@router.patch("/settings/app-config")
async def update_app_config(body:dict,db:AsyncSession=Depends(get_db),user:User=Depends(current_user)):
    require_permission(user,"settings.app_config.edit")
    row=await db.get(AppSetting,"app-config") or AppSetting(key="app-config",value=protect_mapping(DEFAULT_APP_CONFIG)); current=reveal_mapping(row.value or DEFAULT_APP_CONFIG); row.value=protect_mapping(merge_setting(current, body)); row.updated_at=datetime.now(timezone.utc); db.add(row); await db.commit(); return await get_setting(db,"app-config",DEFAULT_APP_CONFIG)
@router.post("/settings/app-config/email/test-connection")
@router.post("/settings/app-config/email/send-test")
@router.post("/settings/app-config/telegram/test-connection")
@router.post("/settings/app-config/telegram/send-test")
async def test_connection(request: Request, db: AsyncSession = Depends(get_db),user:User=Depends(current_user)):
    require_permission(user,"settings.app_config.configure")
    path = request.url.path
    saved = await db.get(AppSetting, "app-config")
    config = reveal_mapping((saved.value if saved else {}) or {})
    if "email" in path:
        from app.modules.notifications.email import send_test_email
        result = await send_test_email(settings.email_from_address, smtp=config.get("email") or {})
        return {"data": {**result, "testedAt": now_iso()}}
    if "telegram" in path:
        from app.modules.notifications.telegram import test_bot
        result = await test_bot("meeting",config=config.get("telegram") or {})
        return {"data": {**result, "testedAt": now_iso()}}
    return {"data": {"status": "connected", "message": "Configuration accepted", "testedAt": now_iso()}}

@router.get("/settings/storage")
async def storage_list(db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    require_permission(user,"settings.storage.view")
    rows = (await db.scalars(select(Entity).where(Entity.resource == "storage-providers", Entity.status != "deleted"))).all()
    return {"data": [{**stamp(row), **mask_mapping(row.payload or {})} for row in rows], "meta": {"page": 1, "limit": len(rows) or 20, "total": len(rows)}}

@router.post("/settings/storage")
async def storage_create(body: dict, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    require_permission(user,"settings.storage.configure")
    body = {**body, "connectionStatus": "not_tested", "isDefault": bool(body.get("isDefault")), "active": bool(body.get("active", True))}
    row = Entity(resource="storage-providers", payload=protect_mapping(body), status="active", created_by=user.id, updated_by=user.id)
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return {"data": {**stamp(row), **mask_mapping(row.payload or {})}}

@router.get("/settings/storage/{entity_id}")
async def storage_get(entity_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    require_permission(user,"settings.storage.view")
    row = await entity_or_404(db, "storage-providers", entity_id)
    return {"data": {**stamp(row), **mask_mapping(row.payload or {})}}

@router.put("/settings/storage/{entity_id}")
@router.patch("/settings/storage/{entity_id}")
async def storage_update(entity_id: str, body: dict, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    require_permission(user,"settings.storage.edit")
    row = await entity_or_404(db, "storage-providers", entity_id)
    current = reveal_mapping(row.payload or {})
    row.payload = protect_mapping(merge_setting(current, body))
    await db.commit()
    await db.refresh(row)
    return {"data": {**stamp(row), **mask_mapping(row.payload or {})}}

@router.delete("/settings/storage/{entity_id}")
async def storage_delete(entity_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    require_permission(user,"settings.storage.configure")
    row = await entity_or_404(db, "storage-providers", entity_id)
    await db.delete(row)
    await db.commit()
    return {"data": {"id": entity_id}}

@router.post("/settings/storage/{entity_id}/test-connection")
async def storage_test(entity_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    require_permission(user,"settings.storage.configure")
    row = await entity_or_404(db, "storage-providers", entity_id)
    from app.modules.storage_integration.providers import test_provider
    result=await test_provider(reveal_mapping(row.payload or {}))
    row.payload = {**(row.payload or {}), "connectionStatus": result["status"], "lastTestedAt": now_iso(), "lastTestMessage": result["message"]}
    await db.commit()
    return {"data": result}

@router.post("/settings/storage/{entity_id}/set-active")
async def storage_active(entity_id: str, body: dict, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    require_permission(user,"settings.storage.configure")
    row = await entity_or_404(db, "storage-providers", entity_id)
    row.payload = {**(row.payload or {}), "active": bool(body.get("active"))}
    await db.commit()
    await db.refresh(row)
    return {"data": {**stamp(row), **mask_mapping(row.payload or {})}}

@router.post("/settings/storage/{entity_id}/set-default")
async def storage_default(entity_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    require_permission(user,"settings.storage.configure")
    rows = (await db.scalars(select(Entity).where(Entity.resource == "storage-providers"))).all()
    for row in rows:
        row.payload = {**(row.payload or {}), "isDefault": str(row.id) == entity_id}
    await db.commit()
    row = await entity_or_404(db, "storage-providers", entity_id)
    return {"data": {**stamp(row), **mask_mapping(row.payload or {})}}

@router.get("/mentions")
async def mentions(q: str = "", type: str = "officer", limit: int = 20, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    resource = {"officer": "officers", "department": "departments", "company": "companies"}.get(type, "officers")
    rows = (await db.scalars(select(Entity).where(Entity.resource == resource, Entity.status == "active", cast(Entity.payload, String).ilike(f"%{q}%")).limit(min(limit, 50)))).all()
    return {"data": [{"id": str(row.id), "label": (row.payload or {}).get("name") or (row.payload or {}).get("title") or str(row.id), "type": type} for row in rows]}

@router.get("/dashboard/summary")
async def dashboard(db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    require_permission(user,"dashboard.view")
    from app.core.cache import short_cache
    cached = await short_cache.get("dashboard:summary")
    if cached:
        return {"data": cached}
    grouped = (await db.execute(select(Entity.resource, func.count()).where(Entity.status.notin_(("archived", "deleted"))).group_by(Entity.resource))).all()
    counts = dict(grouped)
    recent = (await db.scalars(select(Entity).where(Entity.resource == "record-logs").order_by(Entity.created_at.desc()).limit(8))).all()
    data = {
        "totalRecords": sum(counts.get(key, 0) for key in ["incoming-documents", "outgoing-documents", "documents", "master-list-requests"]),
        "incomingDocuments": counts.get("incoming-documents", 0),
        "outgoingDocuments": counts.get("outgoing-documents", 0),
        "documents": counts.get("documents", 0),
        "meetings": counts.get("meeting-history", 0),
        "companies": counts.get("companies", 0),
        "departments": counts.get("departments", 0),
        "users": counts.get("users", 0),
        "recentActivity": [stamp(row) for row in recent],
    }
    await short_cache.set("dashboard:summary", data, 30)
    return {"data": data}

@router.get("/search")
async def search(q: str = "", mode: str = "keyword", limit: int = 12, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    if not q.strip():
        return {"data": []}
    allowed = set(user.permissions or [])
    rows = (await db.scalars(select(Entity).where(Entity.status.notin_(("archived", "deleted")), cast(Entity.payload, String).ilike(f"%{q}%")).order_by(Entity.updated_at.desc()).limit(min(limit, 50)))).all()
    if "ALL_PAGES" not in allowed and user.role not in {"SuperAdmin", "Admin"}:
        rows = [row for row in rows if any(str(row.resource).replace("-", "_") in key for key in allowed)]
    data = []
    for row in rows:
        payload = stamp(row)
        title = payload.get("title") or payload.get("name") or payload.get("fileName") or str(row.id)
        data.append({
            "id": str(row.id),
            "entityType": row.resource,
            "title": title,
            "text": str(payload.get("description") or payload.get("subject") or title),
            "snippet": str(payload.get("description") or title)[:220],
            "url": f"/{row.resource}/{row.id}",
            "permission": "",
            "updatedAt": iso_utc(row.updated_at),
            "score": 1,
            "sourceLabel": row.resource,
        })
    return {"data": data}

@router.post("/search/ask")
async def ask(body: dict, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    hits = await search(str(body.get("q") or ""), "keyword", 5, db, user)
    citations = (hits.get("data") or [])[:5]
    titles = ", ".join(item.get("title") or "" for item in citations) or "no permitted sources"
    return {"data": {"answer": f"Summary for “{body.get('q', '')}” from {titles}. Open each citation to verify.", "citations": citations}}

@router.post("/exports", status_code=202)
async def create_export(body: dict, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    from app.modules.reporting_support.exports import RESOURCE_MAP
    resource=RESOURCE_MAP.get(str(body.get("resource")),str(body.get("resource") or "")); prefix=RESOURCE_PREFIX.get(resource)
    if not prefix: raise HTTPException(422,"Unsupported export resource")
    require_permission(user,f"{prefix}.export")
    if body.get("format") not in {None,"csv"}: raise HTTPException(422,"Only CSV export is supported")
    row = Entity(
        resource="export-jobs",
        payload={**body, "status": "queued", "resource": body.get("resource"), "createdAt": now_iso()},
        status="active",
        created_by=user.id,
        updated_by=user.id,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    data = stamp(row)
    data["status"] = "queued"
    return {"data": data}

@router.get("/exports/{entity_id}")
async def export_status(entity_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    row = await entity_or_404(db, "export-jobs", entity_id)
    if row.created_by!=user.id and user.role not in {"SuperAdmin","Admin"}: raise HTTPException(403,"Export access denied")
    data = stamp(row)
    data["status"] = (row.payload or {}).get("status") or "queued"
    return {"data": data}

@router.delete("/exports/{entity_id}")
async def delete_export(entity_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    row = await entity_or_404(db, "export-jobs", entity_id)
    if row.created_by != user.id and user.role not in {"SuperAdmin", "Admin"}: raise HTTPException(403, "Export access denied")
    object_key = (row.payload or {}).get("objectKey")
    if object_key:
        from app.modules.storage_integration.storage import delete_object
        await delete_object(object_key)
    await db.delete(row); await db.commit()
    return {"data": {"id": entity_id, "deleted": True}}
