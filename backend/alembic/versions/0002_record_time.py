"""Add record_time for list/export date filters."""
from alembic import op
import sqlalchemy as sa

revision = "0002_record_time"
down_revision = "0001_initial"

def upgrade():
    op.add_column("entities", sa.Column("record_time", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_entities_record_time", "entities", ["record_time"])

def downgrade():
    op.drop_index("ix_entities_record_time", table_name="entities")
    op.drop_column("entities", "record_time")
