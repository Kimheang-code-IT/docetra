"""Collection kind resolution for typed application services."""

from __future__ import annotations

from fastapi import HTTPException

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
    ):
        if type_code:
            if not is_valid_type_code(type_code):
                raise HTTPException(404, "Record type not found")
            self.type_code = type_code
            self.resource = TYPE_CODE_TO_RESOURCE.get(type_code) or f"type:{type_code}"
        elif resource:
            self.resource = resource
            self.type_code = RECORD_RESOURCES.get(resource)
        else:
            raise ValueError("CollectionSpec requires resource or type_code")

    def kind(self) -> str:
        if self.type_code or self.resource in RECORD_RESOURCES:
            return "record"
        if self.resource == "record-types":
            return "record_type"
        if self.resource == "record-attributes":
            return "record_attribute"
        if self.resource in {"record-logs", "portal-logs", "system-logs"}:
            return "audit"
        if self.resource in ENTITY_RESOURCES:
            return "entity"
        return "unsupported"
