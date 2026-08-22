"""Rewrite remaining app.services import styles to app.modules."""
from __future__ import annotations

import re
from pathlib import Path

# "from app.services import foo as bar" / "from app.services import foo"
ALIAS_MAP = {
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

# Also rewrite dotted form
DOTTED = {k: v for k, v in ALIAS_MAP.items()}

ROOT = Path(__file__).resolve().parents[1]
TARGETS = [
    ROOT / "app" / "modules",
    ROOT / "app" / "api",
    ROOT / "app" / "core",
    ROOT / "app" / "jobs",
    ROOT / "app" / "scheduler_jobs",
    ROOT / "app" / "factory.py",
]


def rewrite_text(text: str) -> str:
    # from app.services.X import Y
    def dotted(m: re.Match[str]) -> str:
        name = m.group(1)
        if name in DOTTED:
            return f"from {DOTTED[name]} import{m.group(2)}"
        return m.group(0)

    text = re.sub(r"from app\.services\.(\w+) import(\s+)", dotted, text)

    # from app.services import name as alias
    def aliased(m: re.Match[str]) -> str:
        name, alias = m.group(1), m.group(2)
        if name in ALIAS_MAP:
            return f"from {ALIAS_MAP[name]} import {name} as {alias}" if False else f"import {ALIAS_MAP[name]} as {alias}"
        return m.group(0)

    # Prefer: import module.path as alias  OR  from module.path import *
    # For `from app.services import foo as bar` -> `from NEW import ...` won't work for module-as-package.
    # Best: `from NEW_PKG import X` where we need symbols.
    # Pattern used in codebase: `from app.services import collaboration_service as collaboration`
    # -> `from app.modules.record import collaboration as collaboration` NO - collaboration.py is the module
    # -> `from app.modules.record import collaboration_service as collaboration` if re-exported
    # Simplest working form: `import app.modules.record.services.collaboration as collaboration`

    def alias_import(m: re.Match[str]) -> str:
        name, alias = m.group(1), m.group(2)
        if name in ALIAS_MAP:
            return f"import {ALIAS_MAP[name]} as {alias}"
        return m.group(0)

    text = re.sub(
        r"from app\.services import (\w+) as (\w+)",
        alias_import,
        text,
    )

    # from app.services import name  (no alias) — rare
    def plain(m: re.Match[str]) -> str:
        name = m.group(1)
        if name in ALIAS_MAP:
            return f"import {ALIAS_MAP[name]} as {name}"
        return m.group(0)

    text = re.sub(r"from app\.services import (\w+)(?!\s+as)", plain, text)
    return text


changed = []
files: list[Path] = []
for target in TARGETS:
    if target.is_file():
        files.append(target)
    else:
        files.extend(target.rglob("*.py"))

for path in files:
    if "rewrite_module" in path.name:
        continue
    orig = path.read_text(encoding="utf-8")
    text = rewrite_text(orig)
    if text != orig:
        path.write_text(text, encoding="utf-8")
        changed.append(str(path.relative_to(ROOT)))

print(f"updated {len(changed)}")
for c in changed:
    print(c)
