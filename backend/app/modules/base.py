from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import Activity, Entity, Outbox, User

class EntityService:
    """Shared transaction boundary used by configurable Docetra resources."""
    def __init__(self, db: AsyncSession, user: User, resource: str): self.db,self.user,self.resource=db,user,resource
    async def create(self,payload:dict):
        row=Entity(resource=self.resource,payload=payload,created_by=self.user.id,updated_by=self.user.id); self.db.add(row); await self.db.flush(); self.event(row,"created"); return row
    def event(self,row:Entity,action:str):
        self.db.add(Activity(entity_id=row.id,actor_id=self.user.id,action=action,summary=f"{self.user.name} {action} this record")); self.db.add(Outbox(topic=f"entity.{action}",payload={"resource":self.resource,"id":str(row.id)}))
