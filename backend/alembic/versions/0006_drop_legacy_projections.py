"""Drop legacy Entity-era projection tables after relational cutover.

Run scripts/migrate_entities_to_relational.py and verify before applying.
`entities` is retained until google-drive-sync is fully on typed tables.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0006_drop_legacy_projections"
down_revision = "0005_relational_draft"


def upgrade() -> None:
    for table in ("records", "organizations", "officers", "roles"):
        op.execute(sa.text(f"DROP TABLE IF EXISTS {table} CASCADE"))


def downgrade() -> None:
    op.create_table(
        "roles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(80), unique=True),
        sa.Column("name", sa.String(200)),
        sa.Column("permissions", postgresql.JSONB()),
        sa.Column("payload", postgresql.JSONB()),
        sa.Column("status", sa.String(40)),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )
