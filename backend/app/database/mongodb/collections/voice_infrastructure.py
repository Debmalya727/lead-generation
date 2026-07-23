"""
Beanie MongoDB Document collections for Phase 13.1: Enterprise Voice Infrastructure.
Adds 6 collections: voice_sessions, voice_streams, voice_buffers,
voice_metrics, voice_events, voice_devices.
"""
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from beanie import Document
from pydantic import Field


class VoiceSessionDocument(Document):
    """Tracks active and historical enterprise voice sessions."""

    session_id: str = Field(..., description="Unique voice session identifier")
    user_id: str = Field(...)
    org_id: Optional[str] = None
    device_id: Optional[str] = None

    microphone_name: str = Field("Default Microphone")
    codec: str = Field("PCM_16BIT", description="PCM_16BIT | OPUS | G711_ULAW")
    sample_rate: int = Field(16000, description="16000 | 48000 | 8000")
    channels: int = Field(1, description="1=Mono, 2=Stereo")
    bitrate: int = Field(128000, description="Bitrate in bps")

    status: str = Field("initializing", description="initializing | active | paused | closed | error")
    connection_quality: str = Field("Good", description="Good | Fair | Poor")
    latency_ms: float = Field(0.0)

    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    ended_at: Optional[datetime] = None

    class Settings:
        name = "voice_sessions"
        indexes = [
            [("session_id", 1)],
            [("user_id", 1)],
            [("status", 1)],
            [("started_at", -1)],
        ]


class VoiceStreamDocument(Document):
    """Tracks active incoming and outgoing audio streams."""

    stream_id: str = Field(..., description="Unique stream identifier")
    session_id: str = Field(...)
    direction: str = Field("incoming", description="incoming | outgoing")

    codec: str = Field("PCM_16BIT")
    sample_rate: int = Field(16000)

    total_chunks: int = Field(0)
    total_bytes: int = Field(0)
    packet_loss_rate: float = Field(0.0)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "voice_streams"
        indexes = [
            [("stream_id", 1)],
            [("session_id", 1)],
        ]


class VoiceBufferDocument(Document):
    """Tracks buffer capacities and utilization."""

    buffer_id: str = Field(..., description="Unique buffer identifier")
    session_id: str = Field(...)
    buffer_type: str = Field("circular", description="circular | silence | priority_queue")

    capacity_bytes: int = Field(65536)
    current_usage_bytes: int = Field(0)
    overflow_count: int = Field(0)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "voice_buffers"
        indexes = [
            [("buffer_id", 1)],
            [("session_id", 1)],
        ]


class VoiceMetricsDocument(Document):
    """Real-time latency, jitter, and packet loss telemetry."""

    metric_id: str = Field(..., description="Unique metric record ID")
    session_id: str = Field(...)

    jitter_ms: float = Field(0.0)
    packet_loss_percentage: float = Field(0.0)
    audio_level_db: float = Field(-60.0)
    latency_ms: float = Field(0.0)

    recorded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "voice_metrics"
        indexes = [
            [("session_id", 1)],
            [("recorded_at", -1)],
        ]


class VoiceEventDocument(Document):
    """Persists voice event stream logs."""

    event_id: str = Field(..., description="Unique voice event ID")
    session_id: str = Field(...)
    event_type: str = Field(..., description="VoiceConnected | SpeechStarted | SpeechStopped | Interruption | etc.")

    payload: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "voice_events"
        indexes = [
            [("event_id", 1)],
            [("session_id", 1)],
            [("event_type", 1)],
            [("timestamp", -1)],
        ]


class VoiceDeviceDocument(Document):
    """Stores device profiles and hardware specifications."""

    device_id: str = Field(..., description="Unique device profile ID")
    user_id: str = Field(...)
    device_name: str = Field(...)

    max_sample_rate: int = Field(48000)
    supported_codecs: List[str] = Field(default_factory=lambda: ["PCM_16BIT", "OPUS"])
    is_default: bool = Field(True)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "voice_devices"
        indexes = [
            [("device_id", 1)],
            [("user_id", 1)],
        ]
