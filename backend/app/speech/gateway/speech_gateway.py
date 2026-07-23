"""
Master SpeechGateway Orchestrator for Phase 13.2: Speech Recognition Gateway.
Coordinates transcription requests, fallback routing, language detection, confidence scoring, cost attribution, and MongoDB persistence.
"""
import uuid
import time
import logging
from typing import Optional, Dict, Any

from app.speech.providers.base_speech import SpeechTranscriptionResult
from app.speech.gateway.fallback_engine import speech_fallback_engine
from app.speech.gateway.confidence_engine import confidence_engine
from app.speech.gateway.language_detector import language_detector
from app.speech.registry.speech_model_registry import speech_model_registry
from app.database.mongodb.collections.speech_gateway import (
    SpeechRequestDocument,
    SpeechResponseDocument,
)

logger = logging.getLogger("backend.speech.gateway.master")


class SpeechGateway:
    """Master Speech-to-Text (STT) Gateway."""

    async def transcribe(
        self,
        audio_bytes: bytes,
        provider: str = "whisper",
        model: str = "whisper-1",
        user_id: str = "user_default",
        org_id: Optional[str] = None,
        session_id: Optional[str] = None,
        language: Optional[str] = None,
    ) -> SpeechResponseDocument:
        """Process STT transcription request through Speech Gateway pipeline."""
        req_id = f"s_req_{uuid.uuid4().hex[:12]}"
        resp_id = f"s_res_{uuid.uuid4().hex[:12]}"
        start_t = time.time()

        # Calculate estimated audio duration (assuming 16-bit 16kHz mono PCM = 32,000 bytes/sec)
        audio_duration_sec = max(0.5, round(len(audio_bytes) / 32000.0, 2))

        # Log Request in MongoDB
        try:
            req_doc = SpeechRequestDocument(
                request_id=req_id,
                user_id=user_id,
                org_id=org_id,
                session_id=session_id,
                provider=provider,
                model=model,
                audio_duration_seconds=audio_duration_sec,
                language=language,
            )
            await req_doc.insert()
        except Exception:
            pass

        # Execute transcription with fallback
        stt_res: SpeechTranscriptionResult = await speech_fallback_engine.execute_with_fallback(
            primary_provider=provider,
            model=model,
            audio_bytes=audio_bytes,
            language=language,
        )

        # Post-process confidence & language
        conf = confidence_engine.evaluate_confidence(stt_res.transcript, base_confidence=stt_res.confidence)
        lang, lang_conf = language_detector.detect_language(stt_res.transcript, hinted_language=language)

        # Calculate estimated cost
        rate_per_min = speech_model_registry.get_cost_per_minute(stt_res.model_used)
        cost_usd = round((audio_duration_sec / 60.0) * rate_per_min, 6)

        latency = round((time.time() - start_t) * 1000, 2)

        # Log Response in MongoDB
        res_doc = SpeechResponseDocument(
            response_id=resp_id,
            request_id=req_id,
            session_id=session_id,
            transcript_text=stt_res.transcript,
            is_partial=stt_res.is_partial,
            confidence_score=conf,
            detected_language=lang,
            language_confidence=lang_conf,
            latency_ms=latency,
            provider_used=stt_res.provider_used,
            model_used=stt_res.model_used,
            estimated_cost=cost_usd,
        )
        try:
            await res_doc.insert()
        except Exception:
            pass

        logger.info(f"SpeechGateway: Transcribed {audio_duration_sec}s audio via '{stt_res.provider_used}' (conf={conf}, lang={lang}, cost=${cost_usd})")
        return res_doc


speech_gateway = SpeechGateway()
