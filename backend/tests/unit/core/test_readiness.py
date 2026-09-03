import pytest

from app.core import readiness


@pytest.mark.asyncio
async def test_readiness_is_degraded_when_optional_dependencies_fail(monkeypatch):
    async def db_ok():
        return None

    async def fail():
        raise RuntimeError("down")

    monkeypatch.setattr(readiness, "probe_database", db_ok)
    monkeypatch.setattr(readiness, "probe_redis", fail)
    monkeypatch.setattr(readiness, "probe_rabbitmq", db_ok)
    status, body = await readiness.readiness_payload(fail)
    assert status == 200
    assert body["status"] == "degraded"
    assert body["database"] == "ok"
    assert body["redis"] == "unavailable"
    assert body["rabbitmq"] == "ok"
    assert body["storage"] == "unavailable"


@pytest.mark.asyncio
async def test_readiness_is_unavailable_when_database_fails(monkeypatch):
    async def fail():
        raise RuntimeError("db")

    monkeypatch.setattr(readiness, "probe_database", fail)
    status, body = await readiness.readiness_payload(fail)
    assert status == 503
    assert body["status"] == "unavailable"
    assert body["database"] == "unavailable"


@pytest.mark.asyncio
async def test_readiness_is_ready_when_all_probes_pass(monkeypatch):
    async def ok():
        return None

    monkeypatch.setattr(readiness, "probe_database", ok)
    monkeypatch.setattr(readiness, "probe_redis", ok)
    monkeypatch.setattr(readiness, "probe_rabbitmq", ok)
    status, body = await readiness.readiness_payload(ok)
    assert status == 200
    assert body == {"status": "ready", "database": "ok", "redis": "ok", "rabbitmq": "ok", "storage": "ok"}
