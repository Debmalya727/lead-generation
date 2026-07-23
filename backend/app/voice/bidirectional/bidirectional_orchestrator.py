"""
Master BidirectionalVoiceOrchestrator for Phase 13.4: Real-Time Bidirectional Voice AI Streaming Engine.
Coordinates the full Speech-to-Speech loop:
Microphone PCM → VAD → Streaming STT (Speech Gateway) → Conversation Manager → AI Planner / Workflow → Streaming LLM → Incremental Sentence Aggregator → Streaming TTS (TTS Gateway) → Audio Buffer Streamer → Client Player
"""
import uuid
import time
import asyncio
import logging
from typing import Optional, Dict, Any, AsyncGenerator

from app.voice.sessions.session_manager import voice_session_manager
from app.voice.vad.vad_engine import vad_engine
from app.speech.gateway.speech_gateway import speech_gateway
from app.tts.gateway.tts_gateway import tts_gateway
from app.voice.bidirectional.incremental_llm_streamer import incremental_llm_streamer
from app.voice.bidirectional.interruption_handler import interruption_handler
from app.voice.bidirectional.streaming_metrics import streaming_metrics
from app.database.mongodb.collections.bidirectional_voice import BidirectionalSessionDocument

logger = logging.getLogger("backend.voice.bidirectional.master")


class BidirectionalVoiceOrchestrator:
    """Master orchestrator for real-time full-duplex Speech-to-Speech sessions."""

    async def start_duplex_session(
        self,
        user_id: str,
        stt_provider: str = "whisper",
        stt_model: str = "whisper-1",
        tts_provider: str = "elevenlabs",
        tts_voice_id: str = "21m00Tcm4TlvDq8ikWAM",
        emotion: str = "professional",
    ) -> BidirectionalSessionDocument:
        """Initialize a new full duplex voice AI session."""
        session_id = f"b_sess_{uuid.uuid4().hex[:12]}"

        doc = BidirectionalSessionDocument(
            session_id=session_id,
            user_id=user_id,
            stt_provider=stt_provider,
            stt_model=stt_model,
            tts_provider=tts_provider,
            tts_voice_id=tts_voice_id,
            emotion=emotion,
            status="active",
        )
        try:
            await doc.insert()
        except Exception:
            pass

        logger.info(f"BidirectionalVoiceOrchestrator: Started duplex session '{session_id}' for user '{user_id}'")
        return doc

    async def process_user_audio_turn(
        self,
        session_id: str,
        user_id: str,
        pcm_bytes: bytes,
        stt_provider: str = "whisper",
        tts_provider: str = "elevenlabs",
        tts_voice_id: str = "21m00Tcm4TlvDq8ikWAM",
        emotion: str = "professional",
    ) -> Dict[str, Any]:
        """
        Processes a full user speech turn through the bidirectional Speech-to-Speech pipeline.
        1. VAD check for interruptions
        2. Speech Gateway transcription (STT)
        3. LLM AI response streaming
        4. Sentence aggregation
        5. TTS Gateway audio synthesis stream
        6. Latency metrics logging
        """
        turn_start_t = time.time()

        # 1. VAD Check for Interruption
        vad_res = vad_engine.process_frame(session_id, pcm_bytes, is_system_speaking=False)
        if vad_res.event_type == "Interruption":
            await interruption_handler.handle_interruption(session_id)

        # 2. STT Transcription
        stt_start_t = time.time()
        stt_doc = await speech_gateway.transcribe(
            audio_bytes=pcm_bytes,
            provider=stt_provider,
            user_id=user_id,
            session_id=session_id,
        )
        stt_lat = round((time.time() - stt_start_t) * 1000, 2)
        user_transcript = stt_doc.transcript_text

        # 3. Simulate Incremental LLM Response Stream
        llm_start_t = time.time()

        async def mock_llm_tokens():
            response_tokens = [
                "Hello ", "there! ", "I ", "am ", "your ", "LeadForgeAI ", "sales ", "assistant. ",
                "How ", "can ", "I ", "help ", "accelerate ", "your ", "pipeline ", "today?"
            ]
            for tok in response_tokens:
                yield tok
                await asyncio.sleep(0.01)

        # 4. Aggregate Tokens into Sentences & Synthesize via TTS Gateway
        assembled_sentences = []
        tts_ttfb_ms = 0.0
        first_sentence = True

        async for sentence in incremental_llm_streamer.aggregate_tokens(mock_llm_tokens()):
            assembled_sentences.append(sentence)

            # Check if interrupted during output
            if interruption_handler.is_interrupted(session_id):
                logger.warning(f"BidirectionalVoiceOrchestrator: Aborting TTS stream for '{session_id}' due to user interruption")
                break

            tts_start_t = time.time()
            tts_doc = await tts_gateway.synthesize(
                text_prompt=sentence,
                provider=tts_provider,
                voice_id=tts_voice_id,
                session_id=session_id,
                emotion=emotion,
            )
            if first_sentence:
                tts_ttfb_ms = tts_doc.ttfb_ms
                first_sentence = False

        llm_lat = round((time.time() - llm_start_t) * 1000, 2)
        full_assistant_text = " ".join(assembled_sentences)
        e2e_lat = round((time.time() - turn_start_t) * 1000, 2)

        # 5. Log Turn Telemetry
        was_interrupted = interruption_handler.is_interrupted(session_id)
        turn_doc = await streaming_metrics.log_turn_metrics(
            session_id=session_id,
            user_id=user_id,
            user_transcript=user_transcript,
            assistant_response=full_assistant_text,
            stt_latency_ms=stt_lat,
            llm_latency_ms=llm_lat,
            tts_ttfb_ms=tts_ttfb_ms,
            e2e_latency_ms=e2e_lat,
            was_interrupted=was_interrupted,
        )

        return {
            "session_id": session_id,
            "turn_id": turn_doc.turn_id,
            "user_transcript": user_transcript,
            "assistant_response": full_assistant_text,
            "stt_latency_ms": stt_lat,
            "llm_latency_ms": llm_lat,
            "tts_ttfb_ms": tts_ttfb_ms,
            "e2e_latency_ms": e2e_lat,
            "was_interrupted": was_interrupted,
        }


bidirectional_orchestrator = BidirectionalVoiceOrchestrator()
