"""
Webhook Router - Handle incoming webhooks from external services
"""

import json
import math
import os
import secrets
from typing import Any, Dict, Optional, Tuple

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response
from sqlmodel import Session, select

from app.core.agent_engine import AgentEngine, OpenClawRuntime
from app.core.credit_manager import CreditManager
from app.core.router import ConversationRouter
from app.core.setup import SetupOrchestrator
from app.integrations.telegram import TelegramIntegration
from app.integrations.twilio import TwilioSMSIntegration, TwilioVoIPIntegration
from app.models import Channel, ChannelType, get_session

router = APIRouter()


def _verify_telegram_webhook_secret(request: Request) -> None:
    """Optionally verify Telegram webhook secret token."""
    expected = os.getenv("TELEGRAM_WEBHOOK_SECRET", "").strip()
    if not expected:
        return

    provided = request.headers.get("x-telegram-bot-api-secret-token")
    if not provided or not secrets.compare_digest(provided, expected):
        raise HTTPException(status_code=401, detail="Invalid Telegram webhook secret")


def _extract_telegram_message(update: Dict[str, Any]) -> Tuple[Optional[int], Optional[str]]:
    """Extract (chat_id, text) from common Telegram update shapes."""
    message_sources = [
        update.get("message"),
        update.get("edited_message"),
        update.get("channel_post"),
        update.get("edited_channel_post"),
    ]

    for source in message_sources:
        if not isinstance(source, dict):
            continue

        chat = source.get("chat") or {}
        chat_id = chat.get("id")
        text = source.get("text") or source.get("caption")
        if chat_id and text:
            return int(chat_id), str(text)

    callback = update.get("callback_query") or {}
    if isinstance(callback, dict):
        callback_message = callback.get("message") or {}
        callback_chat = callback_message.get("chat") or {}
        chat_id = callback_chat.get("id")
        text = callback.get("data") or callback_message.get("text")
        if chat_id and text:
            return int(chat_id), str(text)

    return None, None


def _get_telegram_channel(client_id: int, db: Session) -> Optional[Channel]:
    """Get active Telegram channel configuration for client."""
    return db.exec(
        select(Channel)
        .where(Channel.client_id == client_id)
        .where(Channel.type == ChannelType.TELEGRAM)
        .where(Channel.active == True)
    ).first()


async def _dispatch_incoming_message(
    client_id: int,
    text: str,
    db: Session,
    channel_type: str = "telegram",
) -> str:
    """Route incoming message to appropriate handler and return reply text."""
    route_result = await ConversationRouter.route(
        client_id=client_id,
        message=text,
        channel=channel_type,
        context={},
    )

    if route_result.handler == "SetupOrchestrator":
        return await SetupOrchestrator.handle(client_id=client_id, message=text, session=db)

    if route_result.handler == "AccountManager":
        balance = CreditManager.get_balance(client_id=client_id, session=db)
        return f"You currently have {balance} credits."

    if route_result.handler == "HelpResponder":
        return "I can help with setup, tasks, and account questions. Ask me anything."

    engine = AgentEngine(runtime=OpenClawRuntime())
    return await engine.execute(
        client_id=client_id,
        message=text,
        channel_type=channel_type,
        session=db,
    )


async def _send_telegram_reply(channel: Channel, chat_id: int, text: str) -> Dict[str, Any]:
    """Send a Telegram reply through configured bot."""
    if not channel.telegram_bot_token:
        return {"success": False, "error": "Telegram bot token is not configured"}

    integration = TelegramIntegration(channel.telegram_bot_token)
    return await integration.execute(
        "send_message",
        {
            "chat_id": chat_id,
            "text": text,
        },
    )


def _normalize_phone_number(number: Optional[str]) -> Optional[str]:
    """Normalize phone number for DB lookup comparisons."""
    if not number:
        return None
    value = str(number).strip()
    if not value:
        return None

    if value.startswith("+"):
        return "+" + "".join(ch for ch in value if ch.isdigit())
    return "".join(ch for ch in value if ch.isdigit())


def _find_twilio_channel_by_number(db: Session, to_number: Optional[str]) -> Optional[Channel]:
    """Resolve active SMS/VOIP channel by Twilio recipient number."""
    normalized = _normalize_phone_number(to_number)
    if not normalized:
        return None

    channels = db.exec(
        select(Channel)
        .where(Channel.active == True)
        .where(Channel.twilio_number.is_not(None))
    ).all()

    for channel in channels:
        if _normalize_phone_number(channel.twilio_number) == normalized:
            return channel

    return None


