"""Telegram integration adapter — throttled around httpx with a fake client."""

import httpx

from app.integrations.telegram import service


class FakeResponse:
    def __init__(self, payload: dict, *, status_code: int = 200, url: str = "https://api.telegram.org/botTEST/X") -> None:
        self._payload = payload
        self.status_code = status_code
        self.request = httpx.Request("GET", url)
        self._url = url

    def json(self) -> dict:
        return self._payload

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise httpx.HTTPStatusError("boom", request=self.request, response=self)


class FakeAsyncClient:
    """Records calls and returns queued responses per HTTP method."""

    calls: list[tuple[str, str, dict | None]] = []
    responses: dict[str, list[FakeResponse]] = {}

    def __init__(self, *args, **kwargs) -> None:
        pass

    async def __aenter__(self) -> "FakeAsyncClient":
        return self

    async def __aexit__(self, *exc_info) -> bool:
        return False

    def _next(self, method: str, url: str, payload) -> FakeResponse:
        FakeAsyncClient.calls.append((method, url, payload))
        queue = FakeAsyncClient.responses.setdefault(method, [])
        if not queue:
            return FakeResponse({"ok": True, "result": {}})
        return queue.pop(0)

    async def get(self, url, params=None):
        return self._next("GET", url, params)

    async def post(self, url, json=None):
        return self._next("POST", url, json)


def install_fake(monkeypatch, responses: dict[str, list[FakeResponse]] | None = None) -> None:
    FakeAsyncClient.calls = []
    FakeAsyncClient.responses = responses or {}
    monkeypatch.setattr(service.httpx, "AsyncClient", FakeAsyncClient)


async def test_test_bot_connected_returns_username(monkeypatch):
    install_fake(monkeypatch, {"GET": [FakeResponse({"ok": True, "result": {"id": 1, "username": "docetra_bot", "first_name": "Docetra"}})]})

    result = await service.test_bot("meeting", config={"enabled": True, "botToken": "TEST"})

    assert result["status"] == "connected"
    assert result["bot"]["username"] == "docetra_bot"
    assert "docetra_bot" in result["message"]


async def test_test_bot_disabled_without_token(monkeypatch):
    install_fake(monkeypatch)

    result = await service.test_bot("meeting", config={"enabled": True, "botToken": ""})

    assert result["status"] == "disabled"
    assert FakeAsyncClient.calls == []


async def test_test_bot_failed_on_http_error(monkeypatch):
    install_fake(monkeypatch, {"GET": [FakeResponse({"ok": False}, status_code=401)]})

    result = await service.test_bot("meeting", config={"enabled": True, "botToken": "BAD"})

    assert result["status"] == "failed"
    assert "401" in result["message"]


async def test_send_message_posts_chat_and_text(monkeypatch):
    install_fake(monkeypatch, {"POST": [FakeResponse({"ok": True, "result": {"message_id": 7}})]})

    result = await service.send_message("TEST", "1489002750", "hello")

    assert result["ok"] is True
    method, url, payload = FakeAsyncClient.calls[0]
    assert method == "POST"
    assert url.endswith("/botTEST/sendMessage")
    assert payload == {"chat_id": "1489002750", "text": "hello", "parse_mode": "HTML"}


async def test_send_meeting_alert_skips_when_disabled(monkeypatch):
    install_fake(monkeypatch)

    result = await service.send_meeting_alert("1489002750", "hi", bot={"enabled": False, "botToken": "TEST"})

    assert result == {"ok": False, "skipped": True}
    assert FakeAsyncClient.calls == []


async def test_discover_chat_ids_dedupes_and_shapes(monkeypatch):
    updates = {
        "ok": True,
        "result": [
            {"message": {"chat": {"id": 1489002750, "type": "private", "first_name": "Admin"}}},
            {"message": {"chat": {"id": 1489002750, "type": "private", "first_name": "Admin"}}},
            {"channel_post": {"chat": {"id": -100123, "type": "channel", "title": "Docetra", "username": "docetra_ch"}}},
        ],
    }
    install_fake(monkeypatch, {"GET": [FakeResponse(updates)]})

    chats = await service.discover_chat_ids("TEST")

    assert len(chats) == 2
    by_id = {chat["chatId"]: chat for chat in chats}
    assert by_id["1489002750"]["title"] == "Admin"
    assert by_id["-100123"]["title"] == "Docetra"
    assert by_id["-100123"]["username"] == "docetra_ch"
