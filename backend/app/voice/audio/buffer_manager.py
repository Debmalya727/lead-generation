"""
Audio Buffer — BufferManager managing circular buffers, silence padding, chunk splitting, and merging.
"""
from typing import Dict, Optional, List
import logging

from app.voice.audio.circular_buffer import CircularBuffer

logger = logging.getLogger("backend.voice.audio.buffer_manager")


class BufferManager:
    """High-level buffer orchestrator for voice sessions."""

    def __init__(self, default_capacity: int = 65536):
        self.default_capacity = default_capacity
        self._buffers: Dict[str, CircularBuffer] = {}

    def get_buffer(self, session_id: str) -> CircularBuffer:
        """Get or create CircularBuffer for session_id."""
        if session_id not in self._buffers:
            self._buffers[session_id] = CircularBuffer(capacity=self.default_capacity)
        return self._buffers[session_id]

    def write_chunk(self, session_id: str, chunk: bytes) -> int:
        """Write audio bytes to session buffer."""
        buf = self.get_buffer(session_id)
        return buf.write(chunk)

    def read_chunk(self, session_id: str, frame_size: int = 320) -> bytes:
        """Read frame_size bytes from session buffer."""
        buf = self.get_buffer(session_id)
        return buf.read(frame_size)

    def pad_silence(self, session_id: str, silence_bytes_len: int = 320) -> int:
        """Pad buffer with silence bytes (0x00)."""
        buf = self.get_buffer(session_id)
        return buf.write(b"\x00" * silence_bytes_len)

    def remove_session_buffer(self, session_id: str) -> None:
        """Clear and remove session buffer."""
        if session_id in self._buffers:
            self._buffers[session_id].clear()
            del self._buffers[session_id]


buffer_manager = BufferManager()
