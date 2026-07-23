"""
ConfirmationEngine — High-stakes action confirmation policy requiring explicit user confirmation before executing risky operations.
High-stakes operations: GENERATE_OUTREACH (sending emails), SCHEDULE_MEETING (booking calendar).
"""
import uuid
from typing import Dict, Any, Tuple, Optional
import logging

from app.voice.commands.voice_command_parser import ParsedVoiceCommand
from app.database.mongodb.collections.voice_commands import VoiceConfirmationDocument

logger = logging.getLogger("backend.voice.commands.confirmation")


class ConfirmationEngine:
    """Evaluates action risk score and manages voice confirmation prompts."""

    def requires_confirmation(self, cmd: ParsedVoiceCommand) -> Tuple[bool, Optional[str], str]:
        """
        Check if voice command requires explicit confirmation before execution.
        Returns: (requires_confirmation, action_description, risk_level)
        """
        high_stakes_intents = {
            "GENERATE_OUTREACH": ("Generate & dispatch automated email sequence to target leads", "high"),
            "SCHEDULE_MEETING": ("Book calendar meeting invite and send notification to prospect", "high"),
        }

        if cmd.intent in high_stakes_intents:
            desc, risk = high_stakes_intents[cmd.intent]
            return True, desc, risk

        return False, None, "low"

    async def create_confirmation_prompt(
        self,
        command_id: str,
        user_id: str,
        action_description: str,
        risk_level: str = "high",
    ) -> VoiceConfirmationDocument:
        """Create pending confirmation document in MongoDB."""
        conf_id = f"v_conf_{uuid.uuid4().hex[:12]}"

        doc = VoiceConfirmationDocument(
            confirmation_id=conf_id,
            command_id=command_id,
            user_id=user_id,
            action_description=action_description,
            risk_level=risk_level,
            status="pending",
        )
        try:
            await doc.insert()
        except Exception:
            pass

        logger.info(f"ConfirmationEngine: Created pending confirmation '{conf_id}' for command '{command_id}'")
        return doc


confirmation_engine = ConfirmationEngine()
