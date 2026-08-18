import csv
import json
import uuid
from datetime import datetime, timedelta, timezone
from io import StringIO
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import Entity
from app.modules.storage_integration.storage import put_bytes

RESOURCE_MAP={
 "meetingTopics":"meeting-topics","meetingHistory":"meeting-history","incomingDocuments":"incoming-documents",
 "outgoingDocuments":"outgoing-documents","documents":"documents","masterListRequests":"master-list-requests",
 "recordLogs":"record-logs","departments":"departments","companies":"companies","companyPurposes":"company-purposes",
 "companySectors":"company-sectors","officers":"officers","roles":"roles","users":"users","recordTypes":"record-types",
 "recordAttributes":"record-attributes","fileUploads":"file-uploads","googleDriveSync":"google-drive-sync","portalLogs":"portal-logs","systemLogs":"system-logs"}

def _cell(value):
    if value is None:return ""
    if isinstance(value,(dict,list)):return json.dumps(value,ensure_ascii=False,default=str)
    return str(value)

async def generate_export(db:AsyncSession,job:Entity)->None:
    payload=dict(job.payload or {}); resource=RESOURCE_MAP.get(str(payload.get("resource")),str(payload.get("resource") or ""))
    if not resource: raise ValueError("Export resource is required")
    stmt=select(Entity).where(Entity.resource==resource,Entity.status!="deleted")
    selected=payload.get("selectedIds") or []
    if payload.get("scope")=="selected":
        ids=[]
        for raw in selected[:5000]:
            try: ids.append(uuid.UUID(str(raw)))
            except ValueError: pass
        stmt=stmt.where(Entity.id.in_(ids))
    rows=(await db.scalars(stmt.order_by(Entity.updated_at.desc()).limit(10000))).all()
    fields=[str(x) for x in payload.get("fieldCodes") or [] if str(x) not in {"password","passwordHash","secret","token","objectKey"}]
    if not fields:
        fields=sorted({key for row in rows for key in (row.payload or {}).keys() if key not in {"password","passwordHash","secret","token","objectKey"}})
    fields=["id",*fields]
    output=StringIO(newline=""); writer=csv.DictWriter(output,fieldnames=fields,extrasaction="ignore"); writer.writeheader()
    for row in rows:
        values={"id":str(row.id),**(row.payload or {}),"status":row.status,"stage":row.stage,"createdAt":row.created_at.isoformat(),"updatedAt":row.updated_at.isoformat()}
        writer.writerow({key:_cell(values.get(key)) for key in fields})
    data=output.getvalue().encode("utf-8-sig"); filename=f"{resource}-{datetime.now(timezone.utc):%Y%m%d-%H%M%S}.csv"; key=f"exports/{job.id}/{filename}"
    await put_bytes(key,data,"text/csv; charset=utf-8")
    payload.update({"status":"completed","objectKey":key,"fileName":filename,"mimeType":"text/csv","sizeBytes":len(data),"downloadUrl":f"/api/v2/files/{job.id}","completedAt":datetime.now(timezone.utc).isoformat(),"expiresAt":(datetime.now(timezone.utc)+timedelta(hours=24)).isoformat()})
    job.payload=payload
