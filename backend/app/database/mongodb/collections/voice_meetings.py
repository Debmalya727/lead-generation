"""
Beanie MongoDB Document collections for Phase 13.7: Enterprise Voice Meeting Assistant.
Adds 4 collections: voice_meetings, voice_meeting_segments, voice_meeting_action_items, voice_meeting_summaries.
"""
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from beanie import Document
from pydantic import Field


class VoiceMeetingDocument(Document):
    """Tracks voice meeting session metadata."""

    meeting_id: str = Field(..., description="Unique voice meeting ID")
    title: str = Field("LeadForgeAI Enterprise Sync")
    platform: str = Field("google_meet", description="google_meet | teams | zoom | custom")
    user_id: str = Field(...)
    org_id: Optional[str] = None
    lead_id: Optional[str] = None

    status: str = Field("active", description="active | completed | processing | error")
    duration_seconds: float = Field(0.0)
    attendees: List[str] = Field(default_factory=lambda: ["host@leadforge.ai", "prospect@acmecorp.com"])

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    ended_at: Optional[datetime] = None

    class Settings:
        name = "voice_meetings"
        indexes = [
            [("meeting_id", 1)],
            [("user_id", 1)],
            [("platform", 1)],
            [("status", 1)],
        ]


class VoiceMeetingSegmentDocument(Document):
    """Stores speaker-diarized speech transcript segments."""

    segment_id: str = Field(..., description="Unique segment ID")
    meeting_id: str = Field(...)

    speaker_id: str = Field("speaker_1", description="speaker_1 | speaker_2 | speaker_3")
    speaker_name: str = Field("Speaker 1")
    start_time_sec: float = Field(0.0)
    end_time_sec: float = Field(0.0)

    transcript_text: str = Field(...)
    confidence: float = Field(0.95)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "voice_meeting_segments"
        indexes = [
            [("segment_id", 1)],
            [("meeting_id", 1)],
            [("speaker_id", 1)],
            [("transcript_text", "text")],  # MongoDB Full-Text Search Index
        ]


class VoiceMeetingActionItemDocument(Document):
    """Stores extracted meeting action items, deadlines, and assignees."""

    item_id: str = Field(..., description="Unique action item ID")
    meeting_id: str = Field(...)

    action_text: str = Field(...)
    assignee: str = Field("Unassigned")
    due_date: Optional[str] = Field(None)
    status: str = Field("pending", description="pending | completed | cancelled")

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "voice_meeting_action_items"
        indexes = [
            [("item_id", 1)],
            [("meeting_id", 1)],
        ]


class VoiceMeetingSummaryDocument(Document):
    """Stores AI executive meeting summaries, CRM record updates, and follow-up email drafts."""

    summary_id: str = Field(...)
    meeting_id: str = Field(...)

    executive_summary: str = Field(...)
    key_highlights: List[str] = Field(default_factory=list)
    crm_update_status: str = Field("attached_to_lead", description="attached_to_lead | skipped")
    followup_email_draft: str = Field(...)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "voice_meeting_summaries"
        indexes = [
            [("summary_id", 1)],
            [("meeting_id", 1)],
        ]
