"""
Voice Session Manager — Pydantic schemas for Phase 13.1.
"""
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field


class VoiceSessionCreate(BaseModel):
    user_id: str
    org_id: Optional[str] = None
    device_id: Optional[str] = None
    microphone_name: str = Field("Default Microphone")
    codec: str = Field("PCM_16BIT", description="PCM_16BIT | OPUS | G711_ULAW")
    sample_rate: int = Field(16000, description="16000 | 48000 | 8000")
    channels: int = Field(1)
    bitrate: int = Field(128000)


class VoiceSessionUpdate(BaseModel):
    status: Optional[str] = None
    connection_quality: Optional[str] = None
    latency_ms: Optional[float] = None
