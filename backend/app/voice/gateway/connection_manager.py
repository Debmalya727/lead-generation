"""
Voice Gateway — ConnectionManager tracking active WebSocket connections.
"""
from typing import Dict, Any, List, Optional
import logging
from fastapi import WebSocket

logger = logging.getLogger("backend.voice.gateway.connection")


class VoiceConnectionManager:
    """Manages active WebSocket connections by session_id and user_id."""

    def __init__(self):
        self._active_connections: Dict[str, WebSocket] = {}  # session_id -> WebSocket
        self._session_users: Dict[str, str] = {}  # session_id -> user_id

    async def connect(self, session_id: str, user_id: str, websocket: WebSocket) -> None:
        """Register a new active WebSocket connection."""
        await websocket.accept()
        self._active_connections[session_id] = websocket
        self._session_users[session_id] = user_id
        logger.info(f"VoiceConnectionManager: Connection accepted for session '{session_id}' (user={user_id})")

    def disconnect(self, session_id: str) -> None:
        """Remove a disconnected session."""
        self._active_connections.pop(session_id, None)
        self._session_users.pop(session_id, None)
        logger.info(f"VoiceConnectionManager: Connection closed for session '{session_id}'")

    def get_connection(self, session_id: str) -> Optional[WebSocket]:
        """Fetch active WebSocket for session_id."""
        return self._active_connections.get(session_id)

    def is_connected(self, session_id: str) -> bool:
        """Return True if session WebSocket is connected."""
        return session_id in self._active_connections

    async def send_json(self, session_id: str, message: Dict[str, Any]) -> bool:
        """Send JSON control frame to client."""
        ws = self.get_connection(session_id)
        if ws:
            try:
                await ws.send_json(message)
                return True
            except Exception as e:
                logger.warning(f"VoiceConnectionManager: Error sending JSON to '{session_id}': {e}")
                self.disconnect(session_id)
        return False

    async def send_bytes(self, session_id: str, data: bytes) -> bool:
        """Send binary audio chunk to client."""
        ws = self.get_connection(session_id)
        if ws:
            try:
                await ws.send_bytes(data)
                return True
            except Exception as e:
                logger.warning(f"VoiceConnectionManager: Error sending bytes to '{session_id}': {e}")
                self.disconnect(session_id)
        return False


voice_connection_manager = VoiceConnectionManager()
