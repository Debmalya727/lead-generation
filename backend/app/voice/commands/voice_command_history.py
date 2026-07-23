"""
VoiceCommandHistory — Tracks execution history, parameters, target workflows, and results for voice commands.
"""
import uuid
import logging
from typing import Dict, Any, List, Optional

from app.database.mongodb.collections.voice_commands import VoiceCommandLogDocument
from app.voice.commands.voice_command_parser import ParsedVoiceCommand

logger = logging.getLogger("backend.voice.commands.history")


class VoiceCommandHistory:
    """Logs executed voice commands to MongoDB and retrieves command history."""

    async def log_command(
        self,
        user_id: str,
        cmd: ParsedVoiceCommand,
        session_id: Optional[str] = None,
        is_ambiguous: bool = False,
        requires_confirmation: bool = False,
        execution_status: str = "completed",
        target_workflow_id: Optional[str] = None,
        result_payload: Optional[Dict[str, Any]] = None,
    ) -> VoiceCommandLogDocument:
        """Create and insert a voice command log entry."""
        cmd_id = f"v_cmd_{uuid.uuid4().hex[:12]}"

        doc = VoiceCommandLogDocument(
            command_id=cmd_id,
            user_id=user_id,
            session_id=session_id,
            raw_transcript=cmd.raw_transcript,
            intent=cmd.intent,
            extracted_parameters=cmd.extracted_parameters,
            is_ambiguous=is_ambiguous,
            requires_confirmation=requires_confirmation,
            execution_status=execution_status,
            target_workflow_id=target_workflow_id,
            execution_result=result_payload or {},
        )
        try:
            await doc.insert()
        except Exception:
            pass

        logger.info(f"VoiceCommandHistory: Logged command '{cmd_id}' (intent={cmd.intent}, status={execution_status})")
        return doc

    async def get_user_command_history(self, user_id: str, limit: int = 30) -> List[VoiceCommandLogDocument]:
        """Fetch command history for a given user."""
        return await VoiceCommandLogDocument.find(VoiceCommandLogDocument.user_id == user_id).sort("-created_at").limit(limit).to_list()


voice_command_history = VoiceCommandHistory()
