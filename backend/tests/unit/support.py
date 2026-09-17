"""Shared fakes for job/consumer unit tests (no database, no broker)."""

from __future__ import annotations

from typing import Any


class FakeResult:
    def __init__(self, rows: list[Any]):
        self._rows = rows

    def all(self) -> list[Any]:
        return self._rows


class FakeSession:
    """Minimal async session stand-in recording mutations."""

    def __init__(self, *, select_batches: list[list[Any]] | None = None, get_row: Any = None):
        self._batches = list(select_batches or [])
        self._get_row = get_row
        self.added: list[Any] = []
        self.deleted: list[Any] = []
        self.commits = 0
        self.flushes = 0

    async def __aenter__(self) -> FakeSession:
        return self

    async def __aexit__(self, *exc: Any) -> bool:
        return False

    async def scalars(self, _stmt: Any) -> FakeResult:
        rows = self._batches.pop(0) if self._batches else []
        return FakeResult(rows)

    async def get(self, _model: Any, _key: Any) -> Any:
        return self._get_row

    def add(self, obj: Any) -> None:
        self.added.append(obj)

    async def flush(self) -> None:
        self.flushes += 1

    async def commit(self) -> None:
        self.commits += 1

    async def delete(self, obj: Any) -> None:
        self.deleted.append(obj)


class FakeCache:
    """Stands in for app.core.cache.short_cache."""

    def __init__(self, *, acquire: bool = True, fail: bool = False):
        self.acquire = acquire
        self.fail = fail
        self.values: dict[str, Any] = {}
        self.deleted: list[str] = []

    async def get(self, key: str) -> Any:
        return self.values.get(key)

    async def set(self, key: str, value: Any, _ttl: int) -> None:
        if self.fail:
            raise RuntimeError("cache unavailable")
        self.values[key] = value

    async def add(self, key: str, value: Any, _ttl: int) -> bool:
        if self.fail:
            raise RuntimeError("cache unavailable")
        if not self.acquire or key in self.values:
            return False
        self.values[key] = value
        return True

    async def delete(self, key: str) -> None:
        self.deleted.append(key)
        self.values.pop(key, None)


class FakeExchange:
    def __init__(self, *, fail: bool = False):
        self.fail = fail
        self.published: list[dict[str, Any]] = []

    async def publish(self, message: Any, routing_key: str) -> None:
        if self.fail:
            raise RuntimeError("broker down")
        self.published.append({"message": message, "routing_key": routing_key})


class FakeChannel:
    def __init__(self, exchange: FakeExchange | None = None):
        self.exchange = exchange or FakeExchange()
        self.declared: list[tuple[str, Any, bool]] = []

    async def declare_exchange(self, name: str, kind: Any, durable: bool = False) -> FakeExchange:
        self.declared.append((name, kind, durable))
        return self.exchange
