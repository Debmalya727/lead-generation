"""
InterruptionHandler — Detects user speech interruptions while system audio plays, cancels active LLM streaming and TTS synthesis, flushes circular playback buffers, and resets state.
"""
from typing import Dict, Optional, Any
import asyncio
import logging

from app.voice.audio.buffer_manager import buffer_manager
from app.voice.events.voice_events import voice_event_publisher

logger = logging.getLogger("backend.voice.bidirectional.interruption")


class InterruptionHandler:
    """Manages full duplex user speech interruption & audio buffer flushing."""

    def __init__(self):
        self._active_tts_tasks: Dict[str, asyncio.Task] = {}
        self._interrupted_flags: Dict[str, bool] = {}

    def register_tts_task(self, session_id: str, task: asyncio.Task) -> None:
        """Register active TTS synthesis task for session."""
        self._active_tts_tasks[session_id] = task
        self._interrupted_flags[session_id] = False

    async def handle_interruption(self, session_id: str) -> bool:
        """
        Triggered when VAD detects user speech while system audio is playing.
        Cancels active TTS synthesis task, flushes circular buffer, and emits Interruption event.
        """
        logger.warning(f"InterruptionHandler: Handling user interruption for session '{session_id}'!")
        self._interrupted_flags[session_id] = True

        # 1. Cancel active TTS synthesis task if running
        task = self._active_tts_tasks.pop(session_id, None)
        if task and not task.done():
            task.cancel()
            logger.info(f"InterruptionHandler: Cancelled active TTS synthesis task for '{session_id}'")

        # 2. Flush session CircularBuffer
        buf = buffer_manager.get_buffer(session_id)
        buf.clear()
        logger.info(f"InterruptionHandler: Cleared circular audio buffer for '{session_id}'")

        # 3. Publish Interruption event
        await voice_event_publisher.emit("Interruption", session_id, {"flushed_buffer": True})
        return True

    def is_interrupted(self, session_id: str) -> bool:
        """Return True if session was interrupted."""
        return self._interrupted_flags.get(session_id, False)


interruption_handler = InterruptionHandler()
