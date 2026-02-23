"""
CreditManager - Handle credits, purchases, and billing
"""

from datetime import datetime
from typing import Optional, List
from sqlmodel import Session, select

from app.models import CreditAccount, CreditTransaction, TransactionType, Client


class CreditManager:
    """Manages credit accounts and transactions"""
    
    @staticmethod
    def get_balance(client_id: int, session: Session) -> int:
        """Get current credit balance for client"""
        statement = select(CreditAccount).where(CreditAccount.client_id == client_id)
        account = session.exec(statement).first()
        return account.balance if account else 0
    
    @staticmethod
    def add_credits(
        client_id: int, 
        amount: int, 
        source: str,
        session: Session
    ) -> bool:
        """Add credits to account"""
        statement = select(CreditAccount).where(CreditAccount.client_id == client_id)
        account = session.exec(statement).first()
        
        if not account:
            # Create new account
            account = CreditAccount(
                client_id=client_id,
                balance=amount,
                total_purchased=amount,
                total_used=0
            )
        else:
            account.balance += amount
            account.total_purchased += amount
            account.updated_at = datetime.utcnow()
        
        # Record transaction
        transaction = CreditTransaction(
            client_id=client_id,
            amount=amount,
            type=TransactionType.PURCHASE if "purchase" in source.lower() else TransactionType.WELCOME,
            description=source
        )
        
        session.add(account)
        session.add(transaction)
        session.commit()
        
        return True
    
    @staticmethod
    def deduct_credits(
        client_id: int, 
        amount: int, 
        description: str,
        session: Session
    ) -> bool:
        """Deduct credits from account"""
        statement = select(CreditAccount).where(CreditAccount.client_id == client_id)
        account = session.exec(statement).first()
        
        if not account or account.balance < amount:
            return False
        
        account.balance -= amount
        account.total_used += amount
        account.updated_at = datetime.utcnow()
        
        transaction = CreditTransaction(
            client_id=client_id,
            amount=-amount,
            type=TransactionType.DEDUCT,
            description=description
        )
        
        session.add(account)
        session.add(transaction)
        session.commit()
        
        return True
    
    @staticmethod
    def get_transaction_history(
        client_id: int,
        session: Session,
        limit: int = 50,
    ) -> List[CreditTransaction]:
        """Get transaction history for client"""
        statement = (
            select(CreditTransaction)
            .where(CreditTransaction.client_id == client_id)
            .order_by(CreditTransaction.created_at.desc())
            .limit(limit)
        )
        return session.exec(statement).all()
    
    @staticmethod
    def check_low_balance(client_id: int, session: Session) -> Optional[str]:
        """Check if balance is low and return alert message"""
        balance = CreditManager.get_balance(client_id, session)
        
        if balance < 50:
            return f"⚠️ You have {balance} credits left. Reply 'buy credits' to top up."
        
        return None
