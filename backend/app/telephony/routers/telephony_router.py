"""
Phase 13.9 — Enterprise Telephony REST API Router.
Endpoints:
  POST /api/v1/telephony/call/outbound         — Initiate outbound call
  POST /api/v1/telephony/call/inbound          — Accept inbound call (webhook)
  POST /api/v1/telephony/call/transfer         — Transfer active call
  POST /api/v1/telephony/call/hangup           — Hang up call
  POST /api/v1/telephony/call/recording/stop   — Stop call recording
  POST /api/v1/telephony/call/sentiment        — AI sentiment analysis on transcript segment
  POST /api/v1/telephony/call/summary          — Generate post-call AI summary
  GET  /api/v1/telephony/call/{call_id}        — Get call details
  GET  /api/v1/telephony/calls                 — List calls
  GET  /api/v1/telephony/queue/stats           — Live queue stats
  GET  /api/v1/telephony/queue/calls           — List queued calls
  GET  /api/v1/telephony/providers             — List providers
  GET  /api/v1/telephony/assistant/context     — Pre-call AI context
  GET  /api/v1/telephony/assistant/objection   — Objection handling guide
"""
import logging
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.telephony.call_router import telephony_call_router
from app.telephony.call_queue_manager import call_queue_manager
from app.telephony.ai_call_assistant import ai_call_assistant
from app.telephony.providers import telephony_provider_registry
from app.database.mongodb.collections.telephony import (
    TelephonyCallDocument,
    TelephonyRecordingDocument,
    TelephonyCallSummaryDocument,
    TelephonyQueueEventDocument,
)

logger = logging.getLogger("backend.telephony.router")

router = APIRouter(prefix="/telephony", tags=["Enterprise Telephony (13.9)"])


# ─── Request Models ──────────────────────────────────────────────────────────

class OutboundCallRequest(BaseModel):
    to_number: str = Field(..., description="E.164 formatted destination number e.g. +14155552671")
    from_number: str = Field("+14155550001", description="Caller ID / DID number")
    provider_id: str = Field("twilio", description="twilio | sip | zoom_phone | teams_phone")
    user_id: str = Field("user_default")
    lead_id: Optional[str] = None
    record: bool = Field(True)


class InboundCallWebhookRequest(BaseModel):
    provider_id: str = Field("twilio")
    CallSid: Optional[str] = None
    call_id: Optional[str] = None
    From: Optional[str] = None
    To: Optional[str] = None
    queue_skill: str = Field("sales", description="sales | support | enterprise | general")
    lead_id: Optional[str] = None


class TransferCallRequest(BaseModel):
    call_id: str = Field(...)
    target_number: str = Field(..., description="E.164 transfer destination")
    provider_id: str = Field("twilio")


class HangupCallRequest(BaseModel):
    call_id: str = Field(...)
    provider_id: str = Field("twilio")


class StopRecordingRequest(BaseModel):
    call_id: str = Field(...)
    provider_id: str = Field("twilio")


class SentimentAnalysisRequest(BaseModel):
    call_id: str = Field(...)
    transcript_segment: str = Field(..., description="Transcript text to analyze")


class CallSummaryRequest(BaseModel):
    call_id: str = Field(...)
    full_transcript: str = Field("...")
    duration_seconds: int = Field(0)
    lead_id: Optional[str] = None


# ─── Call Endpoints ──────────────────────────────────────────────────────────

@router.post("/call/outbound")
async def initiate_outbound_call(request: OutboundCallRequest):
    """Initiate an enterprise outbound call via the chosen telephony provider."""
    try:
        doc = await telephony_call_router.initiate_outbound_call(
            to_number=request.to_number,
            from_number=request.from_number,
            provider_id=request.provider_id,
            user_id=request.user_id,
            lead_id=request.lead_id,
            record=request.record,
        )
        return doc.model_dump()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/call/inbound")
