import uuid

from fastapi import HTTPException
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.datetime import iso_utc, utcnow
from app.core.privileged import is_unrestricted
from app.modules.people_access.dependencies import person
from app.modules.record.model import Activity, Comment, Favorite
from app.modules.record.model import Entity, Record
from app.modules.people_access.service import public_users_by_ids
from app.modules.record.domain.map import RECORD_RESOURCES


def assert_comment_author_or_unrestricted(row: Comment, user: object) -> None:
    if row.author_id and str(row.author_id) == str(user.id):
        return
    if is_unrestricted(user):
        return
    raise HTTPException(403, "Only the author can modify this comment")


async def get_neighbors(db: AsyncSession, resource: str, entity_id: str) -> dict:
    uid = uuid.UUID(entity_id)
    if resource in RECORD_RESOURCES:
        current = await db.get(Record, uid)
        if not current:
            raise HTTPException(404, "Not found")
        if current.record_type_id:
            ids = list((await db.scalars(
                select(Record.id).where(
                    Record.record_type_id == current.record_type_id,
                    Record.lifecycle != "deleted",
                ).order_by(Record.updated_at.desc())
            )).all())
        else:
            type_code = RECORD_RESOURCES[resource]
            ids = list((await db.scalars(
                select(Record.id).where(Record.record_type_code == type_code, Record.lifecycle != "deleted").order_by(Record.updated_at.desc())
            )).all())
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


async def list_comments(db: AsyncSession, resource: str, entity_id: str, user: object) -> tuple[list[dict], int]:
    rows = (await db.scalars(select(Comment).where(Comment.entity_id == uuid.UUID(entity_id)).order_by(Comment.created_at.desc()))).all()
    by_id = await public_users_by_ids(db, {row.author_id for row in rows if row.author_id})
    data = [{
        "id": str(row.id),
        "entityType": resource,
        "entityId": entity_id,
        "body": row.body,
        "author": by_id.get(row.author_id) or person(user),
        "createdAt": iso_utc(row.created_at),
        "editedAt": iso_utc(row.edited_at),
    } for row in rows]
    return data, len(data)


async def add_comment(db: AsyncSession, entity_id: uuid.UUID, body: str, user: object) -> Comment:
    comment = Comment(entity_id=entity_id, body=body, author_id=user.id)
    db.add(comment)
    return comment


async def edit_comment(db: AsyncSession, entity_id: str, comment_id: str, body: str, user: object) -> dict:
    row = await db.scalar(select(Comment).where(Comment.id == uuid.UUID(comment_id), Comment.entity_id == uuid.UUID(entity_id)))
    if not row:
        raise HTTPException(404, "Comment not found")
    assert_comment_author_or_unrestricted(row, user)
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


async def delete_comment(db: AsyncSession, entity_id: str, comment_id: str, user: object) -> str:
    row = await db.scalar(select(Comment).where(Comment.id == uuid.UUID(comment_id), Comment.entity_id == uuid.UUID(entity_id)))
    if not row:
        raise HTTPException(404, "Comment not found")
    assert_comment_author_or_unrestricted(row, user)
    await db.execute(delete(Comment).where(Comment.id == row.id))
    return comment_id


async def list_activity(db: AsyncSession, resource: str, entity_id: str, user: object) -> tuple[list[dict], int]:
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
