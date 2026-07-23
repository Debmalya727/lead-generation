"""
Phase 13.1 REST & WebSocket API Router — Enterprise Voice Infrastructure.
Endpoints:
- GET /api/v1/voice/sessions
- GET /api/v1/voice/session/{id}
- GET /api/v1/voice/events
- GET /api/v1/voice/metrics
- POST /api/v1/voice/session/start
- POST /api/v1/voice/session/stop
- WS /api/v1/voice/ws/{session_id}
"""
import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, WebSocket, status

from app.voice.sessions.session_manager import voice_session_manager
from app.voice.sessions.schemas import VoiceSessionCreate, VoiceSessionUpdate
from app.voice.gateway.gateway import voice_gateway
from app.voice.vad.vad_engine import vad_engine
from app.voice.audio.buffer_manager import buffer_manager
from app.voice.streaming.chunk_manager import chunk_manager
from app.voice.events.voice_events import voice_event_publisher
from app.database.mongodb.collections.voice_infrastructure import (
    VoiceSessionDocument,
    VoiceEventDocument,
    VoiceMetricsDocument,
)

logger = logging.getLogger("backend.voice.routers.voice_router")

router = APIRouter(prefix="/voice", tags=["Enterprise Voice Infrastructure (13.1)"])


# ─── REST ENDPOINTS ─────────────────────────────────────────────────────────────

@router.get("/sessions")
async def list_voice_sessions(
    status: Optional[str] = Query(None),
    limit: int = Query(30, ge=1, le=100),
):
    """List historical and active enterprise voice sessions."""
    query = VoiceSessionDocument.find_all()
    if status:
        query = VoiceSessionDocument.find(VoiceSessionDocument.status == status)

    docs = await query.sort("-started_at").limit(limit).to_list()
    return [d.model_dump() for d in docs]


@router.get("/session/{id}")
async def get_voice_session(id: str):
    """Get voice session details by ID."""
    doc = await voice_session_manager.get_session(id)
    if not doc:
        raise HTTPException(status_code=404, detail=f"Voice session '{id}' not found.")
    return doc.model_dump()


@router.post("/session/start")
async def start_voice_session(request: VoiceSessionCreate):
    """Initialize a new enterprise voice session."""
    try:
        doc = await voice_session_manager.create_session(request)
        await voice_event_publisher.emit("VoiceConnected", doc.session_id, {"user_id": request.user_id})
        return doc.model_dump()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/session/stop")
async def stop_voice_session(session_id: str = Query(...)):
    """Stop and close an active voice session."""
    doc = await voice_session_manager.stop_session(session_id)
    if not doc:
        raise HTTPException(status_code=404, detail=f"Active session '{session_id}' not found.")
    await voice_event_publisher.emit("SessionClosed", session_id)
    buffer_manager.remove_session_buffer(session_id)
    return doc.model_dump()


@router.get("/events")
async def list_voice_events(
    session_id: Optional[str] = Query(None),
    event_type: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
):
    """Query voice infrastructure event logs."""
    query = VoiceEventDocument.find_all()
    if session_id:
        query = VoiceEventDocument.find(VoiceEventDocument.session_id == session_id)
    if event_type:
        query = VoiceEventDocument.find(VoiceEventDocument.event_type == event_type)

    docs = await query.sort("-timestamp").limit(limit).to_list()
    return [d.model_dump() for d in docs]


@router.get("/metrics")
async def get_voice_metrics(
    session_id: Optional[str] = Query(None),
    limit: int = Query(30, ge=1, le=100),
):
    """Query real-time latency, jitter, and packet loss metrics."""
    query = VoiceMetricsDocument.find_all()
    if session_id:
        query = VoiceMetricsDocument.find(VoiceMetricsDocument.session_id == session_id)

    docs = await query.sort("-recorded_at").limit(limit).to_list()
    return [d.model_dump() for d in docs]


# ─── WEBSOCKET ENDPOINT ─────────────────────────────────────────────────────────

@router.websocket("/ws/{session_id}")
async def voice_websocket_endpoint(
    websocket: WebSocket,
    session_id: str,
    token: str = Query("valid_token"),
):
    """
    Real-time audio streaming WebSocket endpoint.
    Handles binary audio frames (PCM/Opus) and JSON control messages.
    """

    async def on_audio_chunk(s_id: str, chunk_bytes: bytes):
        # 1. Format chunk
        chunk_manager.create_chunk(s_id, chunk_bytes)

        # 2. Write to Circular Buffer
        buffer_manager.write_chunk(s_id, chunk_bytes)

        # 3. Analyze Voice Activity (VAD)
        vad_res = vad_engine.process_frame(s_id, chunk_bytes)
        if vad_res.event_type:
            await voice_event_publisher.emit(vad_res.event_type, s_id, {
                "energy_db": vad_res.energy_db,
                "zcr": vad_res.zcr,
            })

    async def on_control_frame(s_id: str, data: Dict[str, Any]):
        msg_type = data.get("type")
        if msg_type == "stop":
            await voice_session_manager.stop_session(s_id)
            await voice_event_publisher.emit("VoiceDisconnected", s_id)

    await voice_gateway.handle_websocket_session(
        session_id=session_id,
        token=token,
        websocket=websocket,
        on_audio_chunk=on_audio_chunk,
        on_control_frame=on_control_frame,
    )
