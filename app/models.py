"""
Database Models for AI Agent SaaS Platform
All models use SQLModel for ORM functionality
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlmodel import SQLModel, Field, Relationship, create_engine, Session, select
from sqlalchemy import Column, JSON, String, DateTime, Integer, Float, Boolean, Text
from enum import Enum
import os
from dotenv import load_dotenv

load_dotenv()

# Database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./ai_agent_saas.db")
engine = create_engine(DATABASE_URL, echo=False)


def get_session():
    """Get database session"""
    with Session(engine) as session:
        yield session


# Enums for status fields
class ClientStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class BotStatus(str, Enum):
    AVAILABLE = "available"
    ASSIGNED = "assigned"
    RETIRED = "retired"


class IntegrationType(str, Enum):
    TELEGRAM = "telegram"
    EMAIL = "email"
    VOIP = "voip"
    SMS = "sms"
    CALENDAR = "calendar"
    CRM = "crm"
    WEB_WIDGET = "web_widget"


class IntegrationStatus(str, Enum):
    CONNECTED = "connected"
    PENDING = "pending"
    ERROR = "error"
    DISCONNECTED = "disconnected"


class ChannelType(str, Enum):
    TELEGRAM = "telegram"
    EMAIL = "email"
    VOIP = "voip"
    SMS = "sms"
    WEB_WIDGET = "web_widget"


class TransactionType(str, Enum):
    PURCHASE = "purchase"
    DEDUCT = "deduct"
    REFUND = "refund"
    WELCOME = "welcome"


# Database Models

class Client(SQLModel, table=True):
    """Client/user of the platform"""
    __tablename__ = "clients"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    email: str = Field(unique=True, index=True)
    stripe_customer_id: Optional[str] = Field(default=None, index=True)
    status: ClientStatus = Field(default=ClientStatus.ACTIVE)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None)
    
    # Relationships
    agent_config: Optional["AgentConfig"] = Relationship(back_populates="client")
    integrations: List["Integration"] = Relationship(back_populates="client")
    channels: List["Channel"] = Relationship(back_populates="client")
    credit_account: Optional["CreditAccount"] = Relationship(back_populates="client")
    credit_transactions: List["CreditTransaction"] = Relationship(back_populates="client")
    conversations: List["Conversation"] = Relationship(back_populates="client")
    memory_entries: List["MemoryStore"] = Relationship(back_populates="client")
    setup_sessions: List["SetupSession"] = Relationship(back_populates="client")


class AgentConfig(SQLModel, table=True):
    """Configuration for each client's AI agent"""
    __tablename__ = "agent_configs"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    client_id: int = Field(foreign_key="clients.id", unique=True)
    agent_name: str = Field(default="My Agent")
    personality: str = Field(default="friendly")  # formal, friendly, brief
    language: str = Field(default="en")
    custom_instructions: Optional[str] = Field(default=None, sa_column=Column(Text))
    compiled_system_prompt: Optional[str] = Field(default=None, sa_column=Column(Text))
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    client: Client = Relationship(back_populates="agent_config")


class Integration(SQLModel, table=True):
    """Third-party integrations for each client"""
    __tablename__ = "integrations"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    client_id: int = Field(foreign_key="clients.id")
    type: IntegrationType
    config_json: Optional[str] = Field(default=None, sa_column=Column(Text))  # JSON as string
    credentials_encrypted: Optional[str] = Field(default=None, sa_column=Column(Text))
    status: IntegrationStatus = Field(default=IntegrationStatus.PENDING)
    connected_at: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None)
    
    # Relationships
    client: Client = Relationship(back_populates="integrations")


class Channel(SQLModel, table=True):
    """Communication channels for each client"""
    __tablename__ = "channels"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    client_id: int = Field(foreign_key="clients.id")
    type: ChannelType
    identifier: str = Field(index=True)  # bot username, email, phone number
    telegram_bot_token: Optional[str] = Field(default=None)
    telegram_bot_username: Optional[str] = Field(default=None)
    email_address: Optional[str] = Field(default=None)
    twilio_number: Optional[str] = Field(default=None)
    active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    client: Client = Relationship(back_populates="channels")


class BotPool(SQLModel, table=True):
    """Pool of pre-created Telegram bots"""
    __tablename__ = "bot_pool"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    bot_token: str = Field(unique=True)  # Encrypted at rest
    bot_username: str = Field(index=True)
    bot_name: str
    status: BotStatus = Field(default=BotStatus.AVAILABLE)
    assigned_to_client_id: Optional[int] = Field(foreign_key="clients.id", default=None)
    assigned_at: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class SetupSession(SQLModel, table=True):
    """Tracks multi-step setup flows"""
    __tablename__ = "setup_sessions"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    client_id: int = Field(foreign_key="clients.id")
    flow_name: str  # voip, sms, calendar, email, crm, web_widget, personality
    current_step: int = Field(default=0)
    collected_data_json: Optional[str] = Field(default=None, sa_column=Column(Text))
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(default=None)
    
    # Relationships
    client: Client = Relationship(back_populates="setup_sessions")


class CreditAccount(SQLModel, table=True):
    """Credit balance for each client"""
    __tablename__ = "credit_accounts"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    client_id: int = Field(foreign_key="clients.id", unique=True)
    balance: int = Field(default=0)
    total_purchased: int = Field(default=0)
    total_used: int = Field(default=0)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    client: Client = Relationship(back_populates="credit_account")


class CreditTransaction(SQLModel, table=True):
    """History of credit purchases and usage"""
    __tablename__ = "credit_transactions"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    client_id: int = Field(foreign_key="clients.id")
    amount: int  # positive for purchase/refund, negative for usage
    type: TransactionType
    description: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    client: Client = Relationship(back_populates="credit_transactions")


class Conversation(SQLModel, table=True):
    """Stores conversation history"""
    __tablename__ = "conversations"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    client_id: int = Field(foreign_key="clients.id")
    channel: ChannelType
    messages_json: str = Field(sa_column=Column(Text))  # JSON array of messages
    started_at: datetime = Field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = Field(default=None)
    
    # Relationships
    client: Client = Relationship(back_populates="conversations")


class MemoryStore(SQLModel, table=True):
    """Key-value memory store for agents"""
    __tablename__ = "memory_store"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    client_id: int = Field(foreign_key="clients.id")
    key: str = Field(index=True)
    value_json: str = Field(sa_column=Column(Text))
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    client: Client = Relationship(back_populates="memory_entries")


# Create all tables
def create_db_and_tables():
    """Create database and all tables"""
    SQLModel.metadata.create_all(engine)


if __name__ == "__main__":
    create_db_and_tables()
    print("✅ Database and tables created successfully!")
