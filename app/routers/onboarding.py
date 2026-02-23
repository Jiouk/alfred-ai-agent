"""
Onboarding Router - Handle new agent claims
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlmodel import Session, select
import os

from app.models import get_session, Client, AgentConfig, CreditAccount, Channel, BotPool
from app.core.bot_pool import BotPoolManager, BotPoolExhaustedException

router = APIRouter()

STARTER_CREDITS = int(os.getenv("STARTER_CREDITS", "50"))


class ClaimAgentRequest(BaseModel):
    name: str
    email: str
    telegram_username: str


class ClaimAgentResponse(BaseModel):
    bot_username: str
    email_address: str
    agent_id: int
    starter_credits: int


@router.post("/claim-agent", response_model=ClaimAgentResponse)
async def claim_agent(
    request: ClaimAgentRequest,
    db: Session = Depends(get_session)
):
    """
    Onboard a new user and assign them an AI agent
    """
    try:
        # 1. Create client record
        client = Client(
            name=request.name,
            email=request.email,
            status="active"
        )
        db.add(client)
        db.commit()
        db.refresh(client)
        
        # 2. Create default agent config
        agent_config = AgentConfig(
            client_id=client.id,
            agent_name=f"{request.name}'s Agent",
            personality="friendly",
            language="en"
        )
        db.add(agent_config)
        
        # 3. Claim bot from pool
        try:
            bot = BotPoolManager.claim_bot(client.id, db)
        except BotPoolExhaustedException:
            # Rollback client creation
            db.delete(client)
            db.commit()
            raise HTTPException(
                status_code=503,
                detail="We'll notify you when an agent is ready. Pool temporarily exhausted."
            )
        
        # 4. Create channel record
        email_address = f"{request.name.lower().replace(' ', '-')}-{client.id}@yourdomain.com"
        channel = Channel(
            client_id=client.id,
            type="telegram",
            identifier=bot.bot_username,
            telegram_bot_token=bot.bot_token,
            telegram_bot_username=bot.bot_username,
            email_address=email_address,
            active=True
        )
        db.add(channel)
        
        # 5. Create credit account with starter credits
        credit_account = CreditAccount(
            client_id=client.id,
            balance=STARTER_CREDITS,
            total_purchased=STARTER_CREDITS,
            total_used=0
        )
        db.add(credit_account)
        
        db.commit()
        
        # 6. TODO: Send welcome message via bot
        # TODO: Set webhook for bot
        
        # 7. Check pool health
        health_alert = BotPoolManager.check_pool_health(db)
        if health_alert:
            # TODO: Send alert to admin
            print(f"ADMIN ALERT: {health_alert}")
        
        return ClaimAgentResponse(
            bot_username=bot.bot_username,
            email_address=email_address,
            agent_id=client.id,
            starter_credits=STARTER_CREDITS
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