async def handle_inbound_call(request: InboundCallWebhookRequest):
    """Accept and route an inbound call from a provider webhook."""
    try:
        payload = request.model_dump()
        result = await telephony_call_router.handle_inbound_call(
            provider_id=request.provider_id,
            webhook_payload=payload,
            queue_skill=request.queue_skill,
            lead_id=request.lead_id,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/call/transfer")
async def transfer_call(request: TransferCallRequest):
    """Transfer an active call to a new destination number."""
    try:
        result = await telephony_call_router.transfer_call(
            call_id=request.call_id,
            target_number=request.target_number,
            provider_id=request.provider_id,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/call/hangup")
async def hangup_call(request: HangupCallRequest):
    """Terminate an active call and mark it completed in the database."""
    try:
        result = await telephony_call_router.hangup_call(
            call_id=request.call_id,
            provider_id=request.provider_id,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/call/recording/stop")
async def stop_recording(request: StopRecordingRequest):
    """Stop an active call recording."""
    try:
        result = await telephony_call_router.stop_recording(
            call_id=request.call_id,
            provider_id=request.provider_id,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/call/{call_id}")
async def get_call(call_id: str):
    """Retrieve full call record including recordings and summary."""
    doc = await TelephonyCallDocument.find_one(TelephonyCallDocument.call_id == call_id)
    if not doc:
        raise HTTPException(status_code=404, detail=f"Call '{call_id}' not found.")
    recordings = await TelephonyRecordingDocument.find(TelephonyRecordingDocument.call_id == call_id).to_list()
    summary = await TelephonyCallSummaryDocument.find_one(TelephonyCallSummaryDocument.call_id == call_id)
    return {
        "call": doc.model_dump(),
        "recordings": [r.model_dump() for r in recordings],
        "summary": summary.model_dump() if summary else None,
    }


@router.get("/calls")
async def list_calls(
    direction: Optional[str] = Query(None, description="inbound | outbound"),
    status: Optional[str] = Query(None),
    provider: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
):
    """List telephony calls with optional filters."""
    query = TelephonyCallDocument.find_all()
    if direction:
        query = TelephonyCallDocument.find(TelephonyCallDocument.direction == direction)
    if status:
        query = TelephonyCallDocument.find(TelephonyCallDocument.status == status)
    if provider:
        query = TelephonyCallDocument.find(TelephonyCallDocument.provider == provider)
    if user_id:
        query = TelephonyCallDocument.find(TelephonyCallDocument.user_id == user_id)
    docs = await query.sort("-created_at").limit(limit).to_list()
    return [d.model_dump() for d in docs]


# ─── Queue Endpoints ─────────────────────────────────────────────────────────

@router.get("/queue/stats")
async def get_queue_stats():
    """Return live call queue depths, average wait times, and top queued calls."""
    return call_queue_manager.queue_stats()


@router.get("/queue/calls")
async def list_queued_calls():
    """List all calls currently waiting in queues."""
    return call_queue_manager.list_queued_calls()


# ─── Provider Endpoints ──────────────────────────────────────────────────────

@router.get("/providers")
async def list_telephony_providers():
    """List all registered telephony providers and their availability."""
    return telephony_provider_registry.list_providers()


# ─── AI Call Assistant Endpoints ─────────────────────────────────────────────

@router.get("/assistant/context")
async def get_call_context(
    call_id: str = Query(...),
    from_number: str = Query("+14155550000"),
    lead_id: Optional[str] = Query(None),
):
    """Retrieve AI-generated pre-call intelligence brief for an inbound caller."""
    try:
        result = await ai_call_assistant.get_call_context(
            call_id=call_id,
            from_number=from_number,
            lead_id=lead_id,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/call/sentiment")
async def analyze_call_sentiment(request: SentimentAnalysisRequest):
    """Run real-time sentiment analysis on a live call transcript segment."""
    try:
        result = await ai_call_assistant.analyze_sentiment(
            call_id=request.call_id,
            transcript_segment=request.transcript_segment,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/call/summary")
async def generate_call_summary(request: CallSummaryRequest):
    """Generate an AI post-call executive summary and queue CRM update."""
    try:
        result = await ai_call_assistant.generate_call_summary(
            call_id=request.call_id,
            full_transcript=request.full_transcript,
            duration_seconds=request.duration_seconds,
            lead_id=request.lead_id,
        )
        # Persist summary to MongoDB
        summary_doc = TelephonyCallSummaryDocument(
            summary_id=result["summary_id"],
            call_id=request.call_id,
            lead_id=request.lead_id,
            executive_summary=result["executive_summary"],
            action_items=result["action_items"],
            sentiment_trend=result["sentiment_trend"],
            duration_seconds=request.duration_seconds,
            crm_update_status="queued",
            followup_email_queued=True,
        )
        try:
            await summary_doc.insert()
        except Exception:
            pass
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/assistant/objection")
async def get_objection_handler(
    objection_type: str = Query("price", description="price | timing | competition"),
):
    """Return AI-scripted objection handling guidance for the specified objection type."""
    try:
        result = await ai_call_assistant.get_objection_handler(objection_type)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
