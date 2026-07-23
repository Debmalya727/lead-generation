"""
Voice Session Manager — VoiceSessionManager tracking active voice sessions, devices, codecs, bitrates, sample rates, and telemetry.
"""
import uuid
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from app.voice.sessions.schemas import VoiceSessionCreate, VoiceSessionUpdate
from app.database.mongodb.collections.voice_infrastructure import VoiceSessionDocument

logger = logging.getLogger("backend.voice.sessions.manager")


class VoiceSessionManager:
    """Manages active and historical voice session lifecycles."""

    def __init__(self):
        self._active_sessions: Dict[str, Dict[str, Any]] = {}

    async def create_session(self, req: VoiceSessionCreate) -> VoiceSessionDocument:
        """Initialize a new voice session in memory and MongoDB."""
        session_id = f"v_sess_{uuid.uuid4().hex[:12]}"

        doc = VoiceSessionDocument(
            session_id=session_id,
            user_id=req.user_id,
            org_id=req.org_id,
            device_id=req.device_id,
            microphone_name=req.microphone_name,
            codec=req.codec,
            sample_rate=req.sample_rate,
            channels=req.channels,
            bitrate=req.bitrate,
            status="active",
            connection_quality="Good",
            latency_ms=15.0,
        )
        await doc.insert()

        self._active_sessions[session_id] = doc.model_dump()
        logger.info(f"VoiceSessionManager: Created session '{session_id}' (codec={req.codec}, rate={req.sample_rate}Hz)")
        return doc

    async def get_session(self, session_id: str) -> Optional[VoiceSessionDocument]:
        """Fetch session by ID."""
        return await VoiceSessionDocument.find_one(VoiceSessionDocument.session_id == session_id)

    async def update_session(self, session_id: str, update: VoiceSessionUpdate) -> Optional[VoiceSessionDocument]:
        """Update active session status and telemetry."""
        doc = await self.get_session(session_id)
        if not doc:
            return None

        if update.status:
            doc.status = update.status
        if update.connection_quality:
            doc.connection_quality = update.connection_quality
        if update.latency_ms is not None:
            doc.latency_ms = update.latency_ms

        await doc.save()

        if session_id in self._active_sessions:
            self._active_sessions[session_id].update(update.model_dump(exclude_unset=True))

        return doc

    async def stop_session(self, session_id: str) -> Optional[VoiceSessionDocument]:
        """Close an active session."""
        doc = await self.get_session(session_id)
        if not doc:
            return None

        doc.status = "closed"
        doc.ended_at = datetime.now(timezone.utc)
        await doc.save()

        self._active_sessions.pop(session_id, None)
        logger.info(f"VoiceSessionManager: Closed session '{session_id}'")
        return doc

    async def list_active_sessions(self) -> List[VoiceSessionDocument]:
        """List active sessions from MongoDB."""
        return await VoiceSessionDocument.find(VoiceSessionDocument.status == "active").to_list()


voice_session_manager = VoiceSessionManager()
