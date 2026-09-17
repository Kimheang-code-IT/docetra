"""Remove the favorites feature (product decision).

Drops the ``favorites`` join table and all rows. The per-user record
star/favorite endpoints were removed from the API at the same time.
Downgrade recreates the legacy table shape only; rows are not restored.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0012_drop_favorites"
down_revision = "0011_drop_enum_vocabulary"


def upgrade() -> None:
    op.drop_table("favorites")


def downgrade() -> None:
    op.create_table(
        "favorites",
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), primary_key=True),
    )
