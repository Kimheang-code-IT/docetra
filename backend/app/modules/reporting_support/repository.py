"""Reporting read-port composition without ownership of business tables."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class ReadPort(Protocol):
    async def read_for_reporting(self, query: dict) -> list[dict]: ...


@dataclass(frozen=True)
class ReportingRepositories:
    records: ReadPort
    organizations: ReadPort
    people: ReadPort
    storage: ReadPort


__all__ = ["ReadPort", "ReportingRepositories"]
