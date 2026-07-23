"""
Beanie MongoDB Document collections for Phase 13.3: Text-to-Speech (TTS) Gateway.
Adds 8 collections: tts_requests, tts_audio_outputs, tts_voice_profiles,
tts_providers, tts_models, tts_costs, tts_caches, tts_benchmarks.
"""
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from beanie import Document
from pydantic import Field


class TTSRequestDocument(Document):
    """Logs text-to-speech synthesis requests."""

    request_id: str = Field(..., description="Unique TTS request ID")
    user_id: str = Field(...)
    org_id: Optional[str] = None
    session_id: Optional[str] = None

    provider: str = Field("elevenlabs", description="elevenlabs | openai | azure | google | polly | piper")
    model: str = Field("eleven_multilingual_v2")
    voice_id: str = Field("21m00Tcm4TlvDq8ikWAM")
    emotion: Optional[str] = Field("professional")

    text_prompt: str = Field(...)
    character_count: int = Field(0)
    has_ssml: bool = Field(False)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "tts_requests"
        indexes = [
            [("request_id", 1)],
            [("user_id", 1)],
            [("provider", 1)],
            [("created_at", -1)],
        ]


class TTSAudioOutputDocument(Document):
    """Stores synthesized audio metadata."""

    output_id: str = Field(..., description="Unique audio output ID")
    request_id: str = Field(...)
    session_id: Optional[str] = None

    audio_format: str = Field("pcm_16000", description="pcm_16000 | mp3 | opus")
    audio_size_bytes: int = Field(0)
    audio_duration_seconds: float = Field(0.0)

    ttfb_ms: float = Field(0.0, description="Time to First Byte in ms")
    total_latency_ms: float = Field(0.0)
    provider_used: str = Field("elevenlabs")
    model_used: str = Field("eleven_multilingual_v2")
    estimated_cost: float = Field(0.0)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "tts_audio_outputs"
        indexes = [
            [("output_id", 1)],
            [("request_id", 1)],
        ]


class TTSVoiceProfileDocument(Document):
    """Stores voice profiles, synthetic voices, and cloned voice metadata."""

    profile_id: str = Field(..., description="Unique voice profile ID")
    voice_name: str = Field(...)
    provider_id: str = Field("elevenlabs")
    gender: str = Field("female", description="female | male | neutral")
    language: str = Field("en-US")

    is_cloned: bool = Field(False)
    supported_emotions: List[str] = Field(default_factory=lambda: ["cheerful", "empathetic", "professional", "urgent"])
    sample_rate: int = Field(24000)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "tts_voice_profiles"
        indexes = [
            [("profile_id", 1)],
            [("provider_id", 1)],
        ]


class TTSProviderDocument(Document):
    """Registered TTS provider configuration."""

    provider_id: str = Field(...)
    name: str = Field(...)
    is_enabled: bool = Field(True)
    health_status: str = Field("healthy")

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "tts_providers"
        indexes = [
            [("provider_id", 1)],
        ]


class TTSModelDocument(Document):
    """TTS models and character pricing specifications."""

    model_id: str = Field(...)
    provider_id: str = Field(...)
    display_name: str = Field(...)

    cost_per_1k_chars: float = Field(0.015, description="Price per 1,000 characters in USD")
    supports_ssml: bool = Field(True)
    supports_streaming: bool = Field(True)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "tts_models"
        indexes = [
            [("model_id", 1)],
            [("provider_id", 1)],
        ]


class TTSCostDocument(Document):
    """Tracks TTS character synthesis expenditure."""

    cost_id: str = Field(...)
    user_id: str = Field(...)
    org_id: Optional[str] = None
    provider: str = Field(...)
    model: str = Field(...)

    character_count: int = Field(0)
    amount_usd: float = Field(0.0)

    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "tts_costs"
        indexes = [
            [("cost_id", 1)],
            [("user_id", 1)],
            [("timestamp", -1)],
        ]


class TTSCacheDocument(Document):
    """Synthesized audio byte cache for deduplication."""

    cache_key: str = Field(..., description="SHA-256 hash of text+voice+emotion")
    text_prompt: str = Field(...)
    voice_id: str = Field(...)

    audio_bytes_base64: str = Field(...)
    hit_count: int = Field(1)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "tts_caches"
        indexes = [
            [("cache_key", 1)],
        ]


class TTSBenchmarkDocument(Document):
    """TTS provider benchmarks (TTFB ms, MOS naturalness score)."""

    benchmark_id: str = Field(...)
    provider: str = Field(...)
    model: str = Field(...)

    ttfb_latency_ms: float = Field(120.0, description="Time to First Byte ms")
    mos_score: float = Field(4.5, description="Mean Opinion Score 1.0 - 5.0")
    cost_per_1k_chars: float = Field(0.015)

    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "tts_benchmarks"
        indexes = [
            [("benchmark_id", 1)],
            [("provider", 1)],
        ]
