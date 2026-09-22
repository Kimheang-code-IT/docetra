"""Add indexes for hot read paths (org-scoped lists, collaboration, default sort).

Models declared ``index=True`` on these columns but no migration ever created
the indexes, so org-scoped record lists, comment/activity panels, and the
default ``updated_at`` sort were doing sequential scans. Additive only.
"""

from alembic import op

revision = "0013_hot_path_indexes"
down_revision = "0012_drop_favorites"


_INDEXES: list[tuple[str, str, list[str]]] = [
    ("ix_officer_organization_id", "officer", ["organization_id"]),
    ("ix_record_organization_record_id", "record_organization", ["record_id"]),
    ("ix_record_organization_organization_id", "record_organization", ["organization_id"]),
    ("ix_record_attachment_record_id", "record_attachment", ["record_id"]),
    ("ix_comments_entity_id", "comments", ["entity_id"]),
    ("ix_activities_entity_id", "activities", ["entity_id"]),
    ("ix_record_created_by", "record", ["created_by"]),
    ("ix_record_updated_by", "record", ["updated_by"]),
    ("ix_record_template_record_type_id", "record_template", ["record_type_id"]),
    ("ix_record_stage_template_record_type_id", "record_stage_template", ["record_type_id"]),
    ("ix_record_type_updated_at", "record", ["record_type_id", "updated_at"]),
]


def upgrade() -> None:
    for name, table, columns in _INDEXES:
        op.create_index(name, table, columns)


def downgrade() -> None:
    for name, table, _ in reversed(_INDEXES):
        op.drop_index(name, table_name=table)
