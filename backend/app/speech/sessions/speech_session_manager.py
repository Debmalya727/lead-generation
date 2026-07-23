"""
SpeechSessionManager — Tracks real-time speech transcription session state, cumulative audio duration, and final transcript concatenation.
"""
import uuid
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from app.speech.sessions.schemas import SpeechSessionCreate, SpeechSessionUpdate
from app.database.mongodb.collections.speech_gateway import SpeechSessionDocument

logger = logging.getLogger("backend.speech.sessions.manager")


class SpeechSessionManager:
    """Manages real-time Speech-to-Text transcription sessions."""

    async def create_session(self, req: SpeechSessionCreate) -> SpeechSessionDocument:
        """Initialize a new STT session."""
        session_id = f"stt_sess_{uuid.uuid4().hex[:12]}"

        doc = SpeechSessionDocument(
            session_id=session_id,
            user_id=req.user_id,
            provider=req.provider,
            model=req.model,
            status="active",
        )
        try:
            await doc.insert()
        except Exception:
            pass

        logger.info(f"SpeechSessionManager: Started STT session '{session_id}' (provider={req.provider})")
        return doc

    async def append_transcript_chunk(
        self, session_id: str, transcript_chunk: str, audio_duration_sec: float = 1.0
    ) -> Optional[SpeechSessionDocument]:
        """Append partial transcript chunk to session."""
        doc = await SpeechSessionDocument.find_one(SpeechSessionDocument.session_id == session_id)
        if not doc:
            return None

        doc.total_audio_seconds += audio_duration_sec
        doc.total_transcript_chunks += 1
        if doc.accumulated_transcript:
            doc.accumulated_transcript += " " + transcript_chunk
        else:
            doc.accumulated_transcript = transcript_chunk

        await doc.save()
        return doc

    async def close_session(self, session_id: str) -> Optional[SpeechSessionDocument]:
        """Close an STT session."""
        doc = await SpeechSessionDocument.find_one(SpeechSessionDocument.session_id == session_id)
        if not doc:
            return None

        doc.status = "completed"
        doc.ended_at = datetime.now(timezone.utc)
        await doc.save()

        logger.info(f"SpeechSessionManager: Closed STT session '{session_id}' ({doc.total_audio_seconds}s total audio)")
        return doc


speech_session_manager = SpeechSessionManager()
