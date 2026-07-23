"""
Audio Streaming — ChunkManager for sequence numbering, packet timestamps, and chunk formatting.
"""
import time
import logging
from typing import Dict, Any, Optional

from app.voice.streaming.schemas import AudioChunkPacket, PacketHeader

logger = logging.getLogger("backend.voice.streaming.chunk_manager")


class ChunkManager:
    """Formats incoming/outgoing audio frames into timestamped sequence chunks."""

    def __init__(self):
        self._sequences: Dict[str, int] = {}

    def create_chunk(
        self,
        session_id: str,
        audio_bytes: bytes,
        direction: str = "incoming",
        codec: str = "PCM_16BIT",
        sample_rate: int = 16000,
    ) -> AudioChunkPacket:
        """Wrap raw audio bytes into sequence-numbered AudioChunkPacket."""
        seq = self._sequences.get(session_id, 0) + 1
        self._sequences[session_id] = seq

        hdr = PacketHeader(
            sequence_number=seq,
            timestamp_ms=round(time.time() * 1000, 2),
            session_id=session_id,
            direction=direction,
            codec=codec,
            sample_rate=sample_rate,
        )
        return AudioChunkPacket(header=hdr, payload=audio_bytes, payload_size=len(audio_bytes))


chunk_manager = ChunkManager()
