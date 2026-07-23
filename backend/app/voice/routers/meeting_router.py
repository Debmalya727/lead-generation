"""
Phase 13.7 REST API Router — Enterprise Voice Meeting Assistant.
Endpoints:
- POST /api/v1/voice/meeting/start
- POST /api/v1/voice/meeting/stop
- GET /api/v1/voice/meeting/{meeting_id}
- GET /api/v1/voice/meeting/search
- GET /api/v1/voice/meeting/list
"""
import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.voice.meeting.engine.meeting_assistant import voice_meeting_assistant
from app.database.mongodb.collections.voice_meetings import (
    VoiceMeetingDocument,
    VoiceMeetingSegmentDocument,
    VoiceMeetingActionItemDocument,
    VoiceMeetingSummaryDocument,
)

logger = logging.getLogger("backend.voice.routers.meeting_router")

router = APIRouter(prefix="/voice/meeting", tags=["Voice Meeting Assistant (13.7)"])


class VoiceMeetingStartRequest(BaseModel):
    meeting_url: str = Field(..., description="Google Meet / Teams / Zoom meeting URL")
    title: str = Field("Enterprise Discovery Sync")
    platform: str = Field("google_meet", description="google_meet | teams | zoom | mock")
    user_id: str = Field("user_default")
    lead_id: Optional[str] = None


# ─── REST ENDPOINTS ─────────────────────────────────────────────────────────────

@router.post("/start")
async def start_voice_meeting(request: VoiceMeetingStartRequest):
    """Connect AI Meeting Assistant bot to video conference meeting session."""
    try:
        doc = await voice_meeting_assistant.start_meeting(
            meeting_url=request.meeting_url,
            user_id=request.user_id,
            title=request.title,
            platform=request.platform,
            lead_id=request.lead_id,
        )
        return doc.model_dump()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/stop")
async def stop_voice_meeting(meeting_id: str = Query(...)):
    """Stop active meeting and execute post-meeting intelligence pipelines."""
    try:
        summary_doc = await voice_meeting_assistant.stop_meeting(meeting_id)
        return summary_doc.model_dump()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/search")
async def search_meeting_transcripts(
    q: str = Query(..., min_length=2, description="Search query string"),
    limit: int = Query(20, ge=1, le=100),
):
    """Search meeting transcripts across all recorded video conferencing sessions."""
    segments = await voice_meeting_assistant.search_transcripts(query=q, limit=limit)
    return [s.model_dump() for s in segments]


@router.get("/list")
async def list_voice_meetings(
    user_id: Optional[str] = Query(None),
    platform: Optional[str] = Query(None),
    limit: int = Query(30, ge=1, le=100),
):
    """List historical recorded voice meeting sessions."""
    query = VoiceMeetingDocument.find_all()
    if user_id:
        query = VoiceMeetingDocument.find(VoiceMeetingDocument.user_id == user_id)
    if platform:
        query = VoiceMeetingDocument.find(VoiceMeetingDocument.platform == platform)

    docs = await query.sort("-created_at").limit(limit).to_list()
    return [d.model_dump() for d in docs]


@router.get("/{meeting_id}")
async def get_meeting_details(meeting_id: str):
    """Fetch complete meeting details including diarized transcript segments, action items, and AI executive summary."""
    doc = await VoiceMeetingDocument.find_one(VoiceMeetingDocument.meeting_id == meeting_id)
    if not doc:
        raise HTTPException(status_code=404, detail=f"Meeting '{meeting_id}' not found.")

    segments = await VoiceMeetingSegmentDocument.find(VoiceMeetingSegmentDocument.meeting_id == meeting_id).to_list()
    action_items = await VoiceMeetingActionItemDocument.find(VoiceMeetingActionItemDocument.meeting_id == meeting_id).to_list()
    summary = await VoiceMeetingSummaryDocument.find_one(VoiceMeetingSummaryDocument.meeting_id == meeting_id)

    return {
        "meeting": doc.model_dump(),
        "segments": [s.model_dump() for s in segments],
        "action_items": [a.model_dump() for a in action_items],
        "summary": summary.model_dump() if summary else None,
    }
