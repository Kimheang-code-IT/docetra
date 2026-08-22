"""record — documents, meetings, meeting topics, logs, and other record-based entities."""

from __future__ import annotations

from typing import Any

__all__ = [
    "CollectionService",
    "record_service",
    "record_map",
    "record_serializer",
    "record_stamp",
    "record_validation",
    "collaboration_service",
    "meeting_service",
    "meeting_schedules",
    "router_factory",
]


def __getattr__(name: str) -> Any:
    if name == "CollectionService":
        from app.modules.record.services.service import CollectionService

        return CollectionService
    if name == "record_service":
        from app.modules.record.services import service as record_service

        return record_service
    if name == "record_map":
        from app.modules.record.domain import map as record_map

        return record_map
    if name == "record_serializer":
        from app.modules.record.services import serializer as record_serializer

        return record_serializer
    if name == "record_stamp":
        from app.modules.record.services import stamp as record_stamp

        return record_stamp
    if name == "record_validation":
        from app.modules.record.services import validation as record_validation

        return record_validation
    if name == "collaboration_service":
        from app.modules.record.services import collaboration as collaboration_service

        return collaboration_service
    if name == "meeting_service":
        from app.modules.record.services import meeting as meeting_service

        return meeting_service
    if name == "meeting_schedules":
        from app.modules.record.services import meeting_schedules

        return meeting_schedules
    if name == "router_factory":
        from app.modules.record.services import router_factory

        return router_factory
    raise AttributeError(name)
