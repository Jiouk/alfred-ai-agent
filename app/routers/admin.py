"""
Admin Router - Internal management endpoints
"""

import os
import secrets
from typing import List

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from app.core.bot_pool import BotPoolManager
from app.models import Client, get_session

router = APIRouter()


def _get_admin_api_key() -> str:
    """Load admin API key from environment."""
    return os.getenv("ADMIN_API_KEY", "").strip()


def verify_admin_key(x_admin_api_key: str | None = Header(default=None, alias="X-Admin-Api-Key")):
    """Verify admin API key"""
    expected_key = _get_admin_api_key()
    if not expected_key:
        raise HTTPException(status_code=503, detail="Admin API key not configured")

    if not x_admin_api_key or not secrets.compare_digest(x_admin_api_key, expected_key):
        raise HTTPException(status_code=401, detail="Invalid admin API key")

    return True


class AddBotRequest(BaseModel):
    token: str


class BulkAddBotsRequest(BaseModel):
    tokens: List[str]


class BotStatusResponse(BaseModel):
    available: int
    assigned: int
    retired: int
    total: int
    low_alert: bool


@router.post("/bots/add")
async def admin_add_bot(
    request: AddBotRequest,
    db: Session = Depends(get_session),
    authorized: bool = Depends(verify_admin_key)
):
    """Add a single bot to the pool"""
    try:
        bot = await BotPoolManager.add_bot(request.token, db)
        return {"success": True, "bot_id": bot.id, "username": bot.bot_username}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/bots/bulk-add")
async def admin_bulk_add_bots(
    request: BulkAddBotsRequest,
    db: Session = Depends(get_session),
    authorized: bool = Depends(verify_admin_key)
):
    """Add multiple bots to the pool"""
    added = 0
    invalid = 0
    
    for token in request.tokens:
        try:
            await BotPoolManager.add_bot(token.strip(), db)
            added += 1
        except ValueError:
            invalid += 1
    
    return {"added": added, "invalid": invalid}


@router.get("/bots/status", response_model=BotStatusResponse)
async def admin_bot_status(
    db: Session = Depends(get_session),
    authorized: bool = Depends(verify_admin_key)
):
    """Get bot pool status"""
    return BotPoolManager.get_pool_status(db)


@router.post("/bots/retire")
async def admin_retire_bot(
    bot_id: int,
    db: Session = Depends(get_session),
    authorized: bool = Depends(verify_admin_key)
):
    """Mark a bot as retired"""
    success = BotPoolManager.retire_bot(bot_id, db)
    if not success:
        raise HTTPException(status_code=404, detail="Bot not found")
    return {"success": True}


@router.get("/clients")
async def admin_list_clients(
    db: Session = Depends(get_session),
    authorized: bool = Depends(verify_admin_key)
):
    """List all clients"""
    statement = select(Client)
    clients = db.exec(statement).all()
    
    return [
        {
            "id": c.id,
            "name": c.name,
            "email": c.email,
            "status": c.status,
            "created_at": c.created_at
        }
        for c in clients
    ]


@router.get("/stats")
async def admin_stats(
    db: Session = Depends(get_session),
    authorized: bool = Depends(verify_admin_key)
):
    """Get platform stats"""
    # TODO: Implement proper stats
    return {
        "total_clients": 0,
        "messages_today": 0,
        "credits_consumed": 0,
        "revenue": 0
    }
