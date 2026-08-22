"""Drop unused document_type table; types live in record_type only."""

from alembic import op

revision = "0008_drop_document_type"
down_revision = "0007_user_actor_fields"


def upgrade() -> None:
    op.drop_table("document_type")


def downgrade() -> None:
    import sqlalchemy as sa
    from sqlalchemy.dialects import postgresql

    op.create_table(
        "document_type",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("nam", sa.String(200), unique=True, nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("color_code", sa.String(40), nullable=True),
        sa.Column("is_active", sa.SmallInteger(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
    )
