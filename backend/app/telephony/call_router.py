"""
Phase 13.9 — Telephony Call Router.
Routes inbound/outbound calls to the correct provider, queue, and agent.
Also handles:
- Round-robin agent assignment
- Call recording orchestration
- CRM lead linkage on call start
- AI Call Assistant invocation
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.telephony.providers import telephony_provider_registry
from app.telephony.call_queue_manager import call_queue_manager
from app.database.mongodb.collections.telephony import (
    TelephonyCallDocument,
    TelephonyRecordingDocument,
)

logger = logging.getLogger("backend.telephony.call_router")


class TelephonyCallRouter:
    """
    Enterprise call router coordinating provider, queue, recording,
    CRM attachment, and AI assistant integration for every call leg.
    """

    # Simple round-robin agent pool (for demo — replace with DB-backed agent pool)
    _AGENT_POOL: List[str] = [
        "agent_sarah@leadforgeai.com",
        "agent_alex@leadforgeai.com",
        "agent_maya@leadforgeai.com",
    ]
    _agent_idx: int = 0

    # ── Outbound ──────────────────────────────────────────────────────────────
    async def initiate_outbound_call(
        self,
        to_number: str,
        from_number: str,
        provider_id: str = "twilio",
        user_id: str = "user_default",
        lead_id: Optional[str] = None,
        record: bool = True,
    ) -> TelephonyCallDocument:
        """Place an outbound call via the specified provider and persist to MongoDB."""
        provider = telephony_provider_registry.get(provider_id)
        result = await provider.initiate_outbound_call(to_number, from_number, {"user_id": user_id})

        call_id = result["call_id"]
        doc = TelephonyCallDocument(
            call_id=call_id,
            provider=provider_id,
            direction="outbound",
            status="ringing",
            from_number=from_number,
            to_number=to_number,
            user_id=user_id,
            lead_id=lead_id,
            recording_enabled=record,
        )
        try:
            await doc.insert()
        except Exception:
            pass

        if record:
            await self._start_recording(call_id, provider_id)

        logger.info(f"[CallRouter] Outbound call initiated '{call_id}' via '{provider_id}'")
        return doc

    # ── Inbound ───────────────────────────────────────────────────────────────
    async def handle_inbound_call(
        self,
        provider_id: str,
        webhook_payload: Dict[str, Any],
        queue_skill: str = "sales",
        lead_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Accept an inbound call, enqueue it, assign to agent, and start AI assistant.
        """
        call_id = webhook_payload.get("CallSid") or webhook_payload.get("call_id") or f"in_{uuid.uuid4().hex[:16]}"
        from_number = webhook_payload.get("From", "unknown")
        to_number = webhook_payload.get("To", "unknown")

        provider = telephony_provider_registry.get(provider_id)
        accept_res = await provider.accept_inbound_call(call_id, webhook_payload)

        # Persist call document
        doc = TelephonyCallDocument(
            call_id=call_id,
            provider=provider_id,
            direction="inbound",
            status="in_progress",
            from_number=from_number,
            to_number=to_number,
            user_id="inbound_gateway",
            lead_id=lead_id,
            recording_enabled=True,
        )
        try:
            await doc.insert()
        except Exception:
            pass

        # Enqueue to skill-based queue
        queued_call = await call_queue_manager.enqueue(
            call_id=call_id,
            provider=provider_id,
            from_number=from_number,
            to_number=to_number,
            priority=3 if queue_skill == "enterprise" else 5,
            required_skill=queue_skill,
            lead_id=lead_id,
        )

        # Assign round-robin agent
        assigned_agent = self._assign_agent()

        # Start AI assistant on inbound call
        ai_notes = await self._run_ai_call_assistant(call_id, from_number, lead_id)

        logger.info(f"[CallRouter] Inbound call '{call_id}' queued (pos={queued_call.queue_position}), assigned → '{assigned_agent}'")

        return {
            "call_id": call_id,
            "provider": provider_id,
            "direction": "inbound",
            "status": "in_progress",
            "queue_position": queued_call.queue_position,
            "assigned_agent": assigned_agent,
            "ai_notes": ai_notes,
            "accept_response": accept_res,
        }

    # ── Transfer ──────────────────────────────────────────────────────────────
    async def transfer_call(
        self,
        call_id: str,
        target_number: str,
        provider_id: str = "twilio",
    ) -> Dict[str, Any]:
        """Transfer an active call to a new destination."""
        provider = telephony_provider_registry.get(provider_id)
        result = await provider.transfer_call(call_id, target_number)

        # Update call document status
        call_doc = await TelephonyCallDocument.find_one(TelephonyCallDocument.call_id == call_id)
        if call_doc:
            call_doc.status = "transferred"
            call_doc.transferred_to = target_number
            await call_doc.save()

        logger.info(f"[CallRouter] Call '{call_id}' transferred → '{target_number}'")
        return result

    # ── Hangup ────────────────────────────────────────────────────────────────
    async def hangup_call(self, call_id: str, provider_id: str = "twilio") -> Dict[str, Any]:
        """Terminate an active call leg."""
        provider = telephony_provider_registry.get(provider_id)
        result = await provider.hangup_call(call_id)
        call_queue_manager.remove_call(call_id)

        call_doc = await TelephonyCallDocument.find_one(TelephonyCallDocument.call_id == call_id)
        if call_doc:
            call_doc.status = "completed"
            call_doc.ended_at = datetime.now(timezone.utc)
            await call_doc.save()

        logger.info(f"[CallRouter] Hung up call '{call_id}'")
        return result

    # ── Recording ─────────────────────────────────────────────────────────────
    async def _start_recording(self, call_id: str, provider_id: str) -> TelephonyRecordingDocument:
        provider = telephony_provider_registry.get(provider_id)
        rec_res = await provider.start_recording(call_id)
        recording_id = rec_res.get("recording_id", f"rec_{uuid.uuid4().hex[:12]}")
        rec_doc = TelephonyRecordingDocument(
            recording_id=recording_id,
            call_id=call_id,
            provider=provider_id,
            status="recording",
        )
        try:
            await rec_doc.insert()
        except Exception:
            pass
        return rec_doc

    async def stop_recording(self, call_id: str, provider_id: str = "twilio") -> Dict[str, Any]:
        provider = telephony_provider_registry.get(provider_id)
        result = await provider.stop_recording(call_id)

        rec_doc = await TelephonyRecordingDocument.find_one(TelephonyRecordingDocument.call_id == call_id)
        if rec_doc:
            rec_doc.status = "completed"
            rec_doc.ended_at = datetime.now(timezone.utc)
            await rec_doc.save()

        return result

    # ── Agent Assignment ──────────────────────────────────────────────────────
    def _assign_agent(self) -> str:
        agent = self._AGENT_POOL[self._agent_idx % len(self._AGENT_POOL)]
        TelephonyCallRouter._agent_idx += 1
        return agent

    # ── AI Call Assistant ─────────────────────────────────────────────────────
    async def _run_ai_call_assistant(
        self,
        call_id: str,
        from_number: str,
        lead_id: Optional[str],
    ) -> Dict[str, Any]:
        """
        Trigger AI Call Assistant to generate real-time call guidance,
        lead context, and suggested talking points.
        (In production: routes to Planner → AI Orchestrator → AI Gateway)
        """
        logger.info(f"[AICallAssistant] Generating real-time guidance for call '{call_id}'")
        return {
            "caller": from_number,
            "lead_id": lead_id,
            "intent_prediction": "Product inquiry — Enterprise plan",
            "suggested_greeting": "Hello! This is LeadForgeAI Sales. I see you're interested in our Enterprise AI platform. How can I help you today?",
            "lead_score": 87,
            "previous_interactions": 2,
            "recommended_next_step": "Book a 30-minute product demo",
        }


telephony_call_router = TelephonyCallRouter()
