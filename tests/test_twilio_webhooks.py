from types import SimpleNamespace

import pytest

from app.routers import webhooks


class _FakeRequest:
    def __init__(self, form_data):
        self._form_data = form_data

    async def form(self):
        return self._form_data


def test_normalize_phone_number():
    assert webhooks._normalize_phone_number("+1 (555) 123-4567") == "+15551234567"
    assert webhooks._normalize_phone_number("555-1234") == "5551234"
    assert webhooks._normalize_phone_number(None) is None


def test_extract_twilio_minutes_round_up():
    assert webhooks._extract_twilio_minutes({"CallDuration": "59"}) == 1
    assert webhooks._extract_twilio_minutes({"CallDuration": "60"}) == 1
    assert webhooks._extract_twilio_minutes({"CallDuration": "61"}) == 2
    assert webhooks._extract_twilio_minutes({}) == 0


@pytest.mark.asyncio
async def test_sms_webhook_dispatches_and_sends(monkeypatch):
    request = _FakeRequest({"To": "+15550001", "From": "+15559999", "Body": "hello"})

    channel = SimpleNamespace(client_id=8, twilio_number="+15550001")

    monkeypatch.setattr(webhooks, "_find_twilio_channel_by_number", lambda db, to_number: channel)

    async def fake_dispatch(client_id, text, db, channel_type):
        assert client_id == 8
        assert text == "hello"
        assert channel_type == "sms"
        return "hi there"

    class FakeSMSIntegration:
        async def execute(self, action, params):
            assert action == "send_sms"
            assert params["to"] == "+15559999"
            assert params["from"] == "+15550001"
            assert params["body"] == "hi there"
            return {"success": True, "message_sid": "SM123"}

    monkeypatch.setattr(webhooks, "_dispatch_incoming_message", fake_dispatch)
    monkeypatch.setattr(webhooks, "TwilioSMSIntegration", lambda: FakeSMSIntegration())

    result = await webhooks.sms_webhook(request=request, db=object())

    assert result["ok"] is True
    assert result["processed"] is True


@pytest.mark.asyncio
async def test_voice_webhook_returns_twiml_and_deducts_usage(monkeypatch):
    request = _FakeRequest({"To": "+15550001", "SpeechResult": "book appointment", "CallDuration": "125"})

    channel = SimpleNamespace(client_id=14, twilio_number="+15550001")

    monkeypatch.setattr(webhooks, "_find_twilio_channel_by_number", lambda db, to_number: channel)

    async def fake_dispatch(client_id, text, db, channel_type):
        assert client_id == 14
        assert channel_type == "voip"
        return "Sure, I can help with that"

    class FakeVoiceIntegration:
        async def execute(self, action, params):
            assert action == "build_voice_response"
            assert "Sure, I can help" in params["message"]
            return {"success": True, "twiml": "<Response><Say>ok</Say></Response>"}

    credit_calls = []

    def fake_deduct(client_id, amount, description, session):
        credit_calls.append({"client_id": client_id, "amount": amount, "description": description})
        return True

    monkeypatch.setenv("COST_VOIP_PER_MIN", "2")
    monkeypatch.setattr(webhooks, "_dispatch_incoming_message", fake_dispatch)
    monkeypatch.setattr(webhooks, "TwilioVoIPIntegration", lambda: FakeVoiceIntegration())
    monkeypatch.setattr(webhooks.CreditManager, "deduct_credits", fake_deduct)

    response = await webhooks.voice_webhook(request=request, db=object())

    assert response.media_type == "application/xml"
    assert b"<Response><Say>ok</Say></Response>" in response.body
    assert credit_calls[0]["client_id"] == 14
    # 125s => ceil(2.08) = 3 minutes => 6 credits
    assert credit_calls[0]["amount"] == 6
