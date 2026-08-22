"""Add users.created_by / users.updated_by for officer actor refs."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0007_user_actor_fields"
down_revision = "0006_drop_legacy_projections"


def upgrade() -> None:
    op.add_column("users", sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("users", sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_index("ix_users_created_by", "users", ["created_by"])
    op.create_index("ix_users_updated_by", "users", ["updated_by"])
    op.create_index("ix_users_role_id", "users", ["role_id"])


def downgrade() -> None:
    op.drop_index("ix_users_role_id", table_name="users")
    op.drop_index("ix_users_updated_by", table_name="users")
    op.drop_index("ix_users_created_by", table_name="users")
    op.drop_column("users", "updated_by")
    op.drop_column("users", "created_by")
