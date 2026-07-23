"""
Phase 13.10 — Voice Analytics REST API Router.
Endpoints:

  POST /api/v1/voice/analytics/event               — Ingest analytics event
  POST /api/v1/voice/analytics/session/summary     — Compute session summary
  POST /api/v1/voice/analytics/daily/rollup        — Run daily rollup pipeline
  POST /api/v1/voice/analytics/export              — Export analytics data
  GET  /api/v1/voice/analytics/events              — List/filter events
  GET  /api/v1/voice/analytics/sessions            — List session summaries
  GET  /api/v1/voice/analytics/daily               — Historical daily rollups
  GET  /api/v1/voice/analytics/dashboard           — Full dashboard payload
  GET  /api/v1/voice/analytics/provider/performance — Provider comparison
  GET  /api/v1/voice/analytics/alerts              — Active alerts
  GET  /api/v1/voice/analytics/alerts/rules        — Alert rule definitions
  GET  /api/v1/voice/analytics/alerts/history      — Alert history
  POST /api/v1/voice/analytics/alerts/{id}/ack     — Acknowledge alert
  POST /api/v1/voice/analytics/alerts/resolve-all  — Bulk resolve alerts
  GET  /api/v1/voice/analytics/observability       — Observability metrics payload
"""
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.voice.analytics.analytics_engine import voice_analytics_engine
from app.voice.analytics.alert_manager import voice_analytics_alert_manager
from app.database.mongodb.collections.voice_analytics import (
    VoiceAnalyticsEventDocument,
    VoiceAnalyticsSessionDocument,
    VoiceAnalyticsDailyDocument,
    VoiceAnalyticsExportDocument,
    VoiceProviderPerformanceDocument,
)

logger = logging.getLogger("backend.voice.analytics.router")

router = APIRouter(prefix="/voice/analytics", tags=["Voice Analytics (13.10)"])


# ─── Request Models ───────────────────────────────────────────────────────────

class IngestEventRequest(BaseModel):
    session_id: str = Field(...)
    user_id: str = Field("user_default")
    provider: str = Field("whisper")
    tts_provider: str = Field("elevenlabs")
    telephony_provider: Optional[str] = None
    speaking_time_ms: float = Field(0.0)
    silence_time_ms: float = Field(0.0)
    interruption_count: int = Field(0)
    response_latency_ms: float = Field(0.0)
    stt_latency_ms: float = Field(0.0)
    ai_latency_ms: float = Field(0.0)
    tts_latency_ms: float = Field(0.0)
    packet_loss_pct: float = Field(0.0)
    jitter_ms: float = Field(0.0)
    speech_confidence: float = Field(0.95)
    audio_level_db: float = Field(-30.0)
    emotion: str = Field("neutral")
    sentiment: str = Field("neutral")
    sentiment_score: float = Field(0.5)
    stt_cost_usd: float = Field(0.0)
    tts_cost_usd: float = Field(0.0)
    ai_cost_usd: float = Field(0.0)
    input_tokens: int = Field(0)
    output_tokens: int = Field(0)
    turn_index: int = Field(0)
    transcript_length: int = Field(0)


class SessionSummaryRequest(BaseModel):
    session_id: str
    user_id: str = Field("user_default")
    session_type: str = Field("voice_agent")
    duration_seconds: float = Field(0.0)


class DailyRollupRequest(BaseModel):
    date_key: Optional[str] = None
    user_id: str = Field("global")


class ExportRequest(BaseModel):
    export_format: str = Field("csv", description="csv | json")
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    limit: int = Field(1000, ge=1, le=10000)


# ─── Ingest ──────────────────────────────────────────────────────────────────

