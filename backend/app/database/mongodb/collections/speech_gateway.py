"""
Beanie MongoDB Document collections for Phase 13.2: Speech Recognition Gateway (ASR / STT).
Adds 7 collections: speech_requests, speech_responses, speech_sessions,
speech_providers, speech_models, speech_costs, speech_benchmarks.
"""
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from beanie import Document
from pydantic import Field


class SpeechRequestDocument(Document):
    """Logs individual speech transcription requests."""

    request_id: str = Field(..., description="Unique speech request ID")
    user_id: str = Field(...)
    org_id: Optional[str] = None
    session_id: Optional[str] = None

    provider: str = Field("whisper", description="whisper | faster_whisper | deepgram | google | azure | assemblyai")
    model: str = Field("whisper-1")
    audio_duration_seconds: float = Field(0.0)
    language: Optional[str] = Field("en")

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "speech_requests"
        indexes = [
            [("request_id", 1)],
            [("user_id", 1)],
            [("provider", 1)],
            [("created_at", -1)],
        ]


class SpeechResponseDocument(Document):
    """Stores transcription response outputs and metadata."""

    response_id: str = Field(..., description="Unique response ID")
    request_id: str = Field(...)
    session_id: Optional[str] = None

    transcript_text: str = Field("")
    is_partial: bool = Field(False)
    confidence_score: float = Field(0.0, description="Confidence score 0.0 - 1.0")
    detected_language: str = Field("en")
    language_confidence: float = Field(0.0)

    latency_ms: float = Field(0.0)
    provider_used: str = Field("whisper")
    model_used: str = Field("whisper-1")
    estimated_cost: float = Field(0.0)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "speech_responses"
        indexes = [
            [("response_id", 1)],
            [("request_id", 1)],
            [("session_id", 1)],
        ]


class SpeechSessionDocument(Document):
    """Tracks active and closed STT sessions."""

    session_id: str = Field(..., description="Unique STT session ID")
    user_id: str = Field(...)
    provider: str = Field("whisper")
    model: str = Field("whisper-1")

    total_audio_seconds: float = Field(0.0)
    total_transcript_chunks: int = Field(0)
    accumulated_transcript: str = Field("")

    status: str = Field("active", description="active | completed | error")
    total_cost: float = Field(0.0)

    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    ended_at: Optional[datetime] = None

    class Settings:
        name = "speech_sessions"
        indexes = [
            [("session_id", 1)],
            [("user_id", 1)],
            [("status", 1)],
        ]


class SpeechProviderDocument(Document):
    """Registered STT provider configuration."""

    provider_id: str = Field(..., description="whisper | deepgram | etc.")
    name: str = Field(...)
    is_enabled: bool = Field(True)
    health_status: str = Field("healthy", description="healthy | degraded | down")
    supported_models: List[str] = Field(default_factory=list)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "speech_providers"
        indexes = [
            [("provider_id", 1)],
        ]


class SpeechModelDocument(Document):
    """Speech recognition models and pricing specifications."""

    model_id: str = Field(...)
    provider_id: str = Field(...)
    display_name: str = Field(...)

    cost_per_minute: float = Field(0.006, description="Price per audio minute in USD")
    supports_streaming: bool = Field(True)
    supported_languages: List[str] = Field(default_factory=lambda: ["en", "es", "fr", "de", "zh", "ja"])

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "speech_models"
        indexes = [
            [("model_id", 1)],
            [("provider_id", 1)],
        ]


class SpeechCostDocument(Document):
    """Tracks audio transcription expenditure."""

    cost_id: str = Field(...)
    user_id: str = Field(...)
    org_id: Optional[str] = None
    provider: str = Field(...)
    model: str = Field(...)

    audio_seconds: float = Field(0.0)
    amount_usd: float = Field(0.0)

    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "speech_costs"
        indexes = [
            [("cost_id", 1)],
            [("user_id", 1)],
            [("timestamp", -1)],
        ]


class SpeechBenchmarkDocument(Document):
    """Speech recognition benchmarks (WER, Latency, Cost)."""

    benchmark_id: str = Field(...)
    provider: str = Field(...)
    model: str = Field(...)

    word_error_rate: float = Field(0.05, description="Simulated/Measured WER (0.0 - 1.0)")
    avg_latency_ms: float = Field(250.0)
    cost_per_min: float = Field(0.006)

    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "speech_benchmarks"
        indexes = [
            [("benchmark_id", 1)],
            [("provider", 1)],
        ]
