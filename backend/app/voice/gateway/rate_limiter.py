"""
Voice Gateway — RateLimiter preventing audio frame socket floods.
"""
import time
from typing import Dict, List
import logging

logger = logging.getLogger("backend.voice.gateway.rate_limiter")


class VoiceRateLimiter:
    """Limits incoming audio chunk frames per second per session."""

    def __init__(self, max_frames_per_sec: int = 100):
        self.max_frames_per_sec = max_frames_per_sec
        self._timestamps: Dict[str, List[float]] = {}

    def allow_frame(self, session_id: str) -> bool:
        """Check if frame is allowed under rate limit."""
        now = time.time()
        if session_id not in self._timestamps:
            self._timestamps[session_id] = []

        # Filter out frames older than 1 second
        self._timestamps[session_id] = [t for t in self._timestamps[session_id] if now - t <= 1.0]

        if len(self._timestamps[session_id]) >= self.max_frames_per_sec:
            logger.warning(f"VoiceRateLimiter: Frame rate limit exceeded for session '{session_id}'")
            return False

        self._timestamps[session_id].append(now)
        return True


voice_rate_limiter = VoiceRateLimiter()
