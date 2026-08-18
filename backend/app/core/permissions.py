WORKFLOW = ["view", "create", "edit", "archive", "restore", "delete", "purge", "assign", "share", "export", "comment", "transition"]
MASTER = ["view", "create", "edit", "delete", "export", "comment"]
AUDIT = ["view", "export"]
CONFIG = ["view", "create", "edit", "delete", "export", "comment", "configure"]
SETTINGS = ["view", "edit", "configure"]
USERS = ["view", "create", "edit", "archive", "restore", "delete", "purge", "comment", "configure"]

# documentType values match frontend ROLE_DOCUMENT_TYPES.
DOCUMENT_TYPES: list[tuple[str, str, list[str]]] = [
    ("dashboard", "dashboard", ["view"]),
    ("archive", "archive", ["view"]),
    ("incoming_document", "records.incoming_documents", WORKFLOW),
    ("outgoing_document", "records.outgoing_documents", WORKFLOW),
    ("document", "records.documents", WORKFLOW),
    ("master_list_request", "records.master_list_requests", WORKFLOW),
    ("meeting_topic", "meetings.topics", WORKFLOW),
    ("meeting_history", "meetings.history", WORKFLOW),
    ("department", "organizations.departments", MASTER),
    ("company", "organizations.companies", MASTER),
    ("company_purpose", "organizations.company_purposes", MASTER),
    ("company_sector", "organizations.company_sectors", MASTER),
    ("officer", "organizations.officers", MASTER),
    ("user", "users.users", USERS),
    ("role", "users.roles", USERS),
    ("record_type", "configuration.record_types", CONFIG),
    ("record_attribute", "configuration.record_attributes", CONFIG),
    ("record_log", "records.logs", AUDIT),
    ("file_upload", "portal.file_upload", ["view", "create", "delete", "share", "export"]),
    ("google_drive_sync", "portal.google_drive_sync", CONFIG),
    ("portal_log", "portal.logs", AUDIT),
    ("system_log", "system.logs", AUDIT),
    ("app_config", "settings.app_config", SETTINGS),
    ("app_info", "settings.app_info", SETTINGS),
    ("storage", "settings.storage", SETTINGS),
]

PREFIXES = {prefix: actions for _, prefix, actions in DOCUMENT_TYPES}
TYPE_TO_PREFIX = {doc_type: prefix for doc_type, prefix, _ in DOCUMENT_TYPES}
ALL_PERMISSIONS = [f"{prefix}.{action}" for prefix, actions in PREFIXES.items() for action in actions]
def normalize_permission_payload(payload:dict)->dict:
    rows=payload.get("permissionRows") or []; normalized=[]; flat=set()
    for raw in rows:
        document_type=str(raw.get("documentType", "")); prefix=TYPE_TO_PREFIX.get(document_type)
        if not prefix: raise ValueError(f"Unknown permission document type: {document_type}")
        allowed=set(PREFIXES[prefix]); actions=[]
        for action in raw.get("actions") or []:
            if action not in allowed: raise ValueError(f"Action {action} is not allowed for {document_type}")
            actions.append(action)
        if actions and "view" not in actions: actions.insert(0,"view")
        actions=list(dict.fromkeys(actions)); level=int(raw.get("level",0))
        if not 0<=level<=9: raise ValueError("Permission level must be between 0 and 9")
        normalized.append({"id":raw.get("id") or f"perm_{document_type}","documentType":document_type,"actions":actions,"onlyIfCreator":bool(raw.get("onlyIfCreator")) if actions and "purge" not in actions else False,"level":level})
        flat.update(f"{prefix}.{action}" for action in actions)
    computed=sorted(flat)
    supplied=payload.get("permissions")
    if supplied is not None and sorted(set(supplied))!=computed: raise ValueError("permission_payload_mismatch")
    return {**payload,"permissionRows":normalized,"permissions":computed,"permissionCount":len(computed),"permissionSchemaVersion":1}


def catalog_rows() -> list[dict]:
    return [
        {
            "id": f"perm_{doc_type}",
            "documentType": doc_type,
            "actions": list(actions),
            "onlyIfCreator": False,
            "level": 0,
        }
        for doc_type, _prefix, actions in DOCUMENT_TYPES
    ]


def expand_permission_rows(rows: list | None) -> list[str]:
    keys: list[str] = []
    for row in rows or []:
        if not isinstance(row, dict):
            continue
        prefix = TYPE_TO_PREFIX.get(str(row.get("documentType") or ""))
        if not prefix:
            continue
        for action in row.get("actions") or []:
            keys.append(f"{prefix}.{action}")
    return keys
