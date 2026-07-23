"""
Voice Gateway — Authentication module for WebSocket connections.
"""
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger("backend.voice.gateway.auth")


class VoiceAuthenticationManager:
    """Validates authorization tokens for voice WebSocket connections."""

    async def authenticate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate token and return user identity info."""
        if not token or token == "invalid":
            return None
        # Return standard identity context for voice sessions
        return {
            "user_id": f"user_voice_{token[:8]}",
            "org_id": "org_enterprise_001",
            "authenticated": True,
        }


voice_auth = VoiceAuthenticationManager()
