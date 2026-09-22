"""Freeze public HTTP and database structure while modules are reorganized."""

from __future__ import annotations

import hashlib
import json

import app.db.metadata  # noqa: F401 - populate SQLAlchemy metadata from the canonical registry
from app.db.base import Base
from app.main import app


# Route count grew from 375 with the approved integration additions:
#   POST   /records/{type_code}/{entity_id}/attachments/upload  (multipart upload + attach)
#   DELETE /records/{type_code}/{entity_id}/attachments/{file_id} (detach without deleting the File)
#   POST /configuration/record-{types,attributes}/{id}/duplicate, PATCH .../status  (Phase 5 UI actions)
# Shrank from 386 when the vocabulary feature was removed by product decision (migration 0011).
# Shrank from 381 when the favorites feature was removed by product decision (migration 0012):
#   GET/PUT /{base}/{id}/favorite across record, organization, and configuration routers.
# Grew from 355 with the approved Telegram notification additions:
#   POST /settings/app-config/telegram/discover-chats (detect chat IDs via getUpdates).
# Grew from 356 with the approved portal storage readiness endpoint:
#   GET /portal/storage-status (file storage + Google Drive readiness for portal pages).
# Shrank from 357 when the App Info settings feature was removed by product decision:
#   GET/PATCH/PUT /settings/app-info and POST /settings/app-info/reset.
ROUTE_MANIFEST_SHA256 = "e65c11328c93a9457aecd0a2996d79f9d6d0b25da619bf6f9ac372ccc1a84a6b"
# Updated for the approved 0010_integration_contract_fields migration:
# permission.scope (enum vocabulary columns later removed by 0011).
# 0011_drop_enum_vocabulary removed the `enum` table (30 → 29).
# 0012_drop_favorites removed the `favorites` table (29 → 28).
# 0013_hot_path_indexes added indexes on officer.organization_id,
# record_organization.*, record_attachment.record_id, comments/activities.entity_id,
# record.created_by/updated_by, record_template/record_stage_template.record_type_id,
# and record(record_type_id, updated_at).
METADATA_MANIFEST_SHA256 = "d39dc0bd2c05e571887a82139bfae399e4ecdecf457492d48e8b621850b0f0a5"


def _digest(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def _route_manifest() -> list[list[object]]:
    result: list[list[object]] = []
    for route in app.routes:
        methods = sorted(
            method
            for method in (getattr(route, "methods", None) or ())
            if method not in {"HEAD", "OPTIONS"}
        )
        if methods:
            result.append([route.path, methods, route.name])
    return result


def _metadata_manifest() -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    for name, table in sorted(Base.metadata.tables.items()):
        constraints = []
        for constraint in table.constraints:
            constraints.append(
                [
                    type(constraint).__name__,
                    constraint.name,
                    sorted(column.name for column in getattr(constraint, "columns", ())),
                    sorted(
                        element.target_fullname
                        for element in getattr(constraint, "elements", ())
                    ),
                ]
            )
        indexes = [
            [index.name, index.unique, sorted(column.name for column in index.columns)]
            for index in table.indexes
        ]
        result.append(
            {
                "table": name,
                "columns": [
                    [column.name, str(column.type), column.nullable, column.primary_key]
                    for column in table.columns
                ],
                "constraints": sorted(constraints, key=str),
                "indexes": sorted(indexes, key=str),
            }
        )
    return result


def test_route_manifest_is_unchanged() -> None:
    assert len(_route_manifest()) == 353
    assert _digest(_route_manifest()) == ROUTE_MANIFEST_SHA256


def test_sqlalchemy_metadata_is_unchanged() -> None:
    assert len(_metadata_manifest()) == 28
    assert _digest(_metadata_manifest()) == METADATA_MANIFEST_SHA256
