"""
SetupOrchestrator - Manage multi-turn conversational setup flows
"""

from typing import Optional, Dict, Any
from datetime import datetime
from sqlmodel import Session, select

from app.models import SetupSession, Client


class SetupFlow:
    """Base class for setup flows"""
    
    name: str
    steps: list
    
    def __init__(self):
        self.collected_data = {}
    
    def validate(self, step: int, user_input: str) -> tuple[bool, Optional[str]]:
        """Validate user input for step. Returns (is_valid, error_message)"""
        # Override in subclasses
        return True, None
    
    async def execute(self, collected_data: dict) -> dict:
        """Execute setup with collected data. Returns result dict."""
        # Override in subclasses
        return {"success": True, "message": "Setup complete"}
    
    def get_step_message(self, step: int) -> str:
        """Get message to show for step"""
        if step < len(self.steps):
            return self.steps[step]
        return "Setup complete!"


class VoIPSetupFlow(SetupFlow):
    """Setup flow for VoIP integration"""
    
    name = "voip"
    steps = [
        "Do you have a VoIP number or should I create one for you? (reply: 'have' or 'create')",
        "What should I say when I answer calls?",
        "Great! I'll configure this now."
    ]
    
    def validate(self, step: int, user_input: str) -> tuple[bool, Optional[str]]:
        if step == 0:
            if user_input.lower() not in ["have", "create"]:
                return False, "Please reply 'have' if you have a number, or 'create' if you need one."
        return True, None
    
    async def execute(self, collected_data: dict) -> dict:
        # TODO: Implement Twilio integration
        return {
            "success": True,
            "message": "✅ VoIP configured! Your number will be ready in a few minutes."
        }


class PersonalitySetupFlow(SetupFlow):
    """Setup flow for agent personality"""
    
    name = "personality"
    steps = [
        "What's your agent's name?",
        "How should it communicate? (formal / friendly / brief)",
        "What's your business about? Describe it in a few words.",
        "Any specific instructions? (languages, things to avoid, etc.)"
    ]
    
    def validate(self, step: int, user_input: str) -> tuple[bool, Optional[str]]:
        if step == 1:
            if user_input.lower() not in ["formal", "friendly", "brief"]:
                return False, "Please choose: formal, friendly, or brief"
        return True, None
    
    async def execute(self, collected_data: dict) -> dict:
        # TODO: Compile system prompt and update bot
        return {
            "success": True,
            "message": f"✅ Your agent '{collected_data.get('name')}' is ready!"
        }


class SetupOrchestrator:
    """Manages multi-step setup flows"""
    
    flows = {
        "voip": VoIPSetupFlow,
        "sms": None,  # TODO: Implement
        "calendar": None,  # TODO: Implement
        "email": None,  # TODO: Implement
        "crm": None,  # TODO: Implement
        "web_widget": None,  # TODO: Implement
        "personality": PersonalitySetupFlow,
    }
    
    @classmethod
    async def handle(cls, client_id: int, message: str, session: Session) -> str:
        """Handle setup-related message"""
        # Check if client has active setup session
        active_session = cls._get_active_session(client_id, session)
        
        if active_session:
            # Continue existing flow
            return await cls._continue_flow(client_id, active_session, message, session)
        else:
            # Start new flow
            flow_name = cls._detect_flow(message)
            if flow_name:
                return await cls._start_flow(client_id, flow_name, session)
            else:
                return "I can help you set up: phone (VoIP), email, calendar, or customize my personality. Which would you like?"
    
    @classmethod
    def _get_active_session(cls, client_id: int, session: Session) -> Optional[SetupSession]:
        """Get active setup session for client"""
        statement = (
            select(SetupSession)
            .where(SetupSession.client_id == client_id)
            .where(SetupSession.completed_at == None)
        )
        return session.exec(statement).first()
    
    @classmethod
    def _detect_flow(cls, message: str) -> Optional[str]:
        """Detect which flow to start based on message"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["phone", "voip", "call", "number"]):
            return "voip"
        elif any(word in message_lower for word in ["personality", "name", "style", "character"]):
            return "personality"
        # TODO: Add more flow detections
        
        return None
    
    @classmethod
    async def _start_flow(cls, client_id: int, flow_name: str, session: Session) -> str:
        """Start a new setup flow"""
        flow_class = cls.flows.get(flow_name)
        if not flow_class:
            return f"Sorry, I don't know how to set up {flow_name} yet."
        
        # Create session
        setup_session = SetupSession(
            client_id=client_id,
            flow_name=flow_name,
            current_step=0,
            collected_data="{}"
        )
        session.add(setup_session)
        session.commit()
        
        # Return first step message
        flow = flow_class()
        return flow.get_step_message(0)
    
    @classmethod
    async def _continue_flow(
        cls, 
        client_id: int, 
        setup_session: SetupSession, 
        message: str,
        session: Session
    ) -> str:
        """Continue existing setup flow"""
        # Check for cancel
        if message.lower() in ["cancel", "stop", "exit"]:
            setup_session.completed_at = datetime.utcnow()
            session.add(setup_session)
            session.commit()
            return "Setup cancelled. You can start again anytime by saying 'setup'."
        
        flow_class = cls.flows.get(setup_session.flow_name)
        if not flow_class:
            return "Error: Unknown setup flow."
        
        flow = flow_class()
        current_step = setup_session.current_step
        
        # Validate input
        is_valid, error = flow.validate(current_step, message)
        if not is_valid:
            return error
        
        # Save data
        import json
        collected_data = json.loads(setup_session.collected_data or "{}")
        collected_data[f"step_{current_step}"] = message
        setup_session.collected_data = json.dumps(collected_data)
        
        # Move to next step
        current_step += 1
        setup_session.current_step = current_step
        session.add(setup_session)
        session.commit()
        
        # Check if flow complete
        if current_step >= len(flow.steps):
            # Execute setup
            result = await flow.execute(collected_data)
            setup_session.completed_at = datetime.utcnow()
            session.add(setup_session)
            session.commit()
            return result["message"]
        
        # Return next step message
        return flow.get_step_message(current_step)
