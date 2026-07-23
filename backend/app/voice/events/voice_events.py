"""
Voice Event Bus for Phase 13.1 Enterprise Voice Infrastructure.
Emits voice lifecycle events:
VoiceConnected, VoiceDisconnected, SpeechStarted, SpeechStopped,
SilenceStarted, SilenceEnded, AudioChunkReceived, SessionClosed.
"""
from typing import Dict, Any, Optional
import logging
from datetime import datetime, timezone

from app.database.mongodb.collections.voice_infrastructure import VoiceEventDocument

logger = logging.getLogger("backend.voice.events")


class VoiceEventPublisher:
    """Publishes voice infrastructure lifecycle events to MongoDB and EventBus."""

    async def emit(self, event_type: str, session_id: str, payload: Optional[Dict[str, Any]] = None) -> VoiceEventDocument:
        """Persist event in MongoDB and publish to global EventBus."""
        payload = payload or {}

        doc = VoiceEventDocument(
            event_id=f"vevt_{session_id[:8]}_{int(datetime.now(timezone.utc).timestamp()*1000)}",
            session_id=session_id,
            event_type=event_type,
            payload=payload,
        )
        try:
            await doc.insert()
        except Exception as e:
            logger.debug(f"VoiceEventPublisher: Event persistence skipped: {e}")

        # Emit to global Platform EventBus (non-blocking)
        try:
            from app.events.event_bus.bus import event_bus
            from app.events.schemas.events import PlatformEvent
            await event_bus.publish(PlatformEvent(
                event_type=f"Voice.{event_type}",
                source="VoiceInfrastructure",
                data={"session_id": session_id, **payload},
            ))
        except Exception:
            pass

        logger.info(f"VoiceEventPublisher: Published '{event_type}' for session '{session_id}'")
        return doc


voice_event_publisher = VoiceEventPublisher()
