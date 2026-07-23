"""
Voice Gateway — Master VoiceGateway orchestrator managing connection, session creation, authentication, and routing.
"""
from typing import Dict, Any, Optional
import logging
from fastapi import WebSocket

from app.voice.gateway.authentication import voice_auth
from app.voice.gateway.connection_manager import voice_connection_manager
from app.voice.gateway.websocket_manager import websocket_manager
from app.voice.gateway.heartbeat import voice_heartbeat
from app.voice.gateway.rate_limiter import voice_rate_limiter

logger = logging.getLogger("backend.voice.gateway.master")


class VoiceGateway:
    """Master Gateway for enterprise voice streaming infrastructure."""

    async def handle_websocket_session(
        self,
        session_id: str,
        token: str,
        websocket: WebSocket,
        on_audio_chunk: Optional[Any] = None,
        on_control_frame: Optional[Any] = None,
    ) -> None:
        """Authenticate and service voice streaming WebSocket connection."""
        auth_context = await voice_auth.authenticate_token(token)
        if not auth_context:
            await websocket.close(code=4001, reason="Authentication failed")
            return

        user_id = auth_context["user_id"]
        logger.info(f"VoiceGateway: Starting session '{session_id}' for user '{user_id}'")

        await websocket_manager.handle_connection(
            session_id=session_id,
            user_id=user_id,
            websocket=websocket,
            on_audio_chunk=on_audio_chunk,
            on_control_frame=on_control_frame,
        )


voice_gateway = VoiceGateway()
