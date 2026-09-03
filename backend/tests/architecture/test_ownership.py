"""ORM ownership rules.

Locks in the removal of the legacy ``app.models`` compatibility package:
every mapped class has exactly one canonical owner module, ``app.db`` exports
infrastructure only, and platform layers stay free of business imports.
"""

from __future__ import annotations

import ast
from pathlib import Path

BACKEND_ROOT = Path(__file__).parents[2]
APP_ROOT = BACKEND_ROOT / "app"
SCAN_ROOTS = (BACKEND_ROOT / "app", BACKEND_ROOT / "tests", BACKEND_ROOT / "alembic")

MAPPED_CLASS_NAMES = frozenset(
    {
        "Activity", "AppSetting", "AuditLog", "Comment", "Entity",
        "Favorite", "File", "MeetingSchedule", "Menu", "NotificationAuditLog",
        "Officer", "OfficerIdentifier", "Organization", "OrganizationPurpose",
        "OrganizationSector", "Outbox", "Permission", "Record",
        "RecordAttachment", "RecordAttribute", "RecordDetail",
        "RecordOrganization", "RecordStageTemplate", "RecordTemplate",
        "RecordType", "RecordTypePermission", "Role", "Setting", "User",
    }
)

SCAN_EXTENSIONS = {".py"}


def _py_files() -> list[Path]:
    files: list[Path] = []
    for root in SCAN_ROOTS:
        files.extend(path for path in root.rglob("*.py") if "__pycache__" not in path.parts)
    return files


def _imported_names(path: Path) -> list[tuple[str, list[str]]]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found: list[tuple[str, list[str]]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                found.append((alias.name, [alias.asname or alias.name]))
        elif isinstance(node, ast.ImportFrom) and node.module:
            found.append((node.module, [alias.asname or alias.name for alias in node.names]))
    return found


def test_app_models_package_is_gone() -> None:
    assert not (APP_ROOT / "models").exists()


def test_no_module_imports_app_models() -> None:
    offenders: list[str] = []
    for path in _py_files():
        for module, _names in _imported_names(path):
            if module == "app.models" or module.startswith("app.models."):
                offenders.append(path.relative_to(BACKEND_ROOT).as_posix())
                break
    assert offenders == []


def test_app_db_exports_infrastructure_only() -> None:
    offenders: list[str] = []
    for path in (APP_ROOT / "db").rglob("*.py"):
        if path.name == "metadata.py" or "__pycache__" in path.parts:
            continue
        for module, names in _imported_names(path):
            parts = module.split(".")
            if (len(parts) >= 3 and parts[0:2] in (["app", "modules"], ["app", "platform"])
                    and (parts[-1] == "model" or "model" in names)):
                offenders.append(path.relative_to(BACKEND_ROOT).as_posix())
    assert offenders == []


def test_mapped_classes_are_not_imported_through_app_db() -> None:
    offenders: list[str] = []
    for path in _py_files():
        for module, names in _imported_names(path):
            if module == "app.db" or module.startswith("app.db."):
                leaked = MAPPED_CLASS_NAMES & set(names)
                if leaked:
                    offenders.append(f"{path.relative_to(BACKEND_ROOT).as_posix()}: {sorted(leaked)}")
    assert offenders == []


def test_metadata_registry_imports_canonical_owners_only() -> None:
    tree = ast.parse((APP_ROOT / "db" / "metadata.py").read_text(encoding="utf-8"))
    owner_imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            for alias in node.names:
                if alias.name == "model":
                    owner_imports.add(f"{node.module}.{alias.name}")
    expected = {
        f"app.modules.{name}.model"
        for name in ("admin_config", "organization", "people_access", "record", "storage_integration")
    } | {"app.platform.audit.model", "app.platform.messaging.model"}
    assert owner_imports == expected


def test_platform_imports_no_business_modules() -> None:
    offenders: list[str] = []
    for path in (APP_ROOT / "platform").rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        for module, _names in _imported_names(path):
            parts = module.split(".")
            if len(parts) >= 3 and parts[0:2] == ["app", "modules"]:
                offenders.append(path.relative_to(BACKEND_ROOT).as_posix())
                break
    assert offenders == []
