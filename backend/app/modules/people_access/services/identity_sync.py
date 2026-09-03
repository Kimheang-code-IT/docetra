"""Legacy Entity → projection sync.

Projection tables (`records`, `organizations`, `officers`, `roles`) were dropped in
Alembic 0006. Typed tables are written directly by CollectionService; this module
is retained only so Entity-era side-effect call sites stay import-safe.
"""

from sqlalchemy.ext.asyncio import AsyncSession

async def sync_domain_row(db: AsyncSession, row: object) -> None:
    return

