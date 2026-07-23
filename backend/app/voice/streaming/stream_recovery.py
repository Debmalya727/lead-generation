"""
Audio Streaming — StreamRecovery handling packet loss concealment and frame recovery.
"""
from typing import Dict, Optional
import logging

from app.voice.streaming.schemas import AudioChunkPacket, PacketHeader

logger = logging.getLogger("backend.voice.streaming.stream_recovery")


class StreamRecovery:
    """Detects packet gaps and synthesizes silence/concealment frames."""

    def conceal_missing_frame(
        self,
        session_id: str,
        missing_seq: int,
        frame_bytes_length: int = 320,
    ) -> AudioChunkPacket:
        """Synthesize silence frame for missing audio packet."""
        logger.warning(f"StreamRecovery: Concealing missing packet seq={missing_seq} for session '{session_id}'")
        silence_bytes = b"\x00" * frame_bytes_length
        hdr = PacketHeader(
            sequence_number=missing_seq,
            session_id=session_id,
            direction="concealment",
        )
        return AudioChunkPacket(header=hdr, payload=silence_bytes, payload_size=frame_bytes_length)


stream_recovery = StreamRecovery()
