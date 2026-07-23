"""
AudioBufferStreamer — Chunks synthesized audio bytes and streams them into Voice Infrastructure CircularBuffer.
"""
from typing import Optional
import logging

from app.voice.audio.buffer_manager import buffer_manager

logger = logging.getLogger("backend.tts.gateway.streamer")


class AudioBufferStreamer:
    """Streams TTS audio byte output directly into session CircularBuffer."""

    def push_tts_to_voice_buffer(self, session_id: str, pcm_bytes: bytes) -> int:
        """Write synthesized TTS audio bytes directly into session buffer."""
        written = buffer_manager.write_chunk(session_id, pcm_bytes)
        logger.info(f"AudioBufferStreamer: Pushed {written} TTS PCM bytes to session '{session_id}' buffer")
        return written


audio_buffer_streamer = AudioBufferStreamer()
