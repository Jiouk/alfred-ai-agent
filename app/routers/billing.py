"""
Billing Router - Handle credit purchases and subscriptions
"""

import os
from typing import Any, Dict, List

import stripe
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from app.models import CreditAccount, get_session
from app.core.auth import get_current_client_id
from app.core.credit_manager import CreditManager

router = APIRouter()


class PurchaseRequest(BaseModel):
    tier: str  # starter, growth, payg


class CreditBalanceResponse(BaseModel):
    balance: int
    total_purchased: int
    total_used: int


class TransactionResponse(BaseModel):
    id: int
    amount: int
    type: str
    description: str
    created_at: str


def _purchase_tiers() -> Dict[str, Dict[str, Any]]:
    """Get purchase tier config from environment."""
    return {
        "starter": {
            "credits": int(os.getenv("STARTER_PLAN_CREDITS", "500")),
            "price_cents": int(os.getenv("STARTER_PLAN_PRICE", "1900")),
            "name": "Starter Credits Pack",
        },
        "growth": {
            "credits": int(os.getenv("GROWTH_PLAN_CREDITS", "2000")),
            "price_cents": int(os.getenv("GROWTH_PLAN_PRICE", "4900")),
            "name": "Growth Credits Pack",
        },
        "payg": {
            "credits": int(os.getenv("PAYG_CREDITS_PER_10", "300")),
            "price_cents": int(os.getenv("PAYG_PACK_PRICE", "1000")),
            "name": "Pay-As-You-Go Credits",
        },
    }


def _checkout_urls() -> tuple[str, str]:
    """Build checkout success/cancel URLs."""
    base_url = os.getenv("BASE_URL", "http://localhost:8000").rstrip("/")
    success_url = os.getenv("STRIPE_CHECKOUT_SUCCESS_URL", f"{base_url}/billing/success")
    cancel_url = os.getenv("STRIPE_CHECKOUT_CANCEL_URL", f"{base_url}/billing/cancel")
    return success_url, cancel_url


def _create_checkout_session(client_id: int, tier_key: str, tier: Dict[str, Any]) -> Dict[str, Any]:
    """Create Stripe checkout session and return normalized values."""
    stripe_secret_key = os.getenv("STRIPE_SECRET_KEY", "").strip()
    if not stripe_secret_key:
        raise HTTPException(status_code=503, detail="Stripe is not configured")

    stripe.api_key = stripe_secret_key

    success_url, cancel_url = _checkout_urls()
    metadata = {
        "client_id": str(client_id),
        "tier": tier_key,
        "credits": str(tier["credits"]),
    }

    try:
        checkout_session = stripe.checkout.Session.create(
            mode="payment",
            success_url=success_url,
            cancel_url=cancel_url,
            client_reference_id=str(client_id),
            metadata=metadata,
            payment_intent_data={"metadata": metadata},
            line_items=[
                {
                    "quantity": 1,
                    "price_data": {
                        "currency": os.getenv("STRIPE_CURRENCY", "usd"),
                        "unit_amount": int(tier["price_cents"]),
                        "product_data": {
                            "name": tier["name"],
                            "description": f"{tier['credits']} AI credits",
                        },
                    },
                }
            ],
        )
    except stripe.error.StripeError as exc:
        raise HTTPException(status_code=502, detail=f"Stripe error: {str(exc)}") from exc

    return {
        "checkout_url": getattr(checkout_session, "url", None),
        "session_id": getattr(checkout_session, "id", None),
    }


@router.get("/balance", response_model=CreditBalanceResponse)
async def get_balance(
    client_id: int = Depends(get_current_client_id),
    db: Session = Depends(get_session)
):
    """Get current credit balance"""
    account = db.exec(
        select(CreditAccount).where(CreditAccount.client_id == client_id)
    ).first()
    
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    return CreditBalanceResponse(
        balance=account.balance,
        total_purchased=account.total_purchased,
        total_used=account.total_used
    )


@router.get("/history", response_model=List[TransactionResponse])
async def get_transaction_history(
    client_id: int = Depends(get_current_client_id),
    limit: int = 50,
    db: Session = Depends(get_session)
):
    """Get credit transaction history"""
    transactions = CreditManager.get_transaction_history(
        client_id=client_id,
        session=db,
        limit=limit,
    )
    
    return [
        TransactionResponse(
            id=t.id,
            amount=t.amount,
            type=t.type,
            description=t.description,
            created_at=t.created_at.isoformat()
        )
        for t in transactions
    ]


@router.post("/purchase")
async def purchase_credits(
    request: PurchaseRequest,
    client_id: int = Depends(get_current_client_id)
):
    """
    Create Stripe checkout session for credit purchase.
    """
    tier_key = request.tier.strip().lower()
    tiers = _purchase_tiers()

    if tier_key not in tiers:
        raise HTTPException(status_code=400, detail="Invalid tier")

    tier = tiers[tier_key]
    checkout = _create_checkout_session(client_id=client_id, tier_key=tier_key, tier=tier)

    if not checkout.get("checkout_url"):
        raise HTTPException(status_code=502, detail="Stripe checkout URL missing")

    return {
        "checkout_url": checkout["checkout_url"],
        "checkout_session_id": checkout.get("session_id"),
        "tier": tier_key,
        "credits": tier["credits"],
        "price_cents": tier["price_cents"],
    }
