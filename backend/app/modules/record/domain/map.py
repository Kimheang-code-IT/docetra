"""Maps frontend API collection resources to record types.

`RECORD_RESOURCES` is a legacy alias map (hyphenated collection paths → type codes).
Prefer resolving by `type_code` via `/api/v2/records/{type_code}` and TYPE_UI_DEFAULTS.

Organization maps live in `organization.domain.map` and are re-exported here for older imports.
"""

from __future__ import annotations

import re

from app.modules.organization.domain.map import (
    LEGACY_ORG_RESOURCES,
    ORG_LOOKUP_RESOURCES,
    ORG_RESOURCES,
    ORG_TYPE_META,
    ORG_TYPE_TO_RESOURCE,
    ORG_TYPES,
    RESERVED_ORG_SEGMENTS,
    db_org_type_for,
    is_valid_org_type,
    permission_prefix_for_org_type,
)

RECORD_RESOURCES: dict[str, str] = {
    "incoming-documents": "incoming_document",
    "outgoing-documents": "outgoing_document",
    "documents": "document",
    "master-list-requests": "master_list_request",
    "meeting-topics": "meeting_topic",
    "meeting-history": "meeting_history",
}

TYPE_CODE_TO_RESOURCE: dict[str, str] = {code: resource for resource, code in RECORD_RESOURCES.items()}

# Built-in type → UI shell + menu hints (stored on record_type.payload).
TYPE_UI_DEFAULTS: dict[str, dict] = {
    "meeting_history": {
        "uiSurface": "meeting",
        "slug": "history",
        "icon": "i-lucide-calendar-clock",
        "menuOrder": 20,
        "isCreatable": True,
        "supportsStages": True,
        "supportsTopicContainer": False,
    },
    "meeting_topic": {
        "uiSurface": "meeting",
        "slug": "topics",
        "icon": "i-lucide-folders",
        "menuOrder": 10,
        "isCreatable": True,
        "supportsStages": True,
        "supportsTopicContainer": True,
    },
    "document": {
        "uiSurface": "document",
        "slug": "documents",
        "icon": "i-lucide-file-text",
        "menuOrder": 30,
        "isCreatable": True,
        "supportsStages": True,
        "supportsTopicContainer": False,
    },
    "incoming_document": {
        "uiSurface": "document",
        "slug": "incoming-documents",
        "icon": "i-lucide-file-input",
        "menuOrder": 10,
        "isCreatable": True,
        "supportsStages": True,
        "supportsTopicContainer": False,
    },
    "outgoing_document": {
        "uiSurface": "document",
        "slug": "outgoing-documents",
        "icon": "i-lucide-file-output",
        "menuOrder": 20,
        "isCreatable": True,
        "supportsStages": True,
        "supportsTopicContainer": False,
    },
    "master_list_request": {
        "uiSurface": "document",
        "slug": "master-list-requests",
        "icon": "i-lucide-list-checks",
        "menuOrder": 40,
        "isCreatable": True,
        "supportsStages": True,
        "supportsTopicContainer": False,
    },
}

TYPE_CODE_PATTERN = re.compile(r"^[a-z][a-z0-9_]{1,63}$")
RESERVED_RECORD_SEGMENTS = frozenset({"_meta", "logs", "schema"})

LIFECYCLE_TO_STATUS = {"active": 1, "archived": 2, "deleted": 0}
STATUS_TO_LIFECYCLE = {1: "active", 2: "archived", 0: "deleted"}

CORE_RECORD_KEYS = {
    "id", "title", "status", "stage", "recordTime", "recordTypeCode", "recordType",
    "recordContent", "recordTag", "tags", "parentRecord", "parentId", "version",
    "createdAt", "updatedAt", "archivedAt", "deletedAt", "recordFlowCode",
    "recordMetadata", "recordAdditionalInfo", "recordStageId",
}


def is_valid_type_code(code: str) -> bool:
    return bool(code and TYPE_CODE_PATTERN.match(code) and code not in RESERVED_RECORD_SEGMENTS)


def permission_prefix_for_type_code(type_code: str) -> str:
    """Map type code to capability prefix. Meeting types use records.* only (no meetings.*)."""
    resource = TYPE_CODE_TO_RESOURCE.get(type_code)
    if resource == "meeting-topics":
        return "records.meeting_topic"
    if resource == "meeting-history":
        return "records.meeting_history"
    if resource == "incoming-documents":
        return "records.incoming_documents"
    if resource == "outgoing-documents":
        return "records.outgoing_documents"
    if resource == "documents":
        return "records.documents"
    if resource == "master-list-requests":
        return "records.master_list_requests"
    return f"records.{type_code}"


def merge_type_ui_payload(code: str, payload: dict | None) -> dict:
    base = dict(TYPE_UI_DEFAULTS.get(code) or {
        "uiSurface": "document",
        "slug": code.replace("_", "-"),
        "icon": "i-lucide-file",
        "menuOrder": 100,
        "isCreatable": True,
        "supportsStages": True,
        "supportsTopicContainer": False,
    })
    if payload:
        base.update({k: v for k, v in payload.items() if v is not None})
    return base
