import secrets
import uuid
from datetime import datetime,timezone
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.permissions import normalize_permission_payload
from app.core.security import hash_password,redis
from app.db import Entity,User

async def prepare_payload(db:AsyncSession,resource:str,payload:dict,current:Entity|None=None)->dict:
    data=dict(payload)
    if resource=="roles":
        try: data=normalize_permission_payload(data)
        except ValueError as exc: raise HTTPException(422,str(exc))
        code=str(data.get("code","")).strip().upper()
        if not code or not str(data.get("name","")).strip(): raise HTTPException(422,"Role code and name are required")
        duplicate=await db.scalar(select(Entity).where(Entity.resource=="roles",Entity.payload["code"].as_string()==code,Entity.id!=(current.id if current else uuid.UUID(int=0))))
        if duplicate: raise HTTPException(409,"Role code already exists")
        data["code"]=code
    if resource=="users":
        email=str(data.get("email","")).strip().lower(); name=str(data.get("name","")).strip()
        if not email or "@" not in email or not name: raise HTTPException(422,"A valid email and name are required")
        existing=await db.scalar(select(User).where(User.email==email,User.id!=(current.id if current else uuid.UUID(int=0))))
        if existing: raise HTTPException(409,"User email already exists")
        data["email"],data["name"]=email,name
        data.pop("password",None); data.pop("passwordConfirmation",None)
    return data

async def sync_identity(db:AsyncSession,entity:Entity,raw_payload:dict,creating:bool):
    if entity.resource=="users":
        account=await db.get(User,entity.id); role_id=entity.payload.get("roleId"); role=None
        if role_id:
            try: role=await db.scalar(select(Entity).where(Entity.id==uuid.UUID(str(role_id)),Entity.resource=="roles",Entity.status=="active"))
            except ValueError: pass
            if not role: raise HTTPException(422,"Assigned role does not exist or is inactive")
        if creating:
            password=str(raw_payload.get("password") or secrets.token_urlsafe(24))
            account=User(id=entity.id,email=entity.payload["email"],name=entity.payload["name"],password_hash=hash_password(password))
            db.add(account)
        account.email=entity.payload["email"]; account.name=entity.payload["name"]; account.role_id=role.id if role else None
        account.role=role.payload.get("name","User") if role else entity.payload.get("roleName","User")
        account.permissions=role.payload.get("permissions",[]) if role else []
        account.officer_id=uuid.UUID(str(entity.payload["officerId"])) if entity.payload.get("officerId") else None
        account.status=entity.status; account.active=entity.status in {"active","draft"}; account.updated_at=datetime.now(timezone.utc); account.version=entity.version
        entity.payload={**entity.payload,"roleId":str(role.id) if role else None,"roleName":role.payload.get("name") if role else account.role,"lastLoginAt":account.last_login_at.isoformat() if account.last_login_at else None}
        if not account.active: await revoke_user_sessions(account.id)
    elif entity.resource=="roles":
        users=(await db.scalars(select(User).where(User.role_id==entity.id))).all()
        for account in users:
            account.permissions=entity.payload.get("permissions",[]); account.role=entity.payload.get("name","User"); account.version+=1; await revoke_user_sessions(account.id)

async def revoke_user_sessions(user_id:uuid.UUID):
    async for key in redis.scan_iter("session:*"):
        value=await redis.get(key)
        if value and str(user_id) in value: await redis.delete(key)
