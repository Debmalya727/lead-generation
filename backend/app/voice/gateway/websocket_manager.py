"""
Voice Gateway — WebSocketManager handling binary audio streams and control JSON messages.
"""
from typing import Dict, Any, Optional
import logging
from fastapi import WebSocket, WebSocketDisconnect

from app.voice.gateway.connection_manager import voice_connection_manager
from app.voice.gateway.heartbeat import voice_heartbeat
from app.voice.gateway.rate_limiter import voice_rate_limiter

logger = logging.getLogger("backend.voice.gateway.websocket")


class WebSocketManager:
    """Manages raw WebSocket stream frames and routes binary/text data."""

    async def handle_connection(
        self,
        session_id: str,
        user_id: str,
        websocket: WebSocket,
        on_audio_chunk: Optional[Any] = None,
        on_control_frame: Optional[Any] = None,
    ) -> None:
        """Main socket handling loop for audio streaming."""
        await voice_connection_manager.connect(session_id, user_id, websocket)

        # Notify connection accepted
        await voice_connection_manager.send_json(session_id, {
            "type": "connection_accepted",
            "session_id": session_id,
            "status": "active",
        })

        try:
            while True:
                # Receive text or binary frame
                message = await websocket.receive()
                
                if "bytes" in message and message["bytes"]:
                    # Binary Audio Chunk
                    audio_bytes = message["bytes"]
                    if not voice_rate_limiter.allow_frame(session_id):
                        continue

                    if on_audio_chunk:
                        await on_audio_chunk(session_id, audio_bytes)

                elif "text" in message and message["text"]:
                    # Text JSON Control Frame (ping/pong, config, pause)
                    import json
                    try:
                        data = json.loads(message["text"])
                        msg_type = data.get("type")

                        if msg_type == "ping":
                            rtt = voice_heartbeat.record_pong(session_id)
                            await voice_connection_manager.send_json(session_id, {
                                "type": "pong",
                                "rtt_ms": rtt,
                            })
                        elif on_control_frame:
                            await on_control_frame(session_id, data)

                    except json.JSONDecodeError:
                        pass

        except WebSocketDisconnect:
            logger.info(f"WebSocketManager: Client disconnected session '{session_id}'")
        except Exception as e:
            logger.warning(f"WebSocketManager: Socket error session '{session_id}': {e}")
        finally:
            voice_connection_manager.disconnect(session_id)


websocket_manager = WebSocketManager()
