"""Collection kind resolution for typed application services."""

from __future__ import annotations

from fastapi import HTTPException

from app.modules.organization.domain.map import LEGACY_ORG_RESOURCES, ORG_RESOURCES, ORG_TYPE_TO_RESOURCE, is_valid_org_type
from app.modules.record.domain.map import RECORD_RESOURCES, TYPE_CODE_TO_RESOURCE, is_valid_type_code

ENTITY_RESOURCES = {
    "google-drive-sync",
    "drive-files",
    "storage-providers",
    "export-jobs",
}


class CollectionSpec:
    def __init__(
        self,
        resource: str | None = None,
        *,
        type_code: str | None = None,
        org_type: str | None = None,
    ):
        self.org_type: str | None = None
        if type_code:
            if not is_valid_type_code(type_code):
                raise HTTPException(404, "Record type not found")
            self.type_code = type_code
            self.org_type = None
            self.resource = TYPE_CODE_TO_RESOURCE.get(type_code) or f"type:{type_code}"
        elif org_type:
            if not is_valid_org_type(org_type):
                raise HTTPException(404, "Organization type not found")
            self.org_type = org_type
            self.type_code = None
            self.resource = ORG_TYPE_TO_RESOURCE.get(org_type) or f"org:{org_type}"
        elif resource:
            self.resource = resource
            self.type_code = RECORD_RESOURCES.get(resource)
            self.org_type = LEGACY_ORG_RESOURCES.get(resource)
        else:
            raise ValueError("CollectionSpec requires resource, type_code, or org_type")

    def kind(self) -> str:
        if self.type_code or self.resource in RECORD_RESOURCES:
            return "record"
        if self.org_type or self.resource in ORG_RESOURCES:
            return "organization"
        if self.resource == "sectors":
            return "sector"
        if self.resource == "purposes":
            return "purpose"
        if self.resource == "officers":
            return "officer"
        if self.resource == "roles":
            return "role"
        if self.resource == "users":
            return "user"
        if self.resource == "record-types":
            return "record_type"
        if self.resource == "record-attributes":
            return "record_attribute"
        if self.resource == "file-uploads":
            return "file"
        if self.resource in {"record-logs", "portal-logs", "system-logs"}:
            return "audit"
        if self.resource in ENTITY_RESOURCES:
            return "entity"
        return "unsupported"