def _extract_twilio_minutes(form_data: Dict[str, Any]) -> int:
    """Extract whole-minute duration from Twilio callback data."""
    duration_value = form_data.get("CallDuration") or form_data.get("CallDurationSeconds")
    try:
        duration_seconds = int(duration_value)
    except (TypeError, ValueError):
        return 0

    if duration_seconds <= 0:
        return 0

    return int(math.ceil(duration_seconds / 60.0))


@router.post("/telegram/{client_id}")
async def telegram_webhook(
    client_id: int,
    request: Request,
    db: Session = Depends(get_session),
):
    """Handle Telegram bot webhook"""
    _verify_telegram_webhook_secret(request)

    try:
        update = await request.json()
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid Telegram webhook payload") from exc

    chat_id, incoming_text = _extract_telegram_message(update)
    if not chat_id or not incoming_text:
        return {"ok": True, "processed": False, "note": "No text message in update"}

    channel = _get_telegram_channel(client_id=client_id, db=db)
    if not channel:
        return {"ok": True, "processed": False, "note": "No active Telegram channel configured"}

    try:
        reply_text = await _dispatch_incoming_message(
            client_id=client_id,
            text=incoming_text,
            db=db,
            channel_type="telegram",
        )
    except Exception:
        reply_text = "Sorry, I ran into an error while processing that. Please try again."

    send_result = await _send_telegram_reply(channel=channel, chat_id=chat_id, text=reply_text)

    return {
        "ok": True,
        "processed": bool(send_result.get("success")),
        "telegram": send_result,
    }


@router.post("/email")
async def email_webhook(request: Request):
    """Handle Mailgun inbound email webhook"""
    data = await request.form()

    # TODO: Parse email
    # TODO: Identify client by To address
    # TODO: Pass to ConversationRouter
    # TODO: Reply via Mailgun
    # TODO: Notify client via Telegram

    return {"ok": True}


@router.post("/voice")
async def voice_webhook(
    request: Request,
    db: Session = Depends(get_session),
):
    """Handle Twilio voice webhook"""
    form_data = dict(await request.form())

    to_number = form_data.get("To")
    channel = _find_twilio_channel_by_number(db=db, to_number=to_number)

    if not channel:
        fallback = TwilioVoIPIntegration().execute(
            action="build_voice_response",
            params={"message": "This number is not configured yet.", "hangup": True},
        )
        response = await fallback
        twiml = response.get("twiml", "<Response><Hangup/></Response>")
        return Response(content=twiml, media_type="application/xml")

    inbound_text = form_data.get("SpeechResult") or "Hello"

    try:
        reply_text = await _dispatch_incoming_message(
            client_id=channel.client_id,
            text=str(inbound_text),
            db=db,
            channel_type="voip",
        )
    except Exception:
        reply_text = "Sorry, I had trouble processing your request. Please try again."

    voice_result = await TwilioVoIPIntegration().execute(
        action="build_voice_response",
        params={
            "message": reply_text,
            "hangup": True,
        },
    )

    minutes = _extract_twilio_minutes(form_data)
    if minutes > 0:
        cost_per_minute = int(os.getenv("COST_VOIP_PER_MIN", "2"))
        total_credits = minutes * cost_per_minute
        CreditManager.deduct_credits(
            client_id=channel.client_id,
            amount=total_credits,
            description=f"VoIP call usage ({minutes} min)",
            session=db,
        )

    twiml = voice_result.get("twiml", "<Response><Hangup/></Response>")
    return Response(content=twiml, media_type="application/xml")


@router.post("/sms")
async def sms_webhook(
    request: Request,
    db: Session = Depends(get_session),
):
    """Handle Twilio SMS webhook"""
    form_data = dict(await request.form())

    to_number = form_data.get("To")
    from_number = form_data.get("From")
    inbound_text = form_data.get("Body")

    channel = _find_twilio_channel_by_number(db=db, to_number=to_number)
    if not channel:
        return {"ok": True, "processed": False, "note": "No matching Twilio channel"}

    if not inbound_text:
        return {"ok": True, "processed": False, "note": "No SMS body"}

    try:
        reply_text = await _dispatch_incoming_message(
            client_id=channel.client_id,
            text=str(inbound_text),
            db=db,
            channel_type="sms",
        )
    except Exception:
        reply_text = "Sorry, I had trouble processing your message. Please try again."

    send_result = await TwilioSMSIntegration().execute(
        action="send_sms",
        params={
            "to": from_number,
            "from": channel.twilio_number or to_number,
            "body": reply_text,
        },
    )

    return {"ok": True, "processed": bool(send_result.get("success")), "twilio": send_result}


