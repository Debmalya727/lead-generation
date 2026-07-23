"""
Phase 13.8 REST API Router — Conversational Voice Agents.
Endpoints:
- POST /api/v1/voice/agent/turn
- POST /api/v1/voice/agent/handoff
- GET /api/v1/voice/agent/personas
- GET /api/v1/voice/agent/session/{session_id}
"""
import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.voice.agents.persona_registry import voice_persona_registry
from app.voice.agents.conversational_voice_agent import conversational_voice_agent
from app.voice.agents.human_handoff_engine import human_handoff_engine
from app.database.mongodb.collections.voice_agents import (
    VoiceAgentSessionDocument,
    VoiceAgentTurnDocument,
)

logger = logging.getLogger("backend.voice.routers.voice_agent_router")

router = APIRouter(prefix="/voice/agent", tags=["Conversational Voice Agents (13.8)"])


class VoiceAgentTurnRequest(BaseModel):
    session_id: Optional[str] = None
    persona_id: str = Field("sdr_persona")
    user_transcript: str = Field(..., description="User voice speech transcript")
    user_id: str = Field("user_default")
    is_interruption: bool = Field(False)


class VoiceAgentHandoffRequest(BaseModel):
    session_id: str = Field(...)
    reason: str = Field("User requested human agent transfer")


# ─── REST ENDPOINTS ─────────────────────────────────────────────────────────────

@router.post("/turn")
async def process_voice_agent_turn(request: VoiceAgentTurnRequest):
    """Process a multi-turn voice dialogue speech turn."""
    try:
        sess_id = request.session_id
        if not sess_id:
            sess_doc = await conversational_voice_agent.start_agent_session(
                user_id=request.user_id,
                persona_id=request.persona_id,
            )
            sess_id = sess_doc.session_id

        res = await conversational_voice_agent.process_voice_turn(
            session_id=sess_id,
            user_transcript=request.user_transcript,
            is_interruption=request.is_interruption,
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/handoff")
async def trigger_human_handoff(request: VoiceAgentHandoffRequest):
    """Initiate human handoff protocol for active voice AI session."""
    try:
        res = await human_handoff_engine.execute_handoff(
            session_id=request.session_id,
            reason=request.reason,
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/personas")
async def list_voice_agent_personas():
    """List available Conversational Voice Agent personas."""
    return voice_persona_registry.list_personas()


@router.get("/session/{session_id}")
async def get_voice_agent_session(session_id: str):
    """Fetch active session details and turn history."""
    sess_doc = await VoiceAgentSessionDocument.find_one(VoiceAgentSessionDocument.session_id == session_id)
    if not sess_doc:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")

    turns = await VoiceAgentTurnDocument.find(VoiceAgentTurnDocument.session_id == session_id).sort("turn_index").to_list()
    return {
        "session": sess_doc.model_dump(),
        "turns": [t.model_dump() for t in turns],
    }
