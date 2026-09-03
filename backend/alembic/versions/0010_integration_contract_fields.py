"""Integration contract fields: permission scope + vocabulary enum ownership.

Approved additive migration after 0009:

- ``permission.scope`` — ``all | creator`` creator-scope enforcement flag.
  Non-null with default ``all``; existing rows backfill to ``all``.
- ``enum`` vocabulary columns — ``enum_type`` (group), ``label_km``,
  ``color_code``, ``ordering``, ``is_active``, ``version``. Existing
  ``value`` stays the English label; legacy ``code``/``value``/``description``
  are preserved. Global ``code`` uniqueness is replaced by
  ``(enum_type, code)`` uniqueness, existing rows are backfilled to a known
  group deterministically, and the known vocabulary groups are seeded
  idempotently.

Pure definition move — no table added or removed (final count remains 30).
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0010_integration_contract_fields"
down_revision = "0009_org_record_types"


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
        "permission",
        sa.Column("scope", sa.String(20), nullable=False, server_default="all"),
    )

    op.add_column("enum", sa.Column("enum_type", sa.String(80), nullable=False, server_default=""))
    op.add_column("enum", sa.Column("label_km", sa.Text(), nullable=True))
    op.add_column("enum", sa.Column("color_code", sa.String(40), nullable=True))
    op.add_column("enum", sa.Column("ordering", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("enum", sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column("enum", sa.Column("version", sa.Integer(), nullable=False, server_default="1"))

    # Deterministic backfill of legacy rows into the known vocabulary groups.
    op.execute(
        """
        UPDATE enum SET enum_type = CASE
            WHEN code IN ('in_person', 'online', 'hybrid') THEN 'meeting_mode'
            WHEN code IN ('created', 'updated', 'stage_changed', 'shared') THEN 'log_action'
            WHEN code IN ('info', 'warn', 'error') THEN 'severity'
            WHEN code IN (
                'document', 'file', 'master_list_request', 'meeting', 'meeting_topic', 'url',
                'approved_master_list', 'extension_of_validity', 'physical_inspection', 'tax_incentive'
            ) THEN 'entity_type'
            ELSE 'status'
        END
        """
    )

    _drop_code_unique("enum")
    op.create_unique_constraint("uq_enum_type_code", "enum", ["enum_type", "code"])
    op.create_index("ix_enum_enum_type", "enum", ["enum_type"])

    # Seed the known vocabulary groups idempotently (parity with the frontend
    # fallback constants; the `stage` group stays type-specific and dynamic).
    op.execute(
        """
        INSERT INTO enum (id, created_at, updated_at, enum_type, code, value, label_km, color_code, ordering, is_active, version)
        VALUES
            -- status
            (gen_random_uuid(), now(), now(), 'status', 'active', 'Active', 'សកម្ម', 'success', 0, true, 1),
            (gen_random_uuid(), now(), now(), 'status', 'archived', 'Archived', 'ទុកដាក់', 'neutral', 1, true, 1),
            (gen_random_uuid(), now(), now(), 'status', 'deleted', 'Delete', 'លុប', 'error', 2, true, 1),
            -- meeting_mode
            (gen_random_uuid(), now(), now(), 'meeting_mode', 'in_person', 'In person', 'ផ្ទាល់', 'primary', 0, true, 1),
            (gen_random_uuid(), now(), now(), 'meeting_mode', 'online', 'Online', 'អនឡាញ', 'info', 1, true, 1),
            (gen_random_uuid(), now(), now(), 'meeting_mode', 'hybrid', 'Hybrid', 'ចម្រុះ', 'warning', 2, true, 1),
            -- log_action
            (gen_random_uuid(), now(), now(), 'log_action', 'created', 'Created', 'បានបង្កើត', 'success', 0, true, 1),
            (gen_random_uuid(), now(), now(), 'log_action', 'updated', 'Updated', 'បានធ្វើបច្ចុប្បន្នភាព', 'info', 1, true, 1),
            (gen_random_uuid(), now(), now(), 'log_action', 'stage_changed', 'Stage changed', 'បានផ្លាស់ប្តូរដំណាក់កាល', 'warning', 2, true, 1),
            (gen_random_uuid(), now(), now(), 'log_action', 'shared', 'Shared', 'បានចែករំលែក', 'primary', 3, true, 1),
            -- severity
            (gen_random_uuid(), now(), now(), 'severity', 'info', 'Info', 'ព័ត៌មាន', 'info', 0, true, 1),
            (gen_random_uuid(), now(), now(), 'severity', 'warn', 'Warn', 'បម្រុប្រួល', 'warning', 1, true, 1),
            (gen_random_uuid(), now(), now(), 'severity', 'error', 'Error', 'កំហុស', 'error', 2, true, 1),
            -- entity_type
            (gen_random_uuid(), now(), now(), 'entity_type', 'document', 'Document', 'ឯកសារ', 'primary', 0, true, 1),
            (gen_random_uuid(), now(), now(), 'entity_type', 'file', 'File', 'ឯកសារភ្ជាប់', 'neutral', 1, true, 1),
            (gen_random_uuid(), now(), now(), 'entity_type', 'master_list_request', 'Master List Request', 'សំណើបញ្ជីឈ្មោះ', 'info', 2, true, 1),
            (gen_random_uuid(), now(), now(), 'entity_type', 'meeting', 'Meeting', 'កិច្ចប្រជុំ', 'secondary', 3, true, 1),
            (gen_random_uuid(), now(), now(), 'entity_type', 'meeting_topic', 'Meeting Topic', 'ប្រធានបទកិច្ចប្រជុំ', 'secondary', 4, true, 1),
            (gen_random_uuid(), now(), now(), 'entity_type', 'url', 'URL', 'តំណភ្ជាប់', 'neutral', 5, true, 1),
            (gen_random_uuid(), now(), now(), 'entity_type', 'approved_master_list', 'Approved Master List', 'បញ្ជីឈ្មោះអនុម័ត', 'success', 6, true, 1),
            (gen_random_uuid(), now(), now(), 'entity_type', 'extension_of_validity', 'Extension Of Validity', 'ការផ្តាច់ពេលប្រើប្រាស់', 'warning', 7, true, 1),
            (gen_random_uuid(), now(), now(), 'entity_type', 'physical_inspection', 'Physical Inspection', 'ការត្រួតពិនិត្យជាក់លាក់', 'info', 8, true, 1),
            (gen_random_uuid(), now(), now(), 'entity_type', 'tax_incentive', 'Tax Incentive', 'លទ្ធភាពពន្ធ', 'success', 9, true, 1)
        ON CONFLICT (enum_type, code) DO NOTHING
        """
    )


def downgrade() -> None:
    # Seed rows are retained on downgrade (codes remain unique, so re-upgrading
    # is idempotent via ON CONFLICT DO NOTHING); only additive columns are removed.
    op.drop_index("ix_enum_enum_type", table_name="enum")
    op.drop_constraint("uq_enum_type_code", "enum", type_="unique")
    op.create_unique_constraint("uq_enum_code", "enum", ["code"])
    op.drop_column("enum", "version")
    op.drop_column("enum", "is_active")
    op.drop_column("enum", "ordering")
    op.drop_column("enum", "color_code")
    op.drop_column("enum", "label_km")
    op.drop_column("enum", "enum_type")
    op.drop_column("permission", "scope")
