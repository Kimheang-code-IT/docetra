import pytest

from app.modules.storage_integration.services import storage as storage_mod


class _Missing(Exception):
    code = "NoSuchKey"


@pytest.mark.asyncio
async def test_delete_object_is_idempotent_when_missing(monkeypatch):
    class Client:
        def remove_object(self, *args, **kwargs):
            raise _Missing()

    async def fake_resolve(_db=None):
        return Client(), "bucket"

    async def fake_to_thread(fn, *args, **kwargs):
        return fn(*args, **kwargs)

    monkeypatch.setattr(storage_mod, "resolve_storage", fake_resolve)
    monkeypatch.setattr(storage_mod.asyncio, "to_thread", fake_to_thread)
    await storage_mod.delete_object("gone/key")


@pytest.mark.asyncio
async def test_delete_object_skips_empty_key(monkeypatch):
    called = False

    async def fake_resolve(_db=None):
        nonlocal called
        called = True
        return object(), "bucket"

    monkeypatch.setattr(storage_mod, "resolve_storage", fake_resolve)
    await storage_mod.delete_object("")
    assert called is False


@pytest.mark.asyncio
async def test_put_bytes_retries_then_succeeds(monkeypatch):
    attempts = {"n": 0}

    class Client:
        def put_object(self, *args, **kwargs):
            attempts["n"] += 1
            if attempts["n"] < 3:
                raise RuntimeError("transient")

    async def fake_resolve(_db=None):
        return Client(), "bucket"

    async def fake_ensure(_db=None):
        return None

    async def fake_to_thread(fn, *args, **kwargs):
        return fn(*args, **kwargs)

    async def fake_sleep(_seconds):
        return None

    monkeypatch.setattr(storage_mod, "resolve_storage", fake_resolve)
    monkeypatch.setattr(storage_mod, "ensure_bucket", fake_ensure)
    monkeypatch.setattr(storage_mod.asyncio, "to_thread", fake_to_thread)
    monkeypatch.setattr(storage_mod.asyncio, "sleep", fake_sleep)
    await storage_mod.put_bytes("k", b"x", "text/plain", attempts=3)
    assert attempts["n"] == 3


@pytest.mark.asyncio
async def test_get_object_bytes_runs_off_the_event_loop(monkeypatch):
    class Client:
        def get_object(self, bucket, key):
            class Response:
                def read(self):
                    return b"file-bytes"

                def close(self):
                    return None

                def release_conn(self):
                    return None

            return Response()

    threaded = {"used": False}

    async def fake_resolve(_db=None):
        return Client(), "bucket"

    async def fake_to_thread(fn, *args, **kwargs):
        threaded["used"] = True
        return fn(*args, **kwargs)

    monkeypatch.setattr(storage_mod, "resolve_storage", fake_resolve)
    monkeypatch.setattr(storage_mod.asyncio, "to_thread", fake_to_thread)
    data = await storage_mod.get_object_bytes("path/key")
    assert data == b"file-bytes"
    assert threaded["used"] is True
