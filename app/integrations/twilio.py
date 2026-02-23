"""
Twilio Integration - Handle VoIP and SMS
"""

import os
from typing import Any, Dict, Optional

from twilio.base.exceptions import TwilioException
from twilio.rest import Client as TwilioClient
from twilio.twiml.voice_response import VoiceResponse

from app.integrations.registry import BaseIntegration


class _TwilioBaseIntegration(BaseIntegration):
    """Shared Twilio auth/client helpers."""

    def __init__(
        self,
        account_sid: Optional[str] = None,
        auth_token: Optional[str] = None,
        phone_number: Optional[str] = None,
    ):
        self.account_sid = account_sid or os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = auth_token or os.getenv("TWILIO_AUTH_TOKEN")
        self.phone_number = phone_number or os.getenv("TWILIO_PHONE_NUMBER")

    def _is_configured(self) -> bool:
        return bool(self.account_sid and self.auth_token)

    def _client(self) -> Optional[TwilioClient]:
        if not self._is_configured():
            return None
        return TwilioClient(self.account_sid, self.auth_token)

    async def test_connection(self) -> bool:
        client = self._client()
        if not client:
            return False

        try:
            # Lightweight account fetch verifies credentials.
            client.api.accounts(self.account_sid).fetch()
            return True
        except TwilioException:
            return False


class TwilioVoIPIntegration(_TwilioBaseIntegration):
    """Twilio VoIP integration"""

    name = "twilio_voip"
    setup_flow = "voip"

    async def execute(self, action: str, params: dict):
        """Execute VoIP action"""
        if action == "build_voice_response":
            return self._build_voice_response(params)
        if action == "make_call":
            return self._make_call(params)
        return {"success": False, "error": f"Unknown action: {action}"}

    def _build_voice_response(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Build TwiML voice response payload."""
        message = params.get("message") or "Hello! Thanks for calling."
        voice = params.get("voice", "alice")
        language = params.get("language", "en-US")

        response = VoiceResponse()
        response.say(message=message, voice=voice, language=language)

        if params.get("hangup", False):
            response.hangup()

        return {
            "success": True,
            "twiml": str(response),
        }

    def _make_call(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create an outbound call through Twilio Calls API."""
        client = self._client()
        if not client:
            return {"success": False, "error": "Twilio credentials not configured"}

        to_number = params.get("to")
        from_number = params.get("from") or self.phone_number
        twiml_url = params.get("url")
        twiml = params.get("twiml")

        if not to_number:
            return {"success": False, "error": "Missing required param: to"}
        if not from_number:
            return {"success": False, "error": "Missing required param: from"}
        if not twiml_url and not twiml:
            return {"success": False, "error": "Missing required param: url or twiml"}

        payload: Dict[str, Any] = {
            "to": to_number,
            "from_": from_number,
        }
        if twiml_url:
            payload["url"] = twiml_url
        else:
            payload["twiml"] = twiml

        try:
            call = client.calls.create(**payload)
            return {
                "success": True,
                "call_sid": getattr(call, "sid", None),
                "status": getattr(call, "status", None),
            }
        except TwilioException as exc:
            return {"success": False, "error": f"Twilio call error: {str(exc)}"}


class TwilioSMSIntegration(_TwilioBaseIntegration):
    """Twilio SMS integration"""

    name = "twilio_sms"
    setup_flow = "sms"

    async def execute(self, action: str, params: dict):
        """Execute SMS action"""
        if action == "send_sms":
            return self._send_sms(params)
        return {"success": False, "error": f"Unknown action: {action}"}

    def _send_sms(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Send SMS via Twilio Messages API."""
        client = self._client()
        if not client:
            return {"success": False, "error": "Twilio credentials not configured"}

        to_number = params.get("to")
        body = params.get("body")
        from_number = params.get("from") or self.phone_number

        if not to_number:
            return {"success": False, "error": "Missing required param: to"}
        if not body:
            return {"success": False, "error": "Missing required param: body"}
        if not from_number:
            return {"success": False, "error": "Missing required param: from"}

        try:
            message = client.messages.create(
                to=to_number,
                from_=from_number,
                body=body,
            )
            return {
                "success": True,
                "message_sid": getattr(message, "sid", None),
                "status": getattr(message, "status", None),
            }
        except TwilioException as exc:
            return {"success": False, "error": f"Twilio SMS error: {str(exc)}"}
