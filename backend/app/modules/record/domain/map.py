"""Maps frontend API collection resources to record types.

`RECORD_RESOURCES` is a legacy alias map (hyphenated collection paths → type codes).
Prefer resolving by `type_code` via `/api/v2/records/{type_code}` and TYPE_UI_DEFAULTS.

Organization maps live exclusively in `organization.domain.map`.
"""

from __future__ import annotations

import re

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

DEFAULT_RECORD_TYPE_FEATURES = {
    "allowAttachments": True,
    "allowComments": True,
    "allowAssignment": True,
    "allowSharing": False,
    "allowRelatedRecords": True,
    "enableWorkflow": True,
    "enableDueDate": True,
    "enableHistory": True,
    "enableExport": True,
}

TYPE_NUMBERING_PREFIX = {
    "incoming_document": "INC",
    "outgoing_document": "OUT",
    "document": "DOC",
    "master_list_request": "MLR",
    "meeting_history": "MTG",
    "meeting_topic": "TPC",
}

DOCUMENT_WORKFLOW_STAGES = [
    {"id": "created", "code": "created", "name": "Created", "color": "neutral", "isInitial": True, "isFinal": False, "order": 1},
    {"id": "record_created", "code": "record_created", "name": "Record created", "color": "info", "isInitial": False, "isFinal": False, "order": 2},
    {"id": "observation_note", "code": "observation_note", "name": "Observation note", "color": "warning", "isInitial": False, "isFinal": False, "order": 3},
    {"id": "waiting_related_document", "code": "waiting_related_document", "name": "Waiting related document", "color": "warning", "isInitial": False, "isFinal": False, "order": 4},
    {"id": "submitted_director", "code": "submitted_director", "name": "Submitted to director", "color": "primary", "isInitial": False, "isFinal": False, "order": 5},
    {"id": "submitted_ddg", "code": "submitted_ddg", "name": "Submitted to DDG", "color": "primary", "isInitial": False, "isFinal": False, "order": 6},
    {"id": "submitted_dg", "code": "submitted_dg", "name": "Submitted to DG", "color": "primary", "isInitial": False, "isFinal": False, "order": 7},
    {"id": "further_measures", "code": "further_measures", "name": "Further measures", "color": "info", "isInitial": False, "isFinal": False, "order": 8},
    {"id": "reply", "code": "reply", "name": "Reply", "color": "success", "isInitial": False, "isFinal": False, "order": 9},
    {"id": "finished_final", "code": "finished_final", "name": "Finished / Final", "color": "success", "isInitial": False, "isFinal": True, "order": 10},
]

MEETING_WORKFLOW_STAGES = [
    {"id": "intake", "code": "intake", "name": "Intake", "color": "info", "isInitial": True, "isFinal": False, "order": 1},
    {"id": "review", "code": "review", "name": "Review", "color": "warning", "isInitial": False, "isFinal": False, "order": 2},
    {"id": "approval", "code": "approval", "name": "Approval", "color": "primary", "isInitial": False, "isFinal": False, "order": 3},
    {"id": "completed", "code": "completed", "name": "Completed", "color": "success", "isInitial": False, "isFinal": True, "order": 4},
]

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


def resolve_type_code(code: str) -> str:
    """Normalize a UI/API type code or legacy hyphenated collection path."""
    raw = str(code or "").strip()
    if not raw:
        return raw
    if raw in TYPE_UI_DEFAULTS:
        return raw
    if raw in RECORD_RESOURCES:
        return RECORD_RESOURCES[raw]
    normalized = raw.replace("-", "_")
    if normalized in TYPE_UI_DEFAULTS:
        return normalized
    return normalized if is_valid_type_code(normalized) else raw


def default_numbering_for_type(code: str) -> dict:
    prefix = TYPE_NUMBERING_PREFIX.get(code) or (code[:3].upper() if code else "REC")
    return {
        "prefix": prefix,
        "includeYear": True,
        "sequenceLength": 6,
        "resetYearly": True,
    }


def default_workflow_stages_for_type(code: str, ui_surface: str | None = None) -> list[dict]:
    surface = ui_surface or (TYPE_UI_DEFAULTS.get(code) or {}).get("uiSurface") or "document"
    source = MEETING_WORKFLOW_STAGES if surface == "meeting" else DOCUMENT_WORKFLOW_STAGES
    return [dict(stage) for stage in source]


def sequential_transitions(stages: list[dict]) -> list[dict]:
    transitions = []
    for index, stage in enumerate(stages[:-1]):
        nxt = stages[index + 1]
        from_code = str(stage.get("code") or "")
        to_code = str(nxt.get("code") or "")
        transitions.append({
            "id": f"{from_code}_to_{to_code}",
            "fromStageCode": from_code,
            "toStageCode": to_code,
        })
    return transitions


def normalize_workflow_stages(raw) -> list[dict]:
    stages = []
    if not isinstance(raw, list):
        return stages
    for index, item in enumerate(raw):
        if not isinstance(item, dict):
            continue
        code = str(item.get("code") or item.get("id") or f"stage_{index + 1}")
        stages.append({
            "id": str(item.get("id") or code),
            "code": code,
            "name": str(item.get("name") or item.get("label") or code.replace("_", " ").title()),
            "color": item.get("color"),
            "isInitial": bool(item.get("isInitial")) if "isInitial" in item else index == 0,
            "isFinal": bool(item.get("isFinal")) if "isFinal" in item else False,
            "order": int(item["order"]) if item.get("order") is not None else index + 1,
        })
    if stages and not any(stage["isInitial"] for stage in stages):
        stages[0]["isInitial"] = True
    if stages and not any(stage["isFinal"] for stage in stages):
        stages[-1]["isFinal"] = True
    return stages


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

    features = {**DEFAULT_RECORD_TYPE_FEATURES, **(base.get("features") or {})}
    base["features"] = features
    base["numbering"] = {**default_numbering_for_type(code), **(base.get("numbering") or {})}

    stages = normalize_workflow_stages(base.get("stages") or base.get("workflowStages"))
    if not stages and features.get("enableWorkflow", True) and base.get("supportsStages", True):
        stages = default_workflow_stages_for_type(code, base.get("uiSurface"))
    base["stages"] = stages
    base["workflowStages"] = stages
    if stages and not base.get("transitions"):
        base["transitions"] = sequential_transitions(stages)
    else:
        base.setdefault("transitions", [])
    return base
