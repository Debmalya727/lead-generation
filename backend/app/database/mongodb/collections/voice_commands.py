"""
Beanie MongoDB Document collections for Phase 13.6: Voice Command Planner Integration.
Adds 2 collections: voice_command_logs, voice_confirmations.
"""
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from beanie import Document
from pydantic import Field


class VoiceCommandLogDocument(Document):
    """Tracks voice command executions and their target workflow routing."""

    command_id: str = Field(..., description="Unique voice command ID")
    user_id: str = Field(...)
    org_id: Optional[str] = None
    session_id: Optional[str] = None

    raw_transcript: str = Field(..., description="Raw voice transcript text")
    intent: str = Field(..., description="RESEARCH_COMPANY | FIND_LEADS | GENERATE_OUTREACH | SCHEDULE_MEETING | SUMMARIZE_CRM | UNKNOWN")
    extracted_parameters: Dict[str, Any] = Field(default_factory=dict)

    is_ambiguous: bool = Field(False)
    requires_confirmation: bool = Field(False)
    confirmation_status: str = Field("not_required", description="not_required | pending | confirmed | rejected")

    execution_status: str = Field("completed", description="completed | pending | failed | cancelled")
    target_workflow_id: Optional[str] = None
    execution_result: Dict[str, Any] = Field(default_factory=dict)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "voice_command_logs"
        indexes = [
            [("command_id", 1)],
            [("user_id", 1)],
            [("intent", 1)],
            [("created_at", -1)],
        ]


class VoiceConfirmationDocument(Document):
    """Stores pending confirmation prompts for high-stakes voice actions."""

    confirmation_id: str = Field(...)
    command_id: str = Field(...)
    user_id: str = Field(...)

    action_description: str = Field(...)
    risk_level: str = Field("high", description="high | medium | low")
    status: str = Field("pending", description="pending | confirmed | rejected | expired")

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "voice_confirmations"
        indexes = [
            [("confirmation_id", 1)],
            [("command_id", 1)],
            [("status", 1)],
        ]
