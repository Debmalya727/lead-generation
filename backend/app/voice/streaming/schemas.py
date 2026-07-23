"""
Audio Streaming — Pydantic schemas for chunk headers and packets.
"""
from typing import Dict, Any, Optional
import time
from pydantic import BaseModel, Field


class PacketHeader(BaseModel):
    sequence_number: int
    timestamp_ms: float = Field(default_factory=lambda: round(time.time() * 1000, 2))
    session_id: str
    direction: str = "incoming"
    codec: str = "PCM_16BIT"
    sample_rate: int = 16000


class AudioChunkPacket(BaseModel):
    header: PacketHeader
    payload: bytes
    payload_size: int = 0
