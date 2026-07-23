"""
HumanHandoffEngine — Handles seamless voice session transfer to human sales/support representatives.
"""
from typing import Dict, Any, Tuple, Optional
import logging

from app.database.mongodb.collections.voice_agents import VoiceAgentSessionDocument

logger = logging.getLogger("backend.voice.agents.handoff")


class HumanHandoffEngine:
    """Evaluates handoff triggers and transfers voice AI sessions to human agents."""

    def should_trigger_handoff(self, user_transcript: str, confidence: float = 0.95) -> Tuple[bool, str]:
        """
        Check if user requested human handoff or if AI confidence dropped.
        Returns: (should_handoff, reason)
        """
        lower = user_transcript.lower()

        handoff_phrases = [
            "speak to a human",
            "talk to a person",
            "connect me to a representative",
            "transfer me to sales",
            "real person",
            "human agent",
        ]
        for phrase in handoff_phrases:
            if phrase in lower:
                return True, f"User explicitly requested human handoff: '{phrase}'"

        if confidence < 0.60:
            return True, f"Low speech recognition confidence ({confidence:.2f})"

        return False, ""

    async def execute_handoff(self, session_id: str, reason: str) -> Dict[str, Any]:
        """Mark session as transferred and assign human agent queue."""
        sess_doc = await VoiceAgentSessionDocument.find_one(VoiceAgentSessionDocument.session_id == session_id)
        if sess_doc:
            sess_doc.status = "handed_off"
            sess_doc.human_handoff_status = "transferred"
            await sess_doc.save()

        logger.info(f"HumanHandoffEngine: Transferred session '{session_id}' to human agent queue. Reason: {reason}")
        return {
            "session_id": session_id,
            "status": "transferred",
            "human_agent_queue": "tier1_sales_reps",
            "reason": reason,
            "message": "Transferring call to human sales representative now...",
        }


human_handoff_engine = HumanHandoffEngine()
