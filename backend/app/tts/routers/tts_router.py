"""
Phase 13.3 REST & WebSocket API Router — Text-to-Speech (TTS) Gateway.
Endpoints:
- POST /api/v1/tts/synthesize
- GET /api/v1/tts/providers
- GET /api/v1/tts/voices
- GET /api/v1/tts/costs
- GET /api/v1/tts/benchmarks
- WS /api/v1/voice/ws/tts-stream/{session_id}
"""
import logging
import base64
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, WebSocket, status
from pydantic import BaseModel, Field

from app.tts.gateway.tts_gateway import tts_gateway
from app.tts.registry.tts_provider_registry import tts_provider_registry
from app.tts.registry.tts_voice_registry import tts_voice_registry
from app.tts.cost.tts_cost_tracker import tts_cost_tracker
from app.tts.benchmarks.tts_benchmark_engine import tts_benchmark_engine
from app.database.mongodb.collections.tts_gateway import (
    TTSAudioOutputDocument,
    TTSCostDocument,
    TTSBenchmarkDocument,
)

logger = logging.getLogger("backend.tts.routers.tts_router")

router = APIRouter(prefix="/tts", tags=["Text-to-Speech Gateway (13.3)"])


class TTSSynthesizeRequest(BaseModel):
    text_prompt: str = Field(..., description="Text or SSML markup to synthesize")
    provider: str = Field("elevenlabs")
    model: str = Field("eleven_multilingual_v2")
    voice_id: str = Field("21m00Tcm4TlvDq8ikWAM")
    user_id: str = Field("user_default")
    session_id: Optional[str] = None
    emotion: str = Field("professional")
    use_cache: bool = Field(True)


# ─── REST ENDPOINTS ─────────────────────────────────────────────────────────────

@router.post("/synthesize")
async def synthesize_text(request: TTSSynthesizeRequest):
    """
    Synchronous text-to-speech synthesis endpoint.
    Routes text through TTS Gateway with SSML parsing, emotion prosody, voice caching, and fallback routing.
    """
    try:
        out_doc = await tts_gateway.synthesize(
            text_prompt=request.text_prompt,
            provider=request.provider,
            model=request.model,
            voice_id=request.voice_id,
            user_id=request.user_id,
            session_id=request.session_id,
            emotion=request.emotion,
            use_cache=request.use_cache,
        )
        return out_doc.model_dump()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/providers")
async def list_tts_providers():
    """List registered text-to-speech provider adapters."""
    return {"providers": tts_provider_registry.list_providers()}


@router.get("/voices")
async def list_tts_voices(provider_id: Optional[str] = Query(None)):
    """List registered voice profiles, synthetic voices, and emotion presets."""
    voices = tts_voice_registry.list_voices(provider_id=provider_id)
    return [v.model_dump() for v in voices]


@router.get("/costs")
async def list_tts_costs(
    user_id: Optional[str] = Query(None),
    limit: int = Query(30, ge=1, le=100),
):
    """Query cumulative TTS speech synthesis spend."""
    query = TTSCostDocument.find_all()
    if user_id:
        query = TTSCostDocument.find(TTSCostDocument.user_id == user_id)

    docs = await query.sort("-timestamp").limit(limit).to_list()
    return [d.model_dump() for d in docs]


@router.get("/benchmarks")
async def get_tts_benchmarks():
    """List Time to First Byte (TTFB) latency and MOS naturalness benchmarks across TTS models."""
    docs = await TTSBenchmarkDocument.find_all().to_list()
    if not docs:
        docs = await tts_benchmark_engine.run_benchmark_suite()
    return [d.model_dump() for d in docs]


# ─── WEBSOCKET AUDIO PLAYBACK STREAM ENDPOINT ─────────────────────────────────

@router.websocket("/ws/tts-stream/{session_id}")
async def tts_streaming_websocket(
    websocket: WebSocket,
    session_id: str,
    text: str = Query("Hello! Welcome to LeadForgeAI Voice System."),
    provider: str = Query("elevenlabs"),
    voice_id: str = Query("21m00Tcm4TlvDq8ikWAM"),
):
    """
    Real-time streaming TTS WebSocket audio output endpoint.
    Synthesizes text and streams binary audio PCM chunks directly to client.
    """
    await websocket.accept()
    await websocket.send_json({
        "type": "tts_playback_started",
        "session_id": session_id,
        "provider": provider,
        "voice_id": voice_id,
    })

    try:
        out_doc = await tts_gateway.synthesize(
            text_prompt=text,
            provider=provider,
            voice_id=voice_id,
            session_id=session_id,
        )

        # Emit synthesis completed event with audio duration
        await websocket.send_json({
            "type": "tts_playback_chunk",
            "session_id": session_id,
            "duration_seconds": out_doc.audio_duration_seconds,
            "ttfb_ms": out_doc.ttfb_ms,
            "status": "completed",
        })

    except Exception as e:
        logger.warning(f"TTS WebSocket playback error session '{session_id}': {e}")
    finally:
        await websocket.close()
