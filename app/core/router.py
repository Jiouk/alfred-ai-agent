"""
ConversationRouter - Route messages to appropriate handlers
"""

from enum import Enum
from typing import Optional
from dataclasses import dataclass


class Intent(Enum):
    SETUP = "setup"
    TASK = "task"
    ACCOUNT = "account"
    HELP = "help"


@dataclass
class RouterResponse:
    intent: Intent
    handler: str
    confidence: float


class ConversationRouter:
    """Routes incoming messages to appropriate handlers"""
    
    # Keywords for intent classification
    SETUP_KEYWORDS = [
        "connect", "add", "change", "configure", "set up", "link",
        "integrate", "setup", "install", "enable", "activate"
    ]
    
    ACCOUNT_KEYWORDS = [
        "credits", "balance", "buy", "purchase", "payment",
        "subscription", "plan", "billing", "how many credits"
    ]
    
    HELP_KEYWORDS = [
        "help", "what can you", "how do i", "how to", "?",
        "explain", "assist", "support"
    ]
    
    TASK_KEYWORDS = [
        "help me", "send", "find", "create", "book", "write",
        "make", "get", "show", "tell me", "do"
    ]
    
    @classmethod
    async def classify_intent(cls, message: str, context: dict = None) -> Intent:
        """Classify message intent"""
        message_lower = message.lower()
        
        # Check for setup intent
        for keyword in cls.SETUP_KEYWORDS:
            if keyword in message_lower:
                return Intent.SETUP
        
        # Check for account intent
        for keyword in cls.ACCOUNT_KEYWORDS:
            if keyword in message_lower:
                return Intent.ACCOUNT
        
        # Check for help intent
        for keyword in cls.HELP_KEYWORDS:
            if keyword in message_lower:
                return Intent.HELP
        
        # Default to task
        return Intent.TASK
    
    @classmethod
    async def route(
        cls, 
        client_id: int, 
        message: str, 
        channel: str,
        context: dict = None
    ) -> RouterResponse:
        """
        Route message to appropriate handler
        
        Returns:
            RouterResponse with intent and handler name
        """
        intent = await cls.classify_intent(message, context)
        
        handler_map = {
            Intent.SETUP: "SetupOrchestrator",
            Intent.TASK: "AgentEngine",
            Intent.ACCOUNT: "AccountManager",
            Intent.HELP: "HelpResponder"
        }
        
        return RouterResponse(
            intent=intent,
            handler=handler_map[intent],
            confidence=0.9  # TODO: Implement proper confidence scoring
        )
