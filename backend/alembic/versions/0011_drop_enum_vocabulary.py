"""Remove the vocabulary (enum) feature entirely — dropped by product decision.

Removes the ``enum`` table added to by 0001/0010 (vocabulary columns + seeds).
The ``permission.scope`` column added by 0010 is intentionally kept.
Downgrade recreates the table in its **0010 shape** (vocabulary columns,
``(enum_type, code)`` uniqueness and the ``enum_type`` index) so that the
``0010`` downgrade that follows can drop them cleanly; seeded data is not
restored.
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
        # 0010 vocabulary columns (must exist for the 0010 downgrade to remove).
        sa.Column("enum_type", sa.String(80), nullable=False, server_default=""),
        sa.Column("label_km", sa.Text(), nullable=True),
        sa.Column("color_code", sa.String(40), nullable=True),
        sa.Column("ordering", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.UniqueConstraint("enum_type", "code", name="uq_enum_type_code"),
    )
    op.create_index("ix_enum_enum_type", "enum", ["enum_type"])
