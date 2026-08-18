"""Production identity fields."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
revision="0004_identity_fields"
down_revision="0003_domain_tables"
def upgrade():
    op.add_column("users",sa.Column("officer_id",postgresql.UUID(as_uuid=True)))
    op.add_column("users",sa.Column("status",sa.String(40),nullable=False,server_default="active"))
    op.add_column("users",sa.Column("last_login_at",sa.DateTime(timezone=True)))
    op.add_column("users",sa.Column("updated_at",sa.DateTime(timezone=True),nullable=False,server_default=sa.func.now()))
    op.add_column("users",sa.Column("version",sa.Integer(),nullable=False,server_default="1"))
    op.create_index("ix_users_officer_id","users",["officer_id"],unique=True)
def downgrade():
    op.drop_index("ix_users_officer_id",table_name="users")
    for name in ["version","updated_at","last_login_at","status","officer_id"]: op.drop_column("users",name)
