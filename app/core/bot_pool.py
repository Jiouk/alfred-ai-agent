"""
BotPoolManager - Core system for managing pre-created Telegram bots
"""

import os
from datetime import datetime
from typing import Optional, List, Dict
from sqlmodel import Session, select
from cryptography.fernet import Fernet
import httpx

from app.models import BotPool, BotStatus, Client, get_session

# Encryption key for bot tokens
FERNET_KEY = os.getenv("FERNET_KEY")
if not FERNET_KEY:
    raise ValueError("FERNET_KEY environment variable required")
fernet = Fernet(FERNET_KEY.encode())

# Telegram Bot API base
TELEGRAM_API = "https://api.telegram.org/bot{token}"
LOW_POOL_THRESHOLD = int(os.getenv("LOW_POOL_THRESHOLD", "10"))


class BotPoolExhaustedException(Exception):
    """Raised when no bots available in pool"""
    pass


class BotPoolManager:
    """
    Manages pool of pre-created Telegram bots.
    Bots are created manually via BotFather and added to pool.
    """
    
    @staticmethod
    def encrypt_token(token: str) -> str:
        """Encrypt bot token for storage"""
        return fernet.encrypt(token.encode()).decode()
    
    @staticmethod
    def decrypt_token(encrypted_token: str) -> str:
        """Decrypt bot token for use"""
        return fernet.decrypt(encrypted_token.encode()).decode()
    
    @staticmethod
    async def validate_bot_token(token: str) -> Optional[Dict]:
        """Validate token via Telegram getMe API"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{TELEGRAM_API.format(token=token)}/getMe")
                data = response.json()
                if data.get("ok"):
                    return data["result"]
                return None
        except Exception as e:
            print(f"Error validating token: {e}")
            return None
    
    @classmethod
    async def add_bot(cls, token: str, session: Session) -> BotPool:
        """Add a new bot to the pool"""
        # Validate token
        bot_info = await cls.validate_bot_token(token)
        if not bot_info:
            raise ValueError("Invalid bot token")
        
        bot_username = bot_info["username"]
        bot_name = bot_info.get("first_name", bot_username)
        
        # Encrypt token
        encrypted_token = cls.encrypt_token(token)
        
        # Create record
        bot_record = BotPool(
            bot_token=encrypted_token,
            bot_username=bot_username,
            bot_name=bot_name,
            status=BotStatus.AVAILABLE
        )
        
        session.add(bot_record)
        session.commit()
        session.refresh(bot_record)
        
        return bot_record
    
    @classmethod
    def claim_bot(cls, client_id: int, session: Session) -> BotPool:
        """Assign an available bot to a client"""
        # Find next available bot
        statement = select(BotPool).where(BotPool.status == BotStatus.AVAILABLE)
        available_bots = session.exec(statement).all()
        
        if not available_bots:
            raise BotPoolExhaustedException("No bots available in pool")
        
        # Take first available
        bot = available_bots[0]
        bot.status = BotStatus.ASSIGNED
        bot.assigned_to_client_id = client_id
        bot.assigned_at = datetime.utcnow()
        
        session.add(bot)
        session.commit()
        session.refresh(bot)
        
        return bot
    
    @classmethod
    def release_bot(cls, client_id: int, session: Session) -> bool:
        """Release bot when client cancels/churns"""
        statement = select(BotPool).where(
            BotPool.assigned_to_client_id == client_id,
            BotPool.status == BotStatus.ASSIGNED
        )
        bot = session.exec(statement).first()
        
        if not bot:
            return False
        
        # TODO: Reset bot via Telegram API
        # - Clear description, about, profile photo
        # - Rename to generic name
        
        bot.status = BotStatus.AVAILABLE
        bot.assigned_to_client_id = None
        bot.assigned_at = None
        
        session.add(bot)
        session.commit()
        
        return True
    
    @classmethod
    def get_pool_status(cls, session: Session) -> Dict:
        """Get current pool statistics"""
        statement = select(BotPool)
        all_bots = session.exec(statement).all()
        
        available = sum(1 for b in all_bots if b.status == BotStatus.AVAILABLE)
        assigned = sum(1 for b in all_bots if b.status == BotStatus.ASSIGNED)
        retired = sum(1 for b in all_bots if b.status == BotStatus.RETIRED)
        
        return {
            "available": available,
            "assigned": assigned,
            "retired": retired,
            "total": len(all_bots),
            "low_alert": available < LOW_POOL_THRESHOLD
        }
    
    @classmethod
    def check_pool_health(cls, session: Session) -> Optional[str]:
        """Check pool health and return alert message if low"""
        status = cls.get_pool_status(session)
        
        if status["low_alert"]:
            return f"⚠️ Bot pool low: only {status['available']} bots available. Add more via /admin/bots/add"
        
        return None
    
    @classmethod
    def retire_bot(cls, bot_id: int, session: Session) -> bool:
        """Mark a bot as retired (broken/banned)"""
        statement = select(BotPool).where(BotPool.id == bot_id)
        bot = session.exec(statement).first()
        
        if not bot:
            return False
        
        bot.status = BotStatus.RETIRED
        bot.assigned_to_client_id = None
        
        session.add(bot)
        session.commit()
        
        return True
    
    @classmethod
    def get_bot_for_client(cls, client_id: int, session: Session) -> Optional[BotPool]:
        """Get the bot assigned to a client"""
        statement = select(BotPool).where(
            BotPool.assigned_to_client_id == client_id,
            BotPool.status == BotStatus.ASSIGNED
        )
        return session.exec(statement).first()


# Admin endpoints helpers
async def admin_add_bot(token: str, session: Session) -> BotPool:
    """Admin endpoint: Add single bot to pool"""
    return await BotPoolManager.add_bot(token, session)


async def admin_bulk_add_bots(tokens: List[str], session: Session) -> Dict:
    """Admin endpoint: Add multiple bots"""
    added = 0
    invalid = 0
    
    for token in tokens:
        try:
            await BotPoolManager.add_bot(token.strip(), session)
            added += 1
        except ValueError:
            invalid += 1
    
    return {"added": added, "invalid": invalid}


def admin_get_pool_status(session: Session) -> Dict:
    """Admin endpoint: Get pool status"""
    return BotPoolManager.get_pool_status(session)


def admin_retire_bot(bot_id: int, session: Session) -> bool:
    """Admin endpoint: Retire a bot"""
    return BotPoolManager.retire_bot(bot_id, session)
