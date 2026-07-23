"""
Phase 13.9 — Beanie MongoDB Document collections.
Adds 4 collections:
  - telephony_calls
  - telephony_recordings
  - telephony_queue_events
  - telephony_call_summaries
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from beanie import Document
from pydantic import Field


class TelephonyCallDocument(Document):
    """Stores metadata for every inbound and outbound telephony call."""

    call_id: str = Field(..., description="Provider call SID / unique call ID")
    provider: str = Field(..., description="twilio | sip | zoom_phone | teams_phone")
    direction: str = Field(..., description="inbound | outbound")
    status: str = Field("ringing", description="ringing | in_progress | transferred | completed | failed | missed")

    from_number: str = Field(...)
    to_number: str = Field(...)

    user_id: str = Field("user_default")
    lead_id: Optional[str] = None
    assigned_agent: Optional[str] = None
    transferred_to: Optional[str] = None

    recording_enabled: bool = Field(True)
    recording_ids: List[str] = Field(default_factory=list)

    ai_context: Dict[str, Any] = Field(default_factory=dict)
    sentiment_trend: Optional[str] = None
    duration_seconds: Optional[int] = None

    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    ended_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "telephony_calls"
        indexes = [
            [("call_id", 1)],
            [("provider", 1)],
            [("direction", 1)],
            [("status", 1)],
            [("user_id", 1)],
            [("lead_id", 1)],
            [("created_at", -1)],
        ]


class TelephonyRecordingDocument(Document):
    """Stores call recording metadata and transcript linkage."""

    recording_id: str = Field(..., description="Provider recording SID")
    call_id: str = Field(...)
    provider: str = Field(...)
    status: str = Field("recording", description="recording | processing | completed | failed")

    duration_seconds: Optional[int] = None
    recording_url: Optional[str] = None
    transcript_id: Optional[str] = None  # Links to Speech Gateway transcript

    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    ended_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "telephony_recordings"
        indexes = [
            [("recording_id", 1)],
            [("call_id", 1)],
            [("status", 1)],
        ]


class TelephonyQueueEventDocument(Document):
    """Audit log for call queue events (enqueue, dequeue, abandon, transfer)."""

    event_id: str = Field(...)
    call_id: str = Field(...)
    queue_key: str = Field(...)
    event_type: str = Field(..., description="enqueued | dequeued | abandoned | transferred | answered")
    priority: int = Field(5)
    wait_seconds: float = Field(0.0)
    assigned_agent: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "telephony_queue_events"
        indexes = [
            [("event_id", 1)],
            [("call_id", 1)],
            [("queue_key", 1)],
            [("timestamp", -1)],
        ]


class TelephonyCallSummaryDocument(Document):
    """Stores AI-generated post-call summaries and CRM update status."""

    summary_id: str = Field(...)
    call_id: str = Field(...)
    lead_id: Optional[str] = None

    executive_summary: str = Field(...)
    action_items: List[str] = Field(default_factory=list)
    sentiment_trend: str = Field("neutral")
    duration_seconds: int = Field(0)

    crm_update_status: str = Field("queued", description="queued | synced | failed")
    followup_email_queued: bool = Field(False)

    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "telephony_call_summaries"
        indexes = [
            [("summary_id", 1)],
            [("call_id", 1)],
            [("lead_id", 1)],
            [("crm_update_status", 1)],
        ]
