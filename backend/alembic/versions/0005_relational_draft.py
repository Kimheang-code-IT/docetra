"""Create draft relational tables alongside Entity JSONB store."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0005_relational_draft"
down_revision = "0004_identity_fields"


def upgrade() -> None:
    op.create_table(
        "role",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_by", postgresql.UUID(as_uuid=True)),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True)),
        sa.Column("nam", sa.String(200), nullable=False, server_default=""),
        sa.Column("lvl", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("description", sa.Text()),
        sa.Column("is_active", sa.SmallInteger(), nullable=False, server_default="0"),
    )
    op.create_table(
        "menu",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_by", postgresql.UUID(as_uuid=True)),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True)),
        sa.Column("parent_code", sa.String(120)),
        sa.Column("code", sa.String(160), nullable=False, unique=True),
        sa.Column("title", sa.String(200), nullable=False, server_default=""),
        sa.Column("icon", sa.String(120)),
        sa.Column("ordering", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_menu", sa.SmallInteger(), nullable=False, server_default="1"),
    )
    op.create_table(
        "permission",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_by", postgresql.UUID(as_uuid=True)),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True)),
        sa.Column("role_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("role.id", ondelete="CASCADE"), nullable=False),
        sa.Column("code", sa.String(160), nullable=False),
        sa.Column("is_enable", sa.SmallInteger(), nullable=False, server_default="0"),
        sa.UniqueConstraint("role_id", "code", name="uq_permission_role_code"),
    )
    op.create_index("ix_permission_role_id", "permission", ["role_id"])
    op.create_index("ix_permission_code", "permission", ["code"])

    op.create_table(
        "organization_sector",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_by", postgresql.UUID(as_uuid=True)),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True)),
        sa.Column("nam", sa.String(200), nullable=False, server_default=""),
        sa.Column("parent_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organization_sector.id", ondelete="SET NULL")),
        sa.Column("description", sa.Text()),
        sa.Column("is_active", sa.SmallInteger(), nullable=False, server_default="0"),
    )
    op.create_table(
        "organization_purpose",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_by", postgresql.UUID(as_uuid=True)),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True)),
        sa.Column("nam", sa.String(200), nullable=False, server_default=""),
        sa.Column("description", sa.Text()),
        sa.Column("is_active", sa.SmallInteger(), nullable=False, server_default="0"),
    )
    op.create_table(
        "organization",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_by", postgresql.UUID(as_uuid=True)),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True)),
        sa.Column("nam", sa.String(200), nullable=False, server_default=""),
        sa.Column("lvl", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("description", sa.Text()),
        sa.Column("is_active", sa.SmallInteger(), nullable=False, server_default="0"),
        sa.Column("parent_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organization.id", ondelete="SET NULL")),
        sa.Column("sector_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organization_sector.id", ondelete="SET NULL")),
        sa.Column("tax_id", sa.String(120)),
        sa.Column("organization_type", sa.String(40), nullable=False, server_default="government"),
        sa.Column("address", sa.Text()),
        sa.Column("contact_info", sa.Text()),
        sa.Column("email", sa.String(320)),
        sa.Column("phone", sa.String(40)),
        sa.Column("organization_purpose_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organization_purpose.id", ondelete="SET NULL")),
        sa.Column("logo_url", sa.String(500)),
        sa.Column("child_ids", sa.Text()),
        sa.Column("code", sa.String(80)),
    )
    op.create_index("ix_organization_organization_type", "organization", ["organization_type"])

    op.create_table(
        "officer",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_by", postgresql.UUID(as_uuid=True)),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True)),
        sa.Column("nam", sa.String(200), nullable=False, server_default=""),
        sa.Column("is_active", sa.SmallInteger(), nullable=False, server_default="0"),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organization.id", ondelete="SET NULL")),
        sa.Column("role_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("role.id", ondelete="SET NULL")),
        sa.Column("auth_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), unique=True),
        sa.Column("profile_url", sa.String(500)),
        sa.Column("email", sa.String(320)),
    )
    op.create_table(
        "officer_identifier",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_by", postgresql.UUID(as_uuid=True)),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True)),
        sa.Column("officer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("officer.id", ondelete="CASCADE"), nullable=False),
        sa.Column("identifier_type", sa.Text(), nullable=False),
        sa.Column("identifier", sa.Text(), nullable=False),
        sa.Column("key1", sa.Text()),
    )
    op.create_index("ix_officer_identifier_officer_id", "officer_identifier", ["officer_id"])

    for col, typ in [
        ("phone", sa.String(40)),
        ("app_metadata", postgresql.JSONB(astext_type=sa.Text())),
        ("user_metadata", postgresql.JSONB(astext_type=sa.Text())),
    ]:
        op.add_column("users", sa.Column(col, typ))

    op.create_table(
        "record_type",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_by", postgresql.UUID(as_uuid=True)),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True)),
        sa.Column("code", sa.String(120), nullable=False, unique=True),
        sa.Column("description", sa.Text()),
        sa.Column("is_active", sa.SmallInteger(), nullable=False, server_default="0"),
        sa.Column("deletable", sa.SmallInteger(), nullable=False, server_default="1"),
        sa.Column("nam", sa.String(200)),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb")),
    )
    op.create_table(
        "record_attribute",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_by", postgresql.UUID(as_uuid=True)),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True)),
        sa.Column("code", sa.String(120), nullable=False, unique=True),
        sa.Column("data_type", sa.String(40), nullable=False, server_default="string"),
        sa.Column("nam", sa.String(200)),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb")),
    )
    op.create_table(
        "record_template",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_by", postgresql.UUID(as_uuid=True)),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True)),
        sa.Column("record_type_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("record_type.id", ondelete="CASCADE"), nullable=False),
        sa.Column("record_attribute_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("record_attribute.id", ondelete="CASCADE"), nullable=False),
        sa.Column("ordering", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_require", sa.SmallInteger(), nullable=False, server_default="0"),
    )
    op.create_table(
        "record_stage_template",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_by", postgresql.UUID(as_uuid=True)),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True)),
        sa.Column("record_type_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("record_type.id", ondelete="CASCADE"), nullable=False),
        sa.Column("ordering", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("nam", sa.String(200), nullable=False, server_default=""),
        sa.Column("is_final", sa.SmallInteger(), nullable=False, server_default="0"),
    )
    op.create_table(
        "file",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_by", postgresql.UUID(as_uuid=True)),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True)),
        sa.Column("nam", sa.String(500), nullable=False, server_default=""),
        sa.Column("path", sa.String(1000), nullable=False, server_default=""),
        sa.Column("file_size", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("mime_type", sa.String(200)),
        sa.Column("storage_type", sa.String(80)),
        sa.Column("direct_url", sa.Text()),
        sa.Column("source_table", sa.String(120)),
        sa.Column("status", sa.String(40), nullable=False, server_default="active"),
    )
    op.create_table(
        "record",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_by", postgresql.UUID(as_uuid=True)),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True)),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("record_type_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("record_type.id", ondelete="SET NULL")),
        sa.Column("title", sa.String(500), nullable=False, server_default=""),
        sa.Column("status", sa.SmallInteger(), nullable=False, server_default="1"),
        sa.Column("record_stage_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("record_stage_template.id", ondelete="SET NULL")),
        sa.Column("record_type_code", sa.String(120)),
        sa.Column("record_content", sa.Text()),
        sa.Column("record_metadata", sa.Text()),
        sa.Column("record_time", sa.DateTime(timezone=True)),
        sa.Column("record_tag", sa.Text()),
        sa.Column("parent_record", postgresql.UUID(as_uuid=True), sa.ForeignKey("record.id", ondelete="SET NULL")),
        sa.Column("record_additional_info", sa.Text()),
        sa.Column("record_flow_code", sa.String(80), nullable=False, server_default="normal"),
        sa.Column("stage", sa.String(100)),
        sa.Column("lifecycle", sa.String(40), nullable=False, server_default="active"),
        sa.Column("archived_at", sa.DateTime(timezone=True)),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_record_type_status_time", "record", ["record_type_id", "status", "record_time"])
    op.create_index("ix_record_type_code", "record", ["record_type_code"])
    op.create_index("ix_record_lifecycle", "record", ["lifecycle"])
    op.create_index("ix_record_record_time", "record", ["record_time"])

    op.create_table(
        "record_detail",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_by", postgresql.UUID(as_uuid=True)),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True)),
        sa.Column("record_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("record.id", ondelete="CASCADE"), nullable=False),
        sa.Column("record_attribute_code", sa.String(120), nullable=False),
        sa.Column("value_number", sa.Numeric()),
        sa.Column("value_string", sa.Text()),
        sa.Column("value_time", sa.DateTime(timezone=True)),
        sa.Column("value_boolean", sa.Boolean()),
        sa.Column("value_json", postgresql.JSONB(astext_type=sa.Text())),
        sa.Column("value_id", postgresql.UUID(as_uuid=True)),
    )
    op.create_index("ix_record_detail_record_attr", "record_detail", ["record_id", "record_attribute_code"])

    op.create_table(
        "record_attachment",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_by", postgresql.UUID(as_uuid=True)),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True)),
        sa.Column("record_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("record.id", ondelete="CASCADE"), nullable=False),
        sa.Column("reference_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("record.id", ondelete="SET NULL")),
        sa.Column("file_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("file.id", ondelete="SET NULL")),
    )
    op.create_table(
        "record_organization",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_by", postgresql.UUID(as_uuid=True)),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True)),
        sa.Column("record_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("record.id", ondelete="CASCADE"), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organization.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role_type", sa.String(40), nullable=False, server_default="participant"),
    )

    op.create_table(
        "setting",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_by", postgresql.UUID(as_uuid=True)),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True)),
        sa.Column("key_group", sa.String(120), nullable=False),
        sa.Column("key", sa.String(160), nullable=False),
        sa.Column("description", sa.String(500)),
        sa.Column("data_type", sa.String(40), nullable=False, server_default="string"),
        sa.Column("public_access", sa.SmallInteger(), nullable=False, server_default="0"),
        sa.Column("visible", sa.SmallInteger(), nullable=False, server_default="0"),
        sa.Column("ordering", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("key_value", sa.Text()),
        sa.UniqueConstraint("key_group", "key", name="uq_setting_group_key"),
    )
    op.create_index("ix_setting_key_group", "setting", ["key_group"])

    op.create_table(
        "document_type",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_by", postgresql.UUID(as_uuid=True)),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True)),
        sa.Column("nam", sa.String(200), nullable=False, unique=True),
        sa.Column("description", sa.Text()),
        sa.Column("is_active", sa.SmallInteger(), nullable=False, server_default="0"),
        sa.Column("color_code", sa.String(40)),
    )
    op.create_table(
        "enum",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_by", postgresql.UUID(as_uuid=True)),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True)),
        sa.Column("code", sa.Text(), nullable=False, unique=True),
        sa.Column("value", sa.Text(), nullable=False, server_default=""),
        sa.Column("description", sa.Text()),
    )

    op.create_table(
        "audit_log",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("officer.id", ondelete="SET NULL")),
        sa.Column("action_code", sa.String(120), nullable=False),
        sa.Column("table_name", sa.String(120), nullable=False),
        sa.Column("row_id", postgresql.UUID(as_uuid=True)),
        sa.Column("detail_data", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb")),
        sa.Column("ip_address", sa.Text()),
        sa.Column("status_code", sa.String(40), nullable=False, server_default="success"),
        sa.Column("source_log", sa.String(80), nullable=False, server_default="unknown"),
        sa.Column("raw_text", sa.Text()),
        sa.Column("message", sa.Text()),
    )
    op.create_index("ix_audit_log_row_id", "audit_log", ["row_id"])
    op.create_table(
        "notification_audit_log",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("log_id", sa.BigInteger(), sa.ForeignKey("audit_log.id", ondelete="SET NULL")),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb")),
        sa.Column("processed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )

    # Soften comments/favorites FKs off entities so Phase 6 can drop entities while keeping collaboration rows
    op.drop_constraint("comments_entity_id_fkey", "comments", type_="foreignkey")
    op.drop_constraint("activities_entity_id_fkey", "activities", type_="foreignkey")
    op.drop_constraint("favorites_entity_id_fkey", "favorites", type_="foreignkey")


def downgrade() -> None:
    op.create_foreign_key("favorites_entity_id_fkey", "favorites", "entities", ["entity_id"], ["id"], ondelete="CASCADE")
    op.create_foreign_key("activities_entity_id_fkey", "activities", "entities", ["entity_id"], ["id"], ondelete="CASCADE")
    op.create_foreign_key("comments_entity_id_fkey", "comments", "entities", ["entity_id"], ["id"], ondelete="CASCADE")
    for table in [
        "notification_audit_log", "audit_log", "enum", "document_type", "setting",
        "record_organization", "record_attachment", "record_detail", "record", "file",
        "record_stage_template", "record_template", "record_attribute", "record_type",
        "officer_identifier", "officer", "organization", "organization_purpose", "organization_sector",
        "permission", "menu", "role",
    ]:
        op.drop_table(table)
    for col in ["user_metadata", "app_metadata", "phone"]:
        op.drop_column("users", col)
