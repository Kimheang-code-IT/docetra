import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.datetime import iso_utc, utcnow
from app.core.security import person
from app.models.audit import Activity, Comment, Favorite
from app.models.people import User
from app.models.record import Entity, Record
from app.modules.record.domain.map import RECORD_RESOURCES


async def get_neighbors(db: AsyncSession, resource: str, entity_id: str) -> dict:
    from fastapi import HTTPException

    uid = uuid.UUID(entity_id)
    if resource in RECORD_RESOURCES:
        type_code = RECORD_RESOURCES[resource]
        ids = list((await db.scalars(select(Record.id).where(Record.record_type_code == type_code, Record.lifecycle != "deleted").order_by(Record.updated_at.desc()))).all())
    else:
        ids = list((await db.scalars(select(Entity.id).where(Entity.resource == resource, Entity.status != "deleted").order_by(Entity.updated_at.desc()))).all())
    if uid not in ids:
        raise HTTPException(404, "Not found")
    index = ids.index(uid)
    return {"previousId": str(ids[index - 1]) if index else None, "nextId": str(ids[index + 1]) if index + 1 < len(ids) else None}


async def get_favorite(db: AsyncSession, user_id: uuid.UUID, entity_id: str) -> bool:
    row = await db.scalar(select(Favorite).where(Favorite.user_id == user_id, Favorite.entity_id == uuid.UUID(entity_id)))
    return bool(row)


async def set_favorite(db: AsyncSession, user_id: uuid.UUID, entity_id: str, desired: bool) -> bool:
    uid = uuid.UUID(entity_id)
    existing = await db.scalar(select(Favorite).where(Favorite.user_id == user_id, Favorite.entity_id == uid))
    if desired and not existing:
        db.add(Favorite(user_id=user_id, entity_id=uid))
    if not desired and existing:
        await db.delete(existing)
    return desired


async def list_comments(db: AsyncSession, resource: str, entity_id: str, user: User) -> tuple[list[dict], int]:
    rows = (await db.scalars(select(Comment).where(Comment.entity_id == uuid.UUID(entity_id)).order_by(Comment.created_at.desc()))).all()
    authors = (await db.scalars(select(User).where(User.id.in_({row.author_id for row in rows if row.author_id} or {user.id})))).all()
    by_id = {row.id: row for row in authors}
    data = [{
        "id": str(row.id),
        "entityType": resource,
        "entityId": entity_id,
        "body": row.body,
        "author": person(by_id.get(row.author_id) or user),
        "createdAt": iso_utc(row.created_at),
        "editedAt": iso_utc(row.edited_at),
    } for row in rows]
    return data, len(data)


async def add_comment(db: AsyncSession, entity_id: uuid.UUID, body: str, user: User) -> Comment:
    comment = Comment(entity_id=entity_id, body=body, author_id=user.id)
    db.add(comment)
    return comment


async def edit_comment(db: AsyncSession, entity_id: str, comment_id: str, body: str, user: User) -> dict:
    from fastapi import HTTPException

    row = await db.scalar(select(Comment).where(Comment.id == uuid.UUID(comment_id), Comment.entity_id == uuid.UUID(entity_id)))
    if not row:
        raise HTTPException(404, "Comment not found")
    row.body = body
    row.edited_at = utcnow()
    return {
        "id": comment_id,
        "entityId": entity_id,
        "body": row.body,
        "author": person(user),
        "createdAt": iso_utc(row.created_at),
        "editedAt": iso_utc(row.edited_at),
    }


async def delete_comment(db: AsyncSession, entity_id: str, comment_id: str) -> str:
    await db.execute(delete(Comment).where(Comment.id == uuid.UUID(comment_id), Comment.entity_id == uuid.UUID(entity_id)))
    return comment_id


async def list_activity(db: AsyncSession, resource: str, entity_id: str, user: User) -> tuple[list[dict], int]:
    rows = (await db.scalars(select(Activity).where(Activity.entity_id == uuid.UUID(entity_id)).order_by(Activity.occurred_at.desc()))).all()
    data = [{
        "id": str(row.id),
        "entityType": resource,
        "entityId": entity_id,
        "action": row.action,
        "summary": row.summary,
        "actor": person(user),
        "occurredAt": iso_utc(row.occurred_at),
        "metadata": row.metadata_,
    } for row in rows]
    return data, len(rows)
