"""Rewrite app.services imports inside app/modules to app.modules paths."""
from __future__ import annotations

import re
from pathlib import Path

MAP = {
    "configuration_service": "app.modules.admin_config.services.configuration",
    "settings_service": "app.modules.admin_config.services.settings",
    "runtime_settings": "app.modules.admin_config.services.runtime",
    "organization_service": "app.modules.organization.services.service",
    "record_organization_service": "app.modules.organization.services.record_links",
    "people_service": "app.modules.people_access.services.people",
    "identity_service": "app.modules.people_access.services.identity",
    "identity_sync": "app.modules.people_access.services.identity_sync",
    "permission_catalog": "app.modules.people_access.services.permission_catalog",
    "notification_email": "app.modules.people_access.services.notification_email",
    "notification_telegram": "app.modules.people_access.services.notification_telegram",
    "storage_service": "app.modules.storage_integration.services.storage",
    "storage_providers": "app.modules.storage_integration.services.providers",
    "storage_provider_service": "app.modules.storage_integration.services.provider_service",
    "upload_validation": "app.modules.storage_integration.services.upload_validation",
    "google_drive_service": "app.modules.storage_integration.services.google_drive",
    "drive_sync_service": "app.modules.storage_integration.services.drive_sync",
    "export_service": "app.modules.reporting_support.services.export",
    "search_service": "app.modules.reporting_support.services.search",
    "dashboard_service": "app.modules.reporting_support.services.dashboard",
    "mention_service": "app.modules.reporting_support.services.mentions",
    "record_service": "app.modules.record.services.service",
    "record_map": "app.modules.record.domain.map",
    "record_serializer": "app.modules.record.services.serializer",
    "record_stamp": "app.modules.record.services.stamp",
    "record_validation": "app.modules.record.services.validation",
    "record_constants": "app.modules.record.domain.constants",
    "collaboration_service": "app.modules.record.services.collaboration",
    "meeting_service": "app.modules.record.services.meeting",
    "meeting_schedules": "app.modules.record.services.meeting_schedules",
    "router_factory": "app.modules.record.services.router_factory",
}

root = Path(__file__).resolve().parents[1] / "app" / "modules"
pat = re.compile(r"from app\.services\.(\w+) import")

changed = []
for path in root.rglob("*.py"):
    text = path.read_text(encoding="utf-8")
    orig = text

    def repl(m: re.Match[str]) -> str:
        name = m.group(1)
        if name in MAP:
            return f"from {MAP[name]} import"
        return m.group(0)

    text = pat.sub(repl, text)
    for old, new in MAP.items():
        text = text.replace(f"import app.services.{old}", f"import {new}")
    if text != orig:
        path.write_text(text, encoding="utf-8")
        changed.append(str(path.relative_to(root.parent.parent)))

print(f"updated {len(changed)} files")
for c in changed:
    print(c)
