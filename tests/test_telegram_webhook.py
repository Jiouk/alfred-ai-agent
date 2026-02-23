from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.routers import webhooks


def test_extract_telegram_message_from_text_message():
    update = {
        "message": {
            "chat": {"id": 12345},
            "text": "hello",
        }
    }

    chat_id, text = webhooks._extract_telegram_message(update)

    assert chat_id == 12345
    assert text == "hello"


def test_extract_telegram_message_from_callback_query():
    update = {
        "callback_query": {
            "data": "pressed:yes",
            "message": {"chat": {"id": 777}},
        }
    }

    chat_id, text = webhooks._extract_telegram_message(update)

    assert chat_id == 777
    assert text == "pressed:yes"


def test_verify_telegram_secret_invalid(monkeypatch):
    monkeypatch.setenv("TELEGRAM_WEBHOOK_SECRET", "expected")

    request = SimpleNamespace(headers={"x-telegram-bot-api-secret-token": "wrong"})

    with pytest.raises(HTTPException) as exc:
        webhooks._verify_telegram_webhook_secret(request)

    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_dispatch_setup_handler(monkeypatch):
    async def fake_route(client_id, message, channel, context):
        return SimpleNamespace(handler="SetupOrchestrator")

    async def fake_setup_handle(client_id, message, session):
        return "setup-ok"

    monkeypatch.setattr(webhooks.ConversationRouter, "route", fake_route)
    monkeypatch.setattr(webhooks.SetupOrchestrator, "handle", fake_setup_handle)

    result = await webhooks._dispatch_incoming_message(client_id=5, text="setup", db=object())

    assert result == "setup-ok"


@pytest.mark.asyncio
async def test_send_telegram_reply_uses_integration(monkeypatch):
    class FakeIntegration:
        def __init__(self, token):
            assert token == "token-123"

        async def execute(self, action, params):
            assert action == "send_message"
            assert params["chat_id"] == 42
            assert params["text"] == "reply"
            return {"success": True, "message_id": 1}

    monkeypatch.setattr(webhooks, "TelegramIntegration", FakeIntegration)

    channel = SimpleNamespace(telegram_bot_token="token-123")
    result = await webhooks._send_telegram_reply(channel=channel, chat_id=42, text="reply")

    assert result["success"] is True