def _coerce_positive_int(value: Any) -> Optional[int]:
    """Convert value to positive int, or return None."""
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def _tier_credit_map() -> Dict[str, int]:
    """Build tier->credits mapping from env."""
    return {
        "starter": int(os.getenv("STARTER_PLAN_CREDITS", "500")),
        "growth": int(os.getenv("GROWTH_PLAN_CREDITS", "2000")),
        "payg": int(os.getenv("PAYG_CREDITS_PER_10", "300")),
    }


def _extract_credit_grant(event_type: str, event_object: Dict[str, Any]) -> Tuple[Optional[int], Optional[int], Optional[str]]:
    """
    Extract (client_id, credits, source_label) from supported Stripe events.
    """
    metadata = event_object.get("metadata") or {}

    client_id = _coerce_positive_int(
        metadata.get("client_id")
        or event_object.get("client_reference_id")
    )

    credits = _coerce_positive_int(
        metadata.get("credits")
        or metadata.get("credit_amount")
        or metadata.get("credits_per_cycle")
        or metadata.get("plan_credits")
    )

    if not credits:
        tier = str(metadata.get("tier") or metadata.get("plan") or "").strip().lower()
        credits = _tier_credit_map().get(tier)

    if event_type == "checkout.session.completed":
        return client_id, credits, "Stripe checkout purchase"

    if event_type == "invoice.paid":
        return client_id, credits, "Stripe invoice renewal"

    return None, None, None


def _verify_and_parse_stripe_event(payload: bytes, signature: Optional[str]) -> Dict[str, Any]:
    """Verify Stripe signature (if configured) and return parsed event dict."""
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

    if webhook_secret:
        if not signature:
            raise HTTPException(status_code=400, detail="Missing stripe-signature header")

        try:
            event = stripe.Webhook.construct_event(payload, signature, webhook_secret)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid Stripe payload") from exc
        except stripe.error.SignatureVerificationError as exc:
            raise HTTPException(status_code=400, detail="Invalid Stripe signature") from exc

        return event

    # Dev fallback when webhook secret is not configured.
    try:
        event = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON payload") from exc

    if not isinstance(event, dict) or "type" not in event:
        raise HTTPException(status_code=400, detail="Malformed Stripe event payload")

    return event


def _handle_stripe_event(event: Dict[str, Any], db: Session) -> Dict[str, Any]:
    """Process supported Stripe events and add credits when needed."""
    event_type = event.get("type")
    event_id = event.get("id", "unknown")

    if event_type == "payment_intent.failed":
        # TODO: Notify client/admin through configured channel.
        return {
            "event_type": event_type,
            "processed": True,
            "credits_added": 0,
            "note": "Payment failure recorded",
        }

    if event_type not in {"checkout.session.completed", "invoice.paid"}:
        return {
            "event_type": event_type,
            "processed": False,
            "credits_added": 0,
            "note": "Event ignored",
        }

    event_object = (event.get("data") or {}).get("object") or {}
    client_id, credits, source_label = _extract_credit_grant(event_type, event_object)

    if not client_id:
        return {
            "event_type": event_type,
            "processed": False,
            "credits_added": 0,
            "note": "Missing client_id metadata",
        }

    if not credits:
        return {
            "event_type": event_type,
            "processed": False,
            "credits_added": 0,
            "note": "Missing credits metadata",
        }

    source = f"{source_label} (event={event_id})"
    CreditManager.add_credits(client_id=client_id, amount=credits, source=source, session=db)

    return {
        "event_type": event_type,
        "processed": True,
        "credits_added": credits,
        "client_id": client_id,
    }


@router.post("/stripe")
async def stripe_webhook(
    request: Request,
    db: Session = Depends(get_session)
):
    """Handle Stripe webhook"""
    payload = await request.body()
    signature = request.headers.get("stripe-signature")

    event = _verify_and_parse_stripe_event(payload, signature)
    result = _handle_stripe_event(event, db)

    return {"ok": True, **result}
