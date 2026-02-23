"""
AgentEngine - Core AI agent execution system
Abstracted runtime for different LLM providers
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, List, Any
from datetime import datetime
import os
import httpx
from sqlmodel import Session

from app.models import Client, AgentConfig, MemoryStore, CreditAccount


class BaseRuntime(ABC):
    """Abstract base class for LLM runtimes"""
    
    @abstractmethod
    async def run(
        self, 
        system_prompt: str, 
        message: str, 
        memory: List[Dict], 
        tools: Optional[List[Dict]] = None
    ) -> str:
        """
        Run inference and return response
        
        Args:
            system_prompt: The compiled system prompt
            message: User message
            memory: Previous conversation context
            tools: Available tools/functions
        
        Returns:
            Response string
        """
        pass


class OpenClawRuntime(BaseRuntime):
    """OpenClaw LLM runtime implementation"""

    def __init__(self):
        self.api_url = os.getenv("OPENCLAW_API_URL", "http://localhost:8080").rstrip("/")
        self.api_key = os.getenv("OPENCLAW_API_KEY")
        self.model = os.getenv("OPENCLAW_MODEL")
        self.timeout = float(os.getenv("OPENCLAW_API_TIMEOUT", "20"))
        endpoint = os.getenv("OPENCLAW_CHAT_ENDPOINT", "/v1/chat/completions")
        self.chat_endpoint = endpoint if endpoint.startswith("/") else f"/{endpoint}"

    def _build_payload(
        self,
        system_prompt: str,
        message: str,
        memory: List[Dict],
        tools: Optional[List[Dict]] = None,
    ) -> Dict[str, Any]:
        """Build a chat-completion-compatible payload."""
        messages: List[Dict[str, Any]] = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        for item in memory:
            role = item.get("role")
            content = item.get("content")
            if role and content:
                messages.append({"role": role, "content": content})

        messages.append({"role": "user", "content": message})

        payload: Dict[str, Any] = {"messages": messages}
        if self.model:
            payload["model"] = self.model
        if tools:
            payload["tools"] = tools

        return payload

    @staticmethod
    def _extract_response_text(data: Dict[str, Any]) -> Optional[str]:
        """Extract assistant text from supported response shapes."""
        # OpenAI-compatible shape
        choices = data.get("choices")
        if isinstance(choices, list) and choices:
            first = choices[0] or {}
            message = first.get("message") if isinstance(first, dict) else None
            if isinstance(message, dict):
                content = message.get("content")
                if isinstance(content, str) and content.strip():
                    return content
                if isinstance(content, list):
                    parts = [
                        part.get("text", "")
                        for part in content
                        if isinstance(part, dict) and isinstance(part.get("text"), str)
                    ]
                    combined = "".join(parts).strip()
                    if combined:
                        return combined

            # Some runtimes place text directly at choice.text
            choice_text = first.get("text") if isinstance(first, dict) else None
            if isinstance(choice_text, str) and choice_text.strip():
                return choice_text

        # Simpler response shapes
        for key in ("response", "text", "output"):
            value = data.get(key)
            if isinstance(value, str) and value.strip():
                return value

        return None

    async def run(
        self,
        system_prompt: str,
        message: str,
        memory: List[Dict],
        tools: Optional[List[Dict]] = None
    ) -> str:
        """Run through OpenClaw API"""
        payload = self._build_payload(system_prompt, message, memory, tools)
        headers: Dict[str, str] = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.api_url}{self.chat_endpoint}",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()

        data = response.json()
        if not isinstance(data, dict):
            raise RuntimeError("OpenClaw API returned invalid response payload")

        response_text = self._extract_response_text(data)
        if not response_text:
            raise RuntimeError("OpenClaw API response missing assistant text")

        return response_text


class AgentEngine:
    """Main engine for executing agent interactions"""
    
    def __init__(self, runtime: BaseRuntime):
        self.runtime = runtime
    
    async def execute(
        self, 
        client_id: int, 
        message: str, 
        channel_type: str,
        session: Session
    ) -> str:
        """
        Execute agent response for a client message
        
        Flow:
        1. Load client config
        2. Check + deduct credits BEFORE running
        3. Run through runtime
        4. Save to memory
        5. Return response
        6. Refund credits if runtime fails
        """
        # 1. Load client config
        config = self._load_config(client_id, session)
        if not config:
            return "Error: Agent not configured"
        
        # 2. Check credits
        credit_cost = self._get_credit_cost(channel_type)
        if not await self._check_and_deduct_credits(client_id, credit_cost, session):
            return "⚠️ You've run out of credits. Reply 'buy credits' to top up."
        
        try:
            # 3. Load memory
            memory = self._load_memory(client_id, session)
            
            # 4. Run through runtime
            response = await self.runtime.run(
                system_prompt=config.compiled_system_prompt or "You are a helpful AI assistant.",
                message=message,
                memory=memory
            )
            
            # 5. Save to memory
            self._save_memory(client_id, message, response, session)
            
            return response
            
        except Exception as e:
            # 6. Refund on failure
            await self._refund_credits(client_id, credit_cost, f"Error: {str(e)}", session)
            return "Sorry, I encountered an error. Please try again."
    
    def _load_config(self, client_id: int, session: Session) -> Optional[AgentConfig]:
        """Load agent configuration for client"""
        from sqlmodel import select
        statement = select(AgentConfig).where(AgentConfig.client_id == client_id)
        return session.exec(statement).first()
    
    def _load_memory(self, client_id: int, session: Session) -> List[Dict]:
        """Load recent conversation memory"""
        # TODO: Implement memory retrieval
        return []
    
    def _save_memory(self, client_id: int, message: str, response: str, session: Session):
        """Save conversation to memory"""
        # TODO: Implement memory storage
        pass
    
    def _get_credit_cost(self, channel_type: str) -> int:
        """Get credit cost for channel type"""
        costs = {
            "telegram": int(os.getenv("COST_TELEGRAM_MSG", "1")),
            "email": int(os.getenv("COST_EMAIL", "2")),
            "voip": int(os.getenv("COST_VOIP_PER_MIN", "2")),
            "sms": int(os.getenv("COST_SMS", "1")),
            "web_widget": int(os.getenv("COST_WEB_WIDGET", "1"))
        }
        return costs.get(channel_type, 1)
    
    async def _check_and_deduct_credits(
        self, 
        client_id: int, 
        amount: int, 
        session: Session
    ) -> bool:
        """Check if client has enough credits and deduct"""
        from sqlmodel import select
        from app.models import CreditAccount, CreditTransaction, TransactionType
        
        statement = select(CreditAccount).where(CreditAccount.client_id == client_id)
        account = session.exec(statement).first()
        
        if not account or account.balance < amount:
            return False
        
        # Deduct credits
        account.balance -= amount
        account.total_used += amount
        account.updated_at = datetime.utcnow()
        
        # Record transaction
        transaction = CreditTransaction(
            client_id=client_id,
            amount=-amount,
            type=TransactionType.DEDUCT,
            description=f"Used {amount} credits"
        )
        
        session.add(account)
        session.add(transaction)
        session.commit()
        
        return True
    
    async def _refund_credits(
        self, 
        client_id: int, 
        amount: int, 
        reason: str,
        session: Session
    ):
        """Refund credits on error"""
        from sqlmodel import select
        from app.models import CreditAccount, CreditTransaction, TransactionType
        
        statement = select(CreditAccount).where(CreditAccount.client_id == client_id)
        account = session.exec(statement).first()
        
        if account:
            account.balance += amount
            account.total_used -= amount
            account.updated_at = datetime.utcnow()
            
            transaction = CreditTransaction(
                client_id=client_id,
                amount=amount,
                type=TransactionType.REFUND,
                description=f"Refund: {reason}"
            )
            
            session.add(account)
            session.add(transaction)
            session.commit()
