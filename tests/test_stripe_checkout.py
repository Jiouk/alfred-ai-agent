from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.routers import billing


def test_purchase_tiers_reads_env(monkeypatch):
    monkeypatch.setenv("STARTER_PLAN_CREDITS", "700")
    monkeypatch.setenv("STARTER_PLAN_PRICE", "2500")

    tiers = billing._purchase_tiers()

    assert tiers["starter"]["credits"] == 700
    assert tiers["starter"]["price_cents"] == 2500


def test_create_checkout_session_requires_stripe_secret(monkeypatch):
    monkeypatch.delenv("STRIPE_SECRET_KEY", raising=False)

    with pytest.raises(HTTPException) as exc:
        billing._create_checkout_session(
            client_id=9,
            tier_key="starter",
            tier={"credits": 500, "price_cents": 1900, "name": "Starter"},
        )

    assert exc.value.status_code == 503


def test_create_checkout_session_builds_metadata_and_line_items(monkeypatch):
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_123")
    monkeypatch.setenv("BASE_URL", "https://api.example.com")

    captured = {}

    def fake_create(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(id="cs_test_1", url="https://checkout.stripe.com/cs_test_1")

    monkeypatch.setattr(billing.stripe.checkout.Session, "create", fake_create)

    result = billing._create_checkout_session(
        client_id=13,
        tier_key="growth",
        tier={"credits": 2000, "price_cents": 4900, "name": "Growth"},
    )

    assert result["session_id"] == "cs_test_1"
    assert result["checkout_url"].startswith("https://checkout.stripe.com/")

    assert captured["mode"] == "payment"
    assert captured["client_reference_id"] == "13"
    assert captured["metadata"]["client_id"] == "13"
    assert captured["metadata"]["tier"] == "growth"
    assert captured["metadata"]["credits"] == "2000"
    assert captured["payment_intent_data"]["metadata"]["client_id"] == "13"

    line_item = captured["line_items"][0]
    assert line_item["price_data"]["unit_amount"] == 4900
