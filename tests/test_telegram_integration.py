import pytest

from app.integrations.telegram import TelegramIntegration


class _MockResponse:
    def __init__(self, payload, raise_http=False):
        self._payload = payload
        self._raise_http = raise_http

    def raise_for_status(self):
        if self._raise_http:
            import httpx
            raise httpx.HTTPStatusError("boom", request=None, response=None)

    def json(self):
        return self._payload


class _MockAsyncClient:
    def __init__(self, response):
        self._response = response
        self.last_url = None
        self.last_json = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, url, json):
        self.last_url = url
        self.last_json = json
        return self._response


@pytest.mark.asyncio
async def test_send_message_requires_chat_and_text():
    integration = TelegramIntegration("token")

    missing_chat = await integration.execute("send_message", {"text": "hi"})
    missing_text = await integration.execute("send_message", {"chat_id": 1})

    assert missing_chat["success"] is False
    assert missing_text["success"] is False


@pytest.mark.asyncio
async def test_send_message_success(monkeypatch):
    response = _MockResponse({"ok": True, "result": {"message_id": 99}})
    client = _MockAsyncClient(response)

    import app.integrations.telegram as telegram_module

    monkeypatch.setattr(
        telegram_module.httpx,
        "AsyncClient",
        lambda timeout: client
    )

    integration = TelegramIntegration("token")
    result = await integration.execute("send_message", {"chat_id": 123, "text": "hello"})

    assert result["success"] is True
    assert result["message_id"] == 99
    assert client.last_url.endswith("/sendMessage")


@pytest.mark.asyncio
async def test_test_connection_false_on_api_error(monkeypatch):
    response = _MockResponse({"ok": False, "description": "Unauthorized"})
    client = _MockAsyncClient(response)

    import app.integrations.telegram as telegram_module

    monkeypatch.setattr(
        telegram_module.httpx,
        "AsyncClient",
        lambda timeout: client
    )

    integration = TelegramIntegration("bad-token")
    ok = await integration.test_connection()

    assert ok is False
