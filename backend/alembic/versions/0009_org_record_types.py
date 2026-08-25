"""Organization-scoped record types: join by id, share via record_type_permission."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0009_org_record_types"
down_revision = "0008_drop_document_type"


def _drop_code_unique(table: str) -> None:
    inspector = sa.inspect(op.get_bind())
    for constraint in inspector.get_unique_constraints(table):
        if constraint.get("column_names") == ["code"]:
            op.drop_constraint(constraint["name"], table, type_="unique")
            return
    for index in inspector.get_indexes(table):
        if index.get("unique") and index.get("column_names") == ["code"]:
            op.drop_index(index["name"], table_name=table)
            return


def upgrade() -> None:
    op.add_column(
        "record_detail",
        sa.Column("record_attribute_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index("ix_record_detail_record_attribute_id", "record_detail", ["record_attribute_id"])
    op.create_index("ix_record_detail_record_attr_id", "record_detail", ["record_id", "record_attribute_id"])
    op.create_foreign_key(
        "fk_record_detail_record_attribute_id",
        "record_detail",
        "record_attribute",
        ["record_attribute_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.execute(
        """
        UPDATE record_detail AS detail
        SET record_attribute_id = attr.id
        FROM record_attribute AS attr
        WHERE detail.record_attribute_id IS NULL
          AND detail.record_attribute_code = attr.code
        """
    )
    op.execute(
        """
        UPDATE record AS rec
        SET record_type_id = rtype.id
        FROM record_type AS rtype
        WHERE rec.record_type_id IS NULL
          AND rec.record_type_code = rtype.code
        """
    )

    _drop_code_unique("record_type")
    _drop_code_unique("record_attribute")
    op.create_index("ix_record_type_code_value", "record_type", ["code"])
    op.create_index("ix_record_attribute_code_value", "record_attribute", ["code"])

    op.create_table(
        "record_type_permission",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_by", postgresql.UUID(as_uuid=True)),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True)),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organization.id", ondelete="CASCADE"), nullable=False),
        sa.Column("record_type_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("record_type.id", ondelete="CASCADE"), nullable=False),
        sa.Column("permission_kind", sa.String(20), nullable=False, server_default="shared"),
        sa.UniqueConstraint("organization_id", "record_type_id", name="uq_record_type_permission_org_type"),
    )
    op.create_index("ix_record_type_permission_organization_id", "record_type_permission", ["organization_id"])
    op.create_index("ix_record_type_permission_type", "record_type_permission", ["record_type_id"])
    op.execute(
        """
        CREATE UNIQUE INDEX uq_record_type_permission_one_owner
        ON record_type_permission (record_type_id)
        WHERE permission_kind = 'owner'
        """
    )
    op.execute(
        """
        INSERT INTO record_type_permission (id, organization_id, record_type_id, permission_kind)
        SELECT gen_random_uuid(), org.id, rtype.id, 'shared'
        FROM organization AS org
        CROSS JOIN record_type AS rtype
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_record_type_permission_one_owner")
    op.drop_index("ix_record_type_permission_type", table_name="record_type_permission")
    op.drop_index("ix_record_type_permission_organization_id", table_name="record_type_permission")
    op.drop_table("record_type_permission")
    op.drop_index("ix_record_attribute_code_value", table_name="record_attribute")
    op.drop_index("ix_record_type_code_value", table_name="record_type")
    op.create_unique_constraint("record_attribute_code_key", "record_attribute", ["code"])
    op.create_unique_constraint("record_type_code_key", "record_type", ["code"])
    op.drop_constraint("fk_record_detail_record_attribute_id", "record_detail", type_="foreignkey")
    op.drop_index("ix_record_detail_record_attr_id", table_name="record_detail")
    op.drop_index("ix_record_detail_record_attribute_id", table_name="record_detail")
    op.drop_column("record_detail", "record_attribute_id")
