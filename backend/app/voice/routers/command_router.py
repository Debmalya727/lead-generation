"""
Phase 13.6 REST API Router — Voice Command Planner Integration.
Endpoints:
- POST /api/v1/voice/command/execute
- POST /api/v1/voice/command/confirm
- GET /api/v1/voice/command/history
- GET /api/v1/voice/command/intents
"""
import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.voice.commands.voice_planner_adapter import voice_planner_adapter
from app.voice.commands.voice_command_history import voice_command_history
from app.database.mongodb.collections.voice_commands import (
    VoiceCommandLogDocument,
    VoiceConfirmationDocument,
)

logger = logging.getLogger("backend.voice.routers.command_router")

router = APIRouter(prefix="/voice/command", tags=["Voice Command Planner (13.6)"])


class VoiceCommandExecuteRequest(BaseModel):
    transcript: str = Field(..., description="Voice transcript command string")
    user_id: str = Field("user_default")
    session_id: Optional[str] = None
    bypass_confirmation: bool = Field(False)


class VoiceCommandConfirmRequest(BaseModel):
    confirmation_id: str = Field(...)
    user_id: str = Field("user_default")
    confirmed: bool = Field(True, description="True to approve execution, False to reject")


# ─── REST ENDPOINTS ─────────────────────────────────────────────────────────────

@router.post("/execute")
async def execute_voice_command(request: VoiceCommandExecuteRequest):
    """
    Execute a voice command through the AI Planner & AI Workflow Orchestrator.
    Supports intent parsing, parameter extraction, ambiguity detection, and confirmation policy.
    """
    try:
        res = await voice_planner_adapter.execute_voice_command(
            transcript=request.transcript,
            user_id=request.user_id,
            session_id=request.session_id,
            bypass_confirmation=request.bypass_confirmation,
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/confirm")
async def confirm_voice_command(request: VoiceCommandConfirmRequest):
    """Confirm or reject a pending high-stakes voice command action."""
    conf = await VoiceConfirmationDocument.find_one(VoiceConfirmationDocument.confirmation_id == request.confirmation_id)
    if not conf:
        raise HTTPException(status_code=404, detail=f"Confirmation ID '{request.confirmation_id}' not found.")

    conf.status = "confirmed" if request.confirmed else "rejected"
    await conf.save()

    return {
        "confirmation_id": request.confirmation_id,
        "status": conf.status,
        "action_description": conf.action_description,
    }


@router.get("/history")
async def get_voice_command_history(
    user_id: Optional[str] = Query(None),
    limit: int = Query(30, ge=1, le=100),
):
    """Query voice command execution logs and status history."""
    query = VoiceCommandLogDocument.find_all()
    if user_id:
        query = VoiceCommandLogDocument.find(VoiceCommandLogDocument.user_id == user_id)

    docs = await query.sort("-created_at").limit(limit).to_list()
    return [d.model_dump() for d in docs]


@router.get("/intents")
async def list_voice_command_intents():
    """List supported voice command intents and parameter requirements."""
    return {
        "supported_intents": [
            {
                "intent": "RESEARCH_COMPANY",
                "example": "Research Tesla",
                "parameters": ["company_name"],
                "requires_confirmation": False,
            },
            {
                "intent": "FIND_LEADS",
                "example": "Find CEOs",
                "parameters": ["job_title"],
                "requires_confirmation": False,
            },
            {
                "intent": "GENERATE_OUTREACH",
                "example": "Generate Outreach",
                "parameters": ["campaign_type"],
                "requires_confirmation": True,
            },
            {
                "intent": "SCHEDULE_MEETING",
                "example": "Schedule Meeting",
                "parameters": ["meeting_type"],
                "requires_confirmation": True,
            },
            {
                "intent": "SUMMARIZE_CRM",
                "example": "Summarize CRM",
                "parameters": ["scope"],
                "requires_confirmation": False,
            },
        ]
    }
