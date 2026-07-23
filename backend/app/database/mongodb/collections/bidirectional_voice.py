"""
Beanie MongoDB Document collections for Phase 13.4: Real-Time Bidirectional Voice AI Streaming Engine.
Adds 3 collections: bidirectional_sessions, bidirectional_turns, bidirectional_metrics.
"""
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from beanie import Document
from pydantic import Field


class BidirectionalSessionDocument(Document):
    """Tracks active full-duplex speech-to-speech voice sessions."""

    session_id: str = Field(..., description="Unique duplex session ID")
    user_id: str = Field(...)
    org_id: Optional[str] = None

    stt_provider: str = Field("whisper")
    stt_model: str = Field("whisper-1")
    tts_provider: str = Field("elevenlabs")
    tts_voice_id: str = Field("21m00Tcm4TlvDq8ikWAM")
    emotion: str = Field("professional")

    status: str = Field("active", description="active | paused | closed | error")
    total_turns: int = Field(0)
    interruption_count: int = Field(0)
    avg_e2e_latency_ms: float = Field(0.0)

    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    ended_at: Optional[datetime] = None

    class Settings:
        name = "bidirectional_sessions"
        indexes = [
            [("session_id", 1)],
            [("user_id", 1)],
            [("status", 1)],
        ]


class BidirectionalTurnDocument(Document):
    """Logs individual conversational turns in a full-duplex session."""

    turn_id: str = Field(..., description="Unique turn ID")
    session_id: str = Field(...)
    user_id: str = Field(...)

    user_transcript: str = Field("", description="Final STT user transcript")
    assistant_response: str = Field("", description="Assembled LLM response text")

    stt_latency_ms: float = Field(0.0)
    llm_latency_ms: float = Field(0.0)
    tts_ttfb_ms: float = Field(0.0)
    e2e_speech_to_speech_latency_ms: float = Field(0.0)

    was_interrupted: bool = Field(False)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "bidirectional_turns"
        indexes = [
            [("turn_id", 1)],
            [("session_id", 1)],
            [("timestamp", -1)],
        ]


class BidirectionalMetricsDocument(Document):
    """Telemetry metrics for bidirectional streaming latency and interruptions."""

    metric_id: str = Field(...)
    session_id: str = Field(...)

    e2e_latency_ms: float = Field(0.0)
    stt_latency_ms: float = Field(0.0)
    llm_ttft_ms: float = Field(0.0, description="Time to First Token for LLM")
    tts_ttfb_ms: float = Field(0.0, description="Time to First Byte for TTS")
    interrupted: bool = Field(False)

    recorded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "bidirectional_metrics"
        indexes = [
            [("session_id", 1)],
            [("recorded_at", -1)],
        ]
