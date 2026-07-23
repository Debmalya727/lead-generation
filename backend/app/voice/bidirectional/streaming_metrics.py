"""
StreamingMetricsTracker — Measures End-to-End Speech-to-Speech Latency, TTFB for STT/LLM/TTS, and interruption counts.
"""
import uuid
import time
import logging
from typing import Dict, Any, Optional

from app.database.mongodb.collections.bidirectional_voice import (
    BidirectionalMetricsDocument,
    BidirectionalTurnDocument,
)

logger = logging.getLogger("backend.voice.bidirectional.metrics")


class StreamingMetricsTracker:
    """Tracks full duplex Speech-to-Speech latency performance metrics."""

    async def log_turn_metrics(
        self,
        session_id: str,
        user_id: str,
        user_transcript: str,
        assistant_response: str,
        stt_latency_ms: float,
        llm_latency_ms: float,
        tts_ttfb_ms: float,
        e2e_latency_ms: float,
        was_interrupted: bool = False,
    ) -> BidirectionalTurnDocument:
        """Log turn metrics and persist to MongoDB."""
        turn_id = f"b_turn_{uuid.uuid4().hex[:12]}"

        turn_doc = BidirectionalTurnDocument(
            turn_id=turn_id,
            session_id=session_id,
            user_id=user_id,
            user_transcript=user_transcript,
            assistant_response=assistant_response,
            stt_latency_ms=stt_latency_ms,
            llm_latency_ms=llm_latency_ms,
            tts_ttfb_ms=tts_ttfb_ms,
            e2e_speech_to_speech_latency_ms=e2e_latency_ms,
            was_interrupted=was_interrupted,
        )
        try:
            await turn_doc.insert()
        except Exception:
            pass

        # Persist metric record
        try:
            m_id = f"b_met_{uuid.uuid4().hex[:12]}"
            m_doc = BidirectionalMetricsDocument(
                metric_id=m_id,
                session_id=session_id,
                e2e_latency_ms=e2e_latency_ms,
                stt_latency_ms=stt_latency_ms,
                llm_ttft_ms=llm_latency_ms,
                tts_ttfb_ms=tts_ttfb_ms,
                interrupted=was_interrupted,
            )
            await m_doc.insert()
        except Exception:
            pass

        logger.info(f"StreamingMetricsTracker: Logged Turn {turn_id} (E2E Latency={e2e_latency_ms}ms, Interrupted={was_interrupted})")
        return turn_doc


streaming_metrics = StreamingMetricsTracker()
