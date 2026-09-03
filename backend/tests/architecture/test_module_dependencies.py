"""Ratchet module dependencies toward the approved acyclic graph."""

from __future__ import annotations

import ast
from pathlib import Path


APP_ROOT = Path(__file__).parents[2] / "app"
MODULE_ROOT = APP_ROOT / "modules"
MODULE_NAMES = frozenset(
    {
        "admin_config",
        "organization",
        "people_access",
        "record",
        "reporting_support",
        "storage_integration",
    }
)

TARGET_EDGES = frozenset(
    {
        ("organization", "admin_config"),
        ("people_access", "admin_config"),
        ("record", "admin_config"),
        ("record", "organization"),
        ("record", "people_access"),
        ("reporting_support", "organization"),
        ("reporting_support", "people_access"),
        ("reporting_support", "record"),
        ("reporting_support", "storage_integration"),
        ("storage_integration", "admin_config"),
        ("storage_integration", "record"),
    }
)


def _imported_modules(path: Path) -> set[str]:
    imported: set[str] = set()
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        names: list[str] = []
        if isinstance(node, ast.Import):
            names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.append(node.module)
        for name in names:
            parts = name.split(".")
            if len(parts) >= 3 and parts[:2] == ["app", "modules"]:
                imported.add(parts[2])
    return imported


def _module_edges() -> set[tuple[str, str]]:
    edges: set[tuple[str, str]] = set()
    for source in MODULE_NAMES:
        for path in (MODULE_ROOT / source).rglob("*.py"):
            for target in _imported_modules(path):
                if target in MODULE_NAMES and target != source:
                    edges.add((source, target))
    return edges


def test_module_graph_matches_approved_dag() -> None:
    assert _module_edges() == TARGET_EDGES


def test_shared_layers_do_not_gain_business_dependencies() -> None:
    offenders = {
        path.relative_to(APP_ROOT).as_posix()
        for layer in ("core", "shared", "integrations")
        for path in (APP_ROOT / layer).rglob("*.py")
        if _imported_modules(path)
    }
    assert offenders == set()


def test_cross_module_imports_use_public_facades() -> None:
    offenders: list[str] = []
    for source in MODULE_NAMES:
        for path in (MODULE_ROOT / source).rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                names = []
                if isinstance(node, ast.Import):
                    names = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom) and node.module:
                    names = [node.module]
                for name in names:
                    parts = name.split(".")
                    if (
                        len(parts) >= 4
                        and parts[:2] == ["app", "modules"]
                        and parts[2] != source
                        and parts[3] not in {"service", "schema", "exceptions", "dependencies"}
                    ):
                        offenders.append(f"{path.relative_to(APP_ROOT)}: {name}")
    assert offenders == []


def test_services_do_not_commit_transactions() -> None:
    offenders = []
    for path in MODULE_ROOT.rglob("services/*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "commit"
            ):
                offenders.append(str(path.relative_to(APP_ROOT)))
    assert offenders == []


def test_modules_do_not_use_legacy_business_model_exports() -> None:
    business_names = {
        "AppSetting", "Entity", "File", "Menu", "Officer",
        "OfficerIdentifier", "Organization", "OrganizationPurpose",
        "OrganizationSector", "Permission", "Record", "RecordAttachment",
        "RecordAttribute", "RecordDetail", "RecordOrganization", "RecordType",
        "RecordTypePermission", "Role", "Setting", "User",
    }
    offenders = []
    for path in MODULE_ROOT.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.ImportFrom):
                continue
            if node.module and node.module.startswith("app.models."):
                imported = business_names & {alias.name for alias in node.names}
                if imported:
                    offenders.append(f"{path.relative_to(APP_ROOT)}: {sorted(imported)}")
            if node.module == "app.db":
                imported = business_names & {alias.name for alias in node.names}
                if imported:
                    offenders.append(f"{path.relative_to(APP_ROOT)}: {sorted(imported)}")
    assert offenders == []


def test_cross_module_imports_are_not_hidden_inside_functions() -> None:
    offenders = []
    for source in MODULE_NAMES:
        for path in (MODULE_ROOT / source).rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                for child in ast.walk(node):
                    if not isinstance(child, (ast.Import, ast.ImportFrom)):
                        continue
                    names = (
                        [alias.name for alias in child.names]
                        if isinstance(child, ast.Import)
                        else [child.module] if child.module else []
                    )
                    for name in names:
                        parts = name.split(".")
                        if len(parts) >= 3 and parts[:2] == ["app", "modules"] and parts[2] != source:
                            offenders.append(f"{path.relative_to(APP_ROOT)}:{child.lineno}: {name}")
    assert offenders == []
