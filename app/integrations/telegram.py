"""
Telegram Integration - Handle Telegram bot messaging
"""

from typing import Any, Dict, Optional
import os

import httpx

from app.integrations.registry import BaseIntegration


class TelegramIntegration(BaseIntegration):
    """Telegram bot integration"""

    name = "telegram"
    setup_flow = "telegram"

    def __init__(self, bot_token: str):
        self.bot_token = bot_token
        self.api_base = f"https://api.telegram.org/bot{bot_token}"
        self.timeout = float(os.getenv("TELEGRAM_API_TIMEOUT", "10"))

    async def execute(self, action: str, params: dict):
        """Execute Telegram action"""
        if action == "send_message":
            return await self._send_message(params)
        if action == "set_webhook":
            return await self._set_webhook(params)
        if action == "get_me":
            return await self._get_me()
        return {"success": False, "error": f"Unknown action: {action}"}

    async def _api_call(self, method: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Call Telegram Bot API and normalize response."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.api_base}/{method}",
                    json=payload or {}
                )
                response.raise_for_status()
        except httpx.HTTPError as exc:
            return {"success": False, "error": f"Telegram HTTP error: {str(exc)}"}

        try:
            data = response.json()
        except ValueError:
            return {"success": False, "error": "Telegram returned non-JSON response"}

        if not data.get("ok"):
            description = data.get("description", "Unknown Telegram API error")
            return {"success": False, "error": description}

        return {"success": True, "result": data.get("result")}

    async def _send_message(self, params: dict):
        """Send message to user"""
        chat_id = params.get("chat_id")
        text = params.get("text")

        if not chat_id:
            return {"success": False, "error": "Missing required param: chat_id"}
        if not text:
            return {"success": False, "error": "Missing required param: text"}

        payload = {
            "chat_id": chat_id,
            "text": text,
        }

        # Optional Telegram sendMessage fields
        for optional_key in ["parse_mode", "disable_web_page_preview", "reply_markup"]:
            if optional_key in params:
                payload[optional_key] = params[optional_key]

        result = await self._api_call("sendMessage", payload)
        if not result["success"]:
            return result

        message = result.get("result") or {}
        return {
            "success": True,
            "message_id": message.get("message_id"),
            "raw": message,
        }

    async def _set_webhook(self, params: dict):
        """Set webhook for bot"""
        url = params.get("url")
        if not url:
            return {"success": False, "error": "Missing required param: url"}

        payload = {"url": url}
        if "secret_token" in params:
            payload["secret_token"] = params["secret_token"]
        if "allowed_updates" in params:
            payload["allowed_updates"] = params["allowed_updates"]

        result = await self._api_call("setWebhook", payload)
        if not result["success"]:
            return result

        return {"success": True, "result": result.get("result")}

    async def _get_me(self) -> Dict[str, Any]:
        """Get bot profile from Telegram API."""
        return await self._api_call("getMe")

    async def test_connection(self) -> bool:
        """Test bot connection"""
        result = await self._get_me()
        return bool(result.get("success"))
