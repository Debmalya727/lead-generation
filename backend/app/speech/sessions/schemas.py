"""
Speech Sessions — Pydantic schemas for STT session management.
"""
from typing import Optional
from pydantic import BaseModel, Field


class SpeechSessionCreate(BaseModel):
    user_id: str
    provider: str = Field("whisper")
    model: str = Field("whisper-1")
    language: Optional[str] = Field("en")


class SpeechSessionUpdate(BaseModel):
    status: Optional[str] = None
    accumulated_transcript: Optional[str] = None
    additional_seconds: float = Field(0.0)
