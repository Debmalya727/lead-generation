"""
Phase 13.2 REST & WebSocket API Router — Speech Recognition Gateway (ASR / STT).
Endpoints:
- POST /api/v1/speech/transcribe
- GET /api/v1/speech/providers
- GET /api/v1/speech/models
- GET /api/v1/speech/sessions
- GET /api/v1/speech/costs
- GET /api/v1/speech/benchmarks
- WS /api/v1/voice/ws/transcribe/{session_id}
"""
import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, WebSocket, File, UploadFile, status

from app.speech.gateway.speech_gateway import speech_gateway
from app.speech.registry.speech_provider_registry import speech_provider_registry
from app.speech.registry.speech_model_registry import speech_model_registry
from app.speech.sessions.speech_session_manager import speech_session_manager
from app.speech.cost.speech_cost_tracker import speech_cost_tracker
from app.speech.benchmarks.speech_benchmark_engine import speech_benchmark_engine
from app.database.mongodb.collections.speech_gateway import (
    SpeechResponseDocument,
    SpeechSessionDocument,
    SpeechCostDocument,
    SpeechBenchmarkDocument,
)

logger = logging.getLogger("backend.speech.routers.speech_router")

router = APIRouter(prefix="/speech", tags=["Speech Recognition Gateway (13.2)"])


# ─── REST ENDPOINTS ─────────────────────────────────────────────────────────────

@router.post("/transcribe")
async def transcribe_audio(
    provider: str = Query("whisper"),
    model: str = Query("whisper-1"),
    language: Optional[str] = Query(None),
    user_id: str = Query("user_default"),
    file: Optional[UploadFile] = File(None),
):
    """
    Synchronous audio file or PCM stream transcription endpoint.
    Routes audio through Speech Gateway with provider failover.
    """
    if file:
        audio_bytes = await file.read()
    else:
        # Default mock 16-bit 16kHz audio sample (1 second silence)
        audio_bytes = b"\x00" * 32000

    try:
        res_doc = await speech_gateway.transcribe(
            audio_bytes=audio_bytes,
            provider=provider,
            model=model,
            user_id=user_id,
            language=language,
        )
        return res_doc.model_dump()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/providers")
async def list_speech_providers():
    """List registered speech recognition provider adapters."""
    return {"providers": speech_provider_registry.list_providers()}


@router.get("/models")
async def list_speech_models():
    """List registered speech recognition models with per-minute USD rates."""
    models = speech_model_registry.list_models()
    return [m.model_dump() for m in models]


@router.get("/sessions")
async def list_speech_sessions(
    status: Optional[str] = Query(None),
    limit: int = Query(30, ge=1, le=100),
):
    """List active and historical STT transcription sessions."""
    query = SpeechSessionDocument.find_all()
    if status:
        query = SpeechSessionDocument.find(SpeechSessionDocument.status == status)

    docs = await query.sort("-started_at").limit(limit).to_list()
    return [d.model_dump() for d in docs]


@router.get("/costs")
async def list_speech_costs(
    user_id: Optional[str] = Query(None),
    limit: int = Query(30, ge=1, le=100),
):
    """Query cumulative STT transcription expenditure."""
    query = SpeechCostDocument.find_all()
    if user_id:
        query = SpeechCostDocument.find(SpeechCostDocument.user_id == user_id)

    docs = await query.sort("-timestamp").limit(limit).to_list()
    return [d.model_dump() for d in docs]


@router.get("/benchmarks")
async def get_speech_benchmarks():
    """List Word Error Rate (WER) and latency benchmarks across speech models."""
    docs = await SpeechBenchmarkDocument.find_all().to_list()
    if not docs:
        docs = await speech_benchmark_engine.run_benchmark_suite()
    return [d.model_dump() for d in docs]


# ─── WEBSOCKET STREAMING ENDPOINT ──────────────────────────────────────────────

@router.websocket("/ws/transcribe/{session_id}")
async def speech_streaming_websocket(
    websocket: WebSocket,
    session_id: str,
    provider: str = Query("whisper"),
    model: str = Query("whisper-1"),
    token: str = Query("valid_token"),
):
    """
    Real-time streaming speech transcription WebSocket endpoint.
    Receives continuous binary audio chunks and emits partial transcript frames.
    """
    await websocket.accept()
    await websocket.send_json({
        "type": "stt_connection_started",
        "session_id": session_id,
        "provider": provider,
        "model": model,
    })

    try:
        while True:
            message = await websocket.receive()
            if "bytes" in message and message["bytes"]:
                chunk = message["bytes"]

                # Process chunk through Speech Gateway
                res_doc = await speech_gateway.transcribe(
                    audio_bytes=chunk,
                    provider=provider,
                    model=model,
                    session_id=session_id,
                )

                # Emit partial transcript frame
                await websocket.send_json({
                    "type": "partial_transcript",
                    "session_id": session_id,
                    "transcript": res_doc.transcript_text,
                    "confidence": res_doc.confidence_score,
                    "language": res_doc.detected_language,
                    "is_partial": True,
                })

            elif "text" in message and message["text"]:
                import json
                try:
                    data = json.loads(message["text"])
                    if data.get("type") == "stop":
                        await websocket.send_json({"type": "stt_session_stopped", "session_id": session_id})
                        break
                except json.JSONDecodeError:
                    pass

    except Exception as e:
        logger.warning(f"Speech STT WebSocket error session '{session_id}': {e}")
    finally:
        await websocket.close()
