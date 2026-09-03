"""Remove the vocabulary (enum) feature entirely — dropped by product decision.

Removes the ``enum`` table added to by 0001/0010 (vocabulary columns + seeds).
The ``permission.scope`` column added by 0010 is intentionally kept.
Downgrade recreates the legacy table shape only; seeded data is not restored.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0011_drop_enum_vocabulary"
down_revision = "0010_integration_contract_fields"


def upgrade() -> None:
    op.drop_index("ix_enum_enum_type", table_name="enum")
    op.drop_table("enum")


def downgrade() -> None:
    op.create_table(
        "enum",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_by", postgresql.UUID(as_uuid=True)),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True)),
        sa.Column("code", sa.Text(), nullable=False),
        sa.Column("value", sa.Text(), nullable=False, server_default=""),
        sa.Column("description", sa.Text(), nullable=True),
        sa.UniqueConstraint("code", name="uq_enum_code"),
    )
