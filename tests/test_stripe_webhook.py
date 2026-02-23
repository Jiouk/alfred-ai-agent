import json

import pytest
from fastapi import HTTPException

from app.routers import webhooks


def test_extract_credit_grant_checkout_from_metadata():
    event_object = {
        "client_reference_id": "77",
        "metadata": {
            "credits": "1200",
        },
    }

    client_id, credits, source = webhooks._extract_credit_grant("checkout.session.completed", event_object)

    assert client_id == 77
    assert credits == 1200
    assert source == "Stripe checkout purchase"


def test_extract_credit_grant_from_tier(monkeypatch):
    monkeypatch.setenv("STARTER_PLAN_CREDITS", "555")

    event_object = {
        "metadata": {
            "client_id": "11",
            "tier": "starter",
        }
    }

    client_id, credits, source = webhooks._extract_credit_grant("invoice.paid", event_object)

    assert client_id == 11
    assert credits == 555
    assert source == "Stripe invoice renewal"


def test_verify_and_parse_stripe_event_without_secret(monkeypatch):
    monkeypatch.delenv("STRIPE_WEBHOOK_SECRET", raising=False)

    payload = json.dumps({"type": "checkout.session.completed", "data": {"object": {}}}).encode()
    parsed = webhooks._verify_and_parse_stripe_event(payload, signature=None)

    assert parsed["type"] == "checkout.session.completed"


def test_verify_and_parse_requires_signature_when_secret_set(monkeypatch):
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_test")

    with pytest.raises(HTTPException) as exc:
        webhooks._verify_and_parse_stripe_event(b"{}", signature=None)

    assert exc.value.status_code == 400
    assert "stripe-signature" in exc.value.detail


def test_handle_stripe_event_adds_credits(monkeypatch):
    calls = []

    def fake_add_credits(client_id, amount, source, session):
        calls.append(
            {
                "client_id": client_id,
                "amount": amount,
                "source": source,
            }
        )
        return True

    monkeypatch.setattr(webhooks.CreditManager, "add_credits", fake_add_credits)

    event = {
        "id": "evt_123",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "client_reference_id": "13",
                "metadata": {"credits": "300"},
            }
        },
    }

    result = webhooks._handle_stripe_event(event, db=object())

    assert result["processed"] is True
    assert result["credits_added"] == 300
    assert calls[0]["client_id"] == 13
    assert calls[0]["amount"] == 300
    assert "evt_123" in calls[0]["source"]
