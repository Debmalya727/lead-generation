"""
Phase 13.4 REST & WebSocket API Router — Real-Time Bidirectional Voice AI Streaming Engine.
Endpoints:
- POST /api/v1/voice/bidirectional/start
- POST /api/v1/voice/bidirectional/stop
- GET /api/v1/voice/bidirectional/sessions
- GET /api/v1/voice/bidirectional/metrics
- WS /api/v1/voice/ws/bidirectional/{session_id}
"""
import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, WebSocket, status
from pydantic import BaseModel, Field

from app.voice.bidirectional.bidirectional_orchestrator import bidirectional_orchestrator
from app.voice.bidirectional.interruption_handler import interruption_handler
from app.database.mongodb.collections.bidirectional_voice import (
    BidirectionalSessionDocument,
    BidirectionalTurnDocument,
    BidirectionalMetricsDocument,
)

logger = logging.getLogger("backend.voice.routers.bidirectional_router")

router = APIRouter(prefix="/voice/bidirectional", tags=["Real-Time Bidirectional Voice (13.4)"])


class BidirectionalStartRequest(BaseModel):
    user_id: str = Field(...)
    stt_provider: str = Field("whisper")
    stt_model: str = Field("whisper-1")
    tts_provider: str = Field("elevenlabs")
    tts_voice_id: str = Field("21m00Tcm4TlvDq8ikWAM")
    emotion: str = Field("professional")


# ─── REST ENDPOINTS ─────────────────────────────────────────────────────────────

@router.post("/start")
async def start_bidirectional_session(request: BidirectionalStartRequest):
    """Start a full-duplex Speech-to-Speech AI session."""
    try:
        doc = await bidirectional_orchestrator.start_duplex_session(
            user_id=request.user_id,
            stt_provider=request.stt_provider,
            stt_model=request.stt_model,
            tts_provider=request.tts_provider,
            tts_voice_id=request.tts_voice_id,
            emotion=request.emotion,
        )
        return doc.model_dump()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/stop")
async def stop_bidirectional_session(session_id: str = Query(...)):
    """Close an active full-duplex session."""
    doc = await BidirectionalSessionDocument.find_one(BidirectionalSessionDocument.session_id == session_id)
    if not doc:
        raise HTTPException(status_code=404, detail=f"Duplex session '{session_id}' not found.")

    doc.status = "closed"
    await doc.save()
    return doc.model_dump()


@router.get("/sessions")
async def list_bidirectional_sessions(
    user_id: Optional[str] = Query(None),
    limit: int = Query(30, ge=1, le=100),
):
    """Query active/past bidirectional Speech-to-Speech sessions."""
    query = BidirectionalSessionDocument.find_all()
    if user_id:
        query = BidirectionalSessionDocument.find(BidirectionalSessionDocument.user_id == user_id)

    docs = await query.sort("-started_at").limit(limit).to_list()
    return [d.model_dump() for d in docs]


@router.get("/metrics")
async def get_bidirectional_metrics(
    session_id: Optional[str] = Query(None),
    limit: int = Query(30, ge=1, le=100),
):
    """Query real-time Speech-to-Speech latency telemetry metrics."""
    query = BidirectionalMetricsDocument.find_all()
    if session_id:
        query = BidirectionalMetricsDocument.find(BidirectionalMetricsDocument.session_id == session_id)

    docs = await query.sort("-recorded_at").limit(limit).to_list()
    return [d.model_dump() for d in docs]


# ─── WEBSOCKET FULL DUPLEX STREAM ENDPOINT ────────────────────────────────────

@router.websocket("/ws/{session_id}")
async def bidirectional_websocket_endpoint(
    websocket: WebSocket,
    session_id: str,
    user_id: str = Query("user_default"),
    stt_provider: str = Query("whisper"),
    tts_provider: str = Query("elevenlabs"),
    tts_voice_id: str = Query("21m00Tcm4TlvDq8ikWAM"),
):
    """
    Real-Time Full-Duplex Speech-to-Speech WebSocket streaming endpoint.
    Receives incoming user audio PCM chunks, transcribes speech, invokes LLM, synthesizes TTS audio, and streams audio back to browser player.
    """
    await websocket.accept()
    await websocket.send_json({
        "type": "duplex_connection_accepted",
        "session_id": session_id,
        "status": "active",
    })

    try:
        while True:
            message = await websocket.receive()
            if "bytes" in message and message["bytes"]:
                chunk = message["bytes"]

                # Process user speech turn through Bidirectional Voice Orchestrator
                turn_result = await bidirectional_orchestrator.process_user_audio_turn(
                    session_id=session_id,
                    user_id=user_id,
                    pcm_bytes=chunk,
                    stt_provider=stt_provider,
                    tts_provider=tts_provider,
                    tts_voice_id=tts_voice_id,
                )

                # Emit turn result frame
                await websocket.send_json({
                    "type": "speech_to_speech_turn",
                    "session_id": session_id,
                    "user_transcript": turn_result["user_transcript"],
                    "assistant_response": turn_result["assistant_response"],
                    "e2e_latency_ms": turn_result["e2e_latency_ms"],
                    "was_interrupted": turn_result["was_interrupted"],
                })

            elif "text" in message and message["text"]:
                import json
                try:
                    data = json.loads(message["text"])
                    if data.get("type") == "interrupt":
                        await interruption_handler.handle_interruption(session_id)
                        await websocket.send_json({"type": "playback_flushed", "session_id": session_id})
                    elif data.get("type") == "stop":
                        await websocket.send_json({"type": "duplex_session_stopped", "session_id": session_id})
                        break
                except json.JSONDecodeError:
                    pass

    except Exception as e:
        logger.warning(f"Full-duplex WebSocket error session '{session_id}': {e}")
    finally:
        await websocket.close()