@router.post("/event")
async def ingest_analytics_event(request: IngestEventRequest):
    """Ingest a single voice analytics event from any voice subsystem."""
    try:
        doc = await voice_analytics_engine.ingest_event(**request.model_dump())
        return {
            "event_id": doc.event_id,
            "session_id": doc.session_id,
            "e2e_latency_ms": doc.e2e_latency_ms,
            "total_cost_usd": doc.total_cost_usd,
            "sentiment": doc.sentiment,
            "emotion": doc.emotion,
            "status": "ingested",
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ─── Aggregation ─────────────────────────────────────────────────────────────

@router.post("/session/summary")
async def compute_session_summary(request: SessionSummaryRequest):
    """Aggregate all events for a completed voice session into a summary."""
    try:
        doc = await voice_analytics_engine.compute_session_summary(
            session_id=request.session_id,
            user_id=request.user_id,
            session_type=request.session_type,
            duration_seconds=request.duration_seconds,
        )
        return doc.model_dump()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/daily/rollup")
async def run_daily_rollup(request: DailyRollupRequest):
    """Run the daily analytics rollup aggregation pipeline."""
    try:
        doc = await voice_analytics_engine.run_daily_rollup(
            date_key=request.date_key,
            user_id=request.user_id,
        )
        return doc.model_dump()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ─── Query / History ─────────────────────────────────────────────────────────

@router.get("/events")
async def list_analytics_events(
    session_id: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    provider: Optional[str] = Query(None),
    sentiment: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
):
    """List voice analytics events with optional filters."""
    try:
        events = await voice_analytics_engine.get_events(
            session_id=session_id,
            user_id=user_id,
            provider=provider,
            sentiment=sentiment,
            limit=limit,
        )
        return [e.model_dump() for e in events]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/sessions")
async def list_session_summaries(
    user_id: Optional[str] = Query(None),
    session_type: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
):
    """List aggregated voice analytics session summaries."""
    try:
        query = VoiceAnalyticsSessionDocument.find_all()
        if user_id:
            query = VoiceAnalyticsSessionDocument.find(VoiceAnalyticsSessionDocument.user_id == user_id)
        docs = await query.sort("-started_at").limit(limit).to_list()
        return [d.model_dump() for d in docs]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/daily")
async def list_daily_rollups(
    user_id: Optional[str] = Query(None),
    limit: int = Query(30, ge=1, le=90),
):
    """List historical daily analytics rollups (up to 90 days)."""
    try:
        query = VoiceAnalyticsDailyDocument.find_all()
        if user_id:
            query = VoiceAnalyticsDailyDocument.find(VoiceAnalyticsDailyDocument.user_id == user_id)
        docs = await query.sort("-date_key").limit(limit).to_list()
        return [d.model_dump() for d in docs]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ─── Dashboard ───────────────────────────────────────────────────────────────

@router.get("/dashboard")
async def get_analytics_dashboard(
    user_id: Optional[str] = Query(None),
):
    """
    Return a complete Voice Analytics dashboard payload:
    - KPI summary (latency, cost, confidence, interruptions)
    - Recent session summaries
    - Daily trend data (last 7 days)
    - Active alerts
    - Provider performance comparison
    - Sentiment and emotion distribution
    """
    try:
        # Fetch most recent sessions
        session_query = VoiceAnalyticsSessionDocument.find_all()
        if user_id:
            session_query = VoiceAnalyticsSessionDocument.find(
                VoiceAnalyticsSessionDocument.user_id == user_id
            )
        sessions = await session_query.sort("-started_at").limit(20).to_list()

        # Fetch most recent events for KPI
        event_query = VoiceAnalyticsEventDocument.find_all()
        if user_id:
            event_query = VoiceAnalyticsEventDocument.find(
                VoiceAnalyticsEventDocument.user_id == user_id
            )
        recent_events = await event_query.sort("-timestamp").limit(200).to_list()

        # Compute KPIs from recent events
        def avg(vals): return round(sum(vals) / len(vals), 2) if vals else 0.0

        kpis = {
            "avg_e2e_latency_ms": avg([e.e2e_latency_ms for e in recent_events]),
            "avg_ai_latency_ms": avg([e.ai_latency_ms for e in recent_events]),
            "avg_stt_latency_ms": avg([e.stt_latency_ms for e in recent_events]),
            "avg_tts_latency_ms": avg([e.tts_latency_ms for e in recent_events]),
            "avg_packet_loss_pct": avg([e.packet_loss_pct for e in recent_events]),
            "avg_speech_confidence": avg([e.speech_confidence for e in recent_events]),
            "avg_silence_pct": avg([e.silence_percentage for e in recent_events]),
            "total_interruptions": sum(e.interruption_count for e in recent_events),
            "total_cost_usd": round(sum(e.total_cost_usd for e in recent_events), 4),
            "total_tokens": sum(e.total_tokens for e in recent_events),
            "total_events": len(recent_events),
            "total_sessions": len(sessions),
        }

        # Sentiment distribution
        sentiment_dist: Dict[str, int] = {}
        emotion_dist: Dict[str, int] = {}
        for e in recent_events:
            sentiment_dist[e.sentiment] = sentiment_dist.get(e.sentiment, 0) + 1
            emotion_dist[e.emotion] = emotion_dist.get(e.emotion, 0) + 1

        # Provider distribution
        provider_dist: Dict[str, int] = {}
        for e in recent_events:
            provider_dist[e.provider] = provider_dist.get(e.provider, 0) + 1

        # Active alerts
        active_alerts = await voice_analytics_alert_manager.get_active_alerts(limit=20)
        alert_severity_counts = voice_analytics_alert_manager.get_severity_counts(active_alerts)

        # Daily rollups (last 7)
        daily_docs = await VoiceAnalyticsDailyDocument.find_all().sort("-date_key").limit(7).to_list()

        # Build latency trend (from recent events, bucketed by turn_index)
        latency_trend = [
            {
                "turn": e.turn_index,
                "e2e_latency_ms": e.e2e_latency_ms,
                "ai_latency_ms": e.ai_latency_ms,
                "stt_latency_ms": e.stt_latency_ms,
                "tts_latency_ms": e.tts_latency_ms,
            }
            for e in sorted(recent_events[:50], key=lambda x: x.timestamp)
        ]

        return {
            "kpis": kpis,
            "sentiment_distribution": sentiment_dist,
            "emotion_distribution": emotion_dist,
            "provider_distribution": provider_dist,
            "latency_trend": latency_trend,
            "sessions": [s.model_dump() for s in sessions[:10]],
            "daily_rollups": [d.model_dump() for d in daily_docs],
            "active_alerts": active_alerts,
            "alert_severity_counts": alert_severity_counts,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ─── Provider Performance ─────────────────────────────────────────────────────

@router.get("/provider/performance")
async def get_provider_performance(
    provider_type: str = Query("stt", description="stt | tts | telephony"),
    window_hours: int = Query(24, ge=1, le=168),
    refresh: bool = Query(False, description="Force recompute provider snapshots"),
):
    """Get provider performance comparison (latency, confidence, error rate, cost, uptime)."""
    try:
        if refresh:
            docs = await voice_analytics_engine.compute_provider_performance(
                provider_type=provider_type,
                window_hours=window_hours,
            )
            return [d.model_dump() for d in docs]
        else:
            docs = await VoiceProviderPerformanceDocument.find(
                VoiceProviderPerformanceDocument.provider_type == provider_type
            ).sort("-measured_at").limit(20).to_list()
            if not docs:
                docs = await voice_analytics_engine.compute_provider_performance(
                    provider_type=provider_type,
                    window_hours=window_hours,
                )
            return [d.model_dump() for d in docs]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ─── Alerts ──────────────────────────────────────────────────────────────────

@router.get("/alerts")
async def get_active_alerts(
    severity: Optional[str] = Query(None, description="info | warning | critical"),
    limit: int = Query(50, ge=1, le=200),
):
    """Get all active (unresolved) voice analytics alerts."""
    try:
        return await voice_analytics_alert_manager.get_active_alerts(severity=severity, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/alerts/rules")
async def get_alert_rules():
    """Return all configured alert rules and their thresholds."""
    return voice_analytics_alert_manager.list_alert_rules()


@router.get("/alerts/history")
async def get_alert_history(limit: int = Query(100, ge=1, le=500)):
    """Return full alert history (active + resolved)."""
    try:
        return await voice_analytics_alert_manager.get_alert_history(limit=limit)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/alerts/{alert_id}/ack")
async def acknowledge_alert(alert_id: str):
    """Acknowledge and resolve a specific alert by ID."""
    try:
        result = await voice_analytics_alert_manager.acknowledge_alert(alert_id)
        if not result:
            raise HTTPException(status_code=404, detail=f"Alert '{alert_id}' not found.")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/alerts/resolve-all")
async def resolve_all_alerts(user_id: Optional[str] = Query(None)):
    """Bulk resolve all active alerts for a user."""
    try:
        count = await voice_analytics_alert_manager.resolve_all(user_id=user_id)
        return {"resolved_count": count, "status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ─── Export ──────────────────────────────────────────────────────────────────

@router.post("/export")
async def export_analytics(request: ExportRequest):
    """Export analytics events to CSV or JSON format."""
    try:
        export_id = f"exp_{uuid.uuid4().hex[:12]}"
        result = await voice_analytics_engine.build_export(
            export_format=request.export_format,
            session_id=request.session_id,
            user_id=request.user_id,
            limit=request.limit,
        )
        # Persist export job record
        export_doc = VoiceAnalyticsExportDocument(
            export_id=export_id,
            user_id=request.user_id or "global",
            export_format=request.export_format,
            filter_params=request.model_dump(),
            status="completed",
            row_count=result["row_count"],
            download_url=f"/api/v1/voice/analytics/export/{export_id}/download",
            completed_at=datetime.now(timezone.utc),
        )
        try:
            await export_doc.insert()
        except Exception:
            pass

        return {
            "export_id": export_id,
            "format": request.export_format,
            "row_count": result["row_count"],
            "download_url": export_doc.download_url,
            "data": result["data"][:50],  # preview first 50
            "generated_at": result["generated_at"],
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ─── Observability ────────────────────────────────────────────────────────────

@router.get("/observability")
async def get_observability_metrics(
    session_id: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=100),
):
    """
    Return structured OpenTelemetry-compatible metrics payload
    for integration with the LeadForgeAI Observability Platform.
    """
    try:
        events = await voice_analytics_engine.get_events(session_id=session_id, limit=limit)
        telemetry = []
        for ev in events:
            metrics = voice_analytics_engine.emit_observability_metrics(ev)
            telemetry.append({
                "event_id": ev.event_id,
                "session_id": ev.session_id,
                "timestamp": ev.timestamp.isoformat(),
                "metrics": metrics,
                "labels": {
                    "provider": ev.provider,
                    "tts_provider": ev.tts_provider,
                    "sentiment": ev.sentiment,
                    "emotion": ev.emotion,
                },
            })
        return {
            "platform": "LeadForgeAI Observability",
            "schema_version": "otel_v1",
            "event_count": len(telemetry),
            "telemetry": telemetry,
            "exported_at": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
