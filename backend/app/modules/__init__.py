"""Docetra domain modules (modular monolith). Spec: prompt/specification/01-system-architecture.md.

Owned domains:
- record: documents, meetings, meeting topics, logs, other record entities
- organization: departments, government structures, companies, classification
- people_access: officers, users, roles, permissions
- storage_integration: file upload, object storage, Google Drive sync
- admin_config: record types, record attributes, app configuration, settings
- reporting_support: exports and reporting-ready data preparation
"""

from __future__ import annotations

__all__ = [
    "admin_config",
    "organization",
    "people_access",
    "storage_integration",
    "reporting_support",
    "record",
]
