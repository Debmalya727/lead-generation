"""
Phase 13.10 — Voice Analytics MongoDB Collections.
Collections:
  - voice_analytics_events      (per-turn analytics events)
  - voice_analytics_sessions    (aggregated per-session metrics)
  - voice_analytics_daily       (daily rollup aggregations)
  - voice_analytics_alerts      (threshold alert instances)
  - voice_analytics_exports     (export job records)
  - voice_provider_performance  (provider benchmark comparisons)
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from beanie import Document
from pydantic import Field


class VoiceAnalyticsEventDocument(Document):
    """
    Single analytics event captured for a voice turn or interaction segment.
    Captures: speaking_time, silence, interruptions, STT latency, AI latency,
              TTS latency, packet_loss, confidence, emotion, sentiment, cost, tokens.
    """
    event_id: str = Field(...)
    session_id: str = Field(...)
    user_id: str = Field("user_default")
    provider: str = Field("whisper")        # STT provider
    tts_provider: str = Field("elevenlabs")
    telephony_provider: Optional[str] = None

    # ── Speaking / Silence ─────────────────────────────────────
    speaking_time_ms: float = Field(0.0)
    silence_time_ms: float = Field(0.0)
    silence_percentage: float = Field(0.0)

    # ── Interruptions ──────────────────────────────────────────
    interruption_count: int = Field(0)
    interruption_flag: bool = Field(False)

    # ── Latency ────────────────────────────────────────────────
    response_latency_ms: float = Field(0.0)   # Time from user stop → AI response start
    stt_latency_ms: float = Field(0.0)
    ai_latency_ms: float = Field(0.0)
    tts_latency_ms: float = Field(0.0)
    e2e_latency_ms: float = Field(0.0)        # Full pipeline

    # ── Network ────────────────────────────────────────────────
    packet_loss_pct: float = Field(0.0)
    jitter_ms: float = Field(0.0)

    # ── Quality ────────────────────────────────────────────────
    speech_confidence: float = Field(0.0)     # 0.0 - 1.0
    audio_level_db: float = Field(-60.0)

    # ── Emotion / Sentiment ────────────────────────────────────
    emotion: str = Field("neutral")           # happy | sad | frustrated | neutral | excited
    sentiment: str = Field("neutral")         # positive | neutral | negative | objection_price
    sentiment_score: float = Field(0.5)       # 0.0 - 1.0

    # ── Cost / Tokens ──────────────────────────────────────────
    stt_cost_usd: float = Field(0.0)
    tts_cost_usd: float = Field(0.0)
    ai_cost_usd: float = Field(0.0)
    total_cost_usd: float = Field(0.0)
    input_tokens: int = Field(0)
    output_tokens: int = Field(0)
    total_tokens: int = Field(0)

    # ── Metadata ───────────────────────────────────────────────
    turn_index: int = Field(0)
    transcript_length: int = Field(0)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "voice_analytics_events"
        indexes = [
            [("event_id", 1)],
            [("session_id", 1)],
            [("user_id", 1)],
            [("provider", 1)],
            [("timestamp", -1)],
            [("sentiment", 1)],
            [("emotion", 1)],
        ]


class VoiceAnalyticsSessionDocument(Document):
    """
    Aggregated analytics for a complete voice session.
    Computed by rolling up all VoiceAnalyticsEventDocuments for a session.
    """
    session_id: str = Field(...)
    user_id: str = Field("user_default")
    session_type: str = Field("voice_agent", description="voice_agent | meeting | telephony | bidirectional")

    # ── Session Duration ───────────────────────────────────────
    duration_seconds: float = Field(0.0)
    total_turns: int = Field(0)

    # ── Speaking / Silence ─────────────────────────────────────
    total_speaking_ms: float = Field(0.0)
    total_silence_ms: float = Field(0.0)
    avg_silence_pct: float = Field(0.0)

    # ── Interruptions ──────────────────────────────────────────
    total_interruptions: int = Field(0)

    # ── Latency Averages ───────────────────────────────────────
    avg_response_latency_ms: float = Field(0.0)
    avg_stt_latency_ms: float = Field(0.0)
    avg_ai_latency_ms: float = Field(0.0)
    avg_tts_latency_ms: float = Field(0.0)
    avg_e2e_latency_ms: float = Field(0.0)
    p95_e2e_latency_ms: float = Field(0.0)

    # ── Network ────────────────────────────────────────────────
    avg_packet_loss_pct: float = Field(0.0)
    avg_jitter_ms: float = Field(0.0)

    # ── Quality ────────────────────────────────────────────────
    avg_speech_confidence: float = Field(0.0)

    # ── Emotion / Sentiment Distribution ──────────────────────
    sentiment_distribution: Dict[str, int] = Field(default_factory=dict)
    emotion_distribution: Dict[str, int] = Field(default_factory=dict)
    dominant_sentiment: str = Field("neutral")
    dominant_emotion: str = Field("neutral")

    # ── Cost Summary ───────────────────────────────────────────
    total_stt_cost_usd: float = Field(0.0)
    total_tts_cost_usd: float = Field(0.0)
    total_ai_cost_usd: float = Field(0.0)
    total_session_cost_usd: float = Field(0.0)
    total_tokens: int = Field(0)

    # ── Provider ───────────────────────────────────────────────
    primary_stt_provider: str = Field("whisper")
    primary_tts_provider: str = Field("elevenlabs")

    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    ended_at: Optional[datetime] = None
    computed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "voice_analytics_sessions"
        indexes = [
            [("session_id", 1)],
            [("user_id", 1)],
            [("session_type", 1)],
            [("started_at", -1)],
            [("total_session_cost_usd", -1)],
        ]


class VoiceAnalyticsDailyDocument(Document):
    """Daily rollup of voice analytics across all sessions for a user/org."""
    date_key: str = Field(..., description="YYYY-MM-DD")
    user_id: str = Field("global")
    org_id: Optional[str] = None

    total_sessions: int = Field(0)
    total_duration_seconds: float = Field(0.0)
    total_turns: int = Field(0)
    total_interruptions: int = Field(0)

    avg_silence_pct: float = Field(0.0)
    avg_response_latency_ms: float = Field(0.0)
    avg_ai_latency_ms: float = Field(0.0)
    avg_packet_loss_pct: float = Field(0.0)
    avg_speech_confidence: float = Field(0.0)

    sentiment_distribution: Dict[str, int] = Field(default_factory=dict)
    emotion_distribution: Dict[str, int] = Field(default_factory=dict)

    total_cost_usd: float = Field(0.0)
    total_tokens: int = Field(0)

    provider_breakdown: Dict[str, Any] = Field(default_factory=dict)

    computed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "voice_analytics_daily"
        indexes = [
            [("date_key", 1)],
            [("user_id", 1)],
            [("date_key", -1), ("user_id", 1)],
        ]


class VoiceAnalyticsAlertDocument(Document):
    """Triggered alert instance when a metric crosses a threshold."""
    alert_id: str = Field(...)
    alert_rule_id: str = Field(...)
    session_id: Optional[str] = None
    user_id: str = Field("user_default")

    metric_name: str = Field(...)         # e.g. avg_e2e_latency_ms
    metric_value: float = Field(...)
    threshold_value: float = Field(...)
    operator: str = Field("gt")           # gt | lt | gte | lte
    severity: str = Field("warning")      # info | warning | critical

    message: str = Field(...)
    acknowledged: bool = Field(False)
    resolved: bool = Field(False)

    triggered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    resolved_at: Optional[datetime] = None

    class Settings:
        name = "voice_analytics_alerts"
        indexes = [
            [("alert_id", 1)],
            [("session_id", 1)],
            [("user_id", 1)],
            [("severity", 1)],
            [("resolved", 1)],
            [("triggered_at", -1)],
        ]


class VoiceAnalyticsExportDocument(Document):
    """Tracks analytics export job status and download URL."""
    export_id: str = Field(...)
    user_id: str = Field("user_default")
    export_format: str = Field("csv")         # csv | json | xlsx
    filter_params: Dict[str, Any] = Field(default_factory=dict)
    status: str = Field("pending")            # pending | running | completed | failed
    row_count: int = Field(0)
    download_url: Optional[str] = None
    error_message: Optional[str] = None
    requested_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None

    class Settings:
        name = "voice_analytics_exports"
        indexes = [
            [("export_id", 1)],
            [("user_id", 1)],
            [("status", 1)],
        ]


class VoiceProviderPerformanceDocument(Document):
    """Comparative provider performance snapshot for analytics dashboard."""
    perf_id: str = Field(...)
    provider_type: str = Field("stt")      # stt | tts | telephony
    provider_id: str = Field(...)

    avg_latency_ms: float = Field(0.0)
    p95_latency_ms: float = Field(0.0)
    avg_confidence: float = Field(0.0)
    error_rate_pct: float = Field(0.0)
    avg_cost_per_turn: float = Field(0.0)
    total_requests: int = Field(0)
    uptime_pct: float = Field(99.9)

    measured_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    window_hours: int = Field(24)

    class Settings:
        name = "voice_provider_performance"
        indexes = [
            [("perf_id", 1)],
            [("provider_id", 1)],
            [("provider_type", 1)],
            [("measured_at", -1)],
        ]
