"""
Voice Gateway — Heartbeat monitor for ping/pong latency tracking and connection health checks.
"""
import time
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("backend.voice.gateway.heartbeat")


class VoiceHeartbeatMonitor:
    """Tracks WebSocket ping/pong timestamps and connection latency."""

    def __init__(self):
        self._last_ping: Dict[str, float] = {}
        self._latency_ms: Dict[str, float] = {}

    def record_ping(self, session_id: str) -> float:
        """Record ping timestamp and return timestamp."""
        now = time.time()
        self._last_ping[session_id] = now
        return now

    def record_pong(self, session_id: str) -> float:
        """Calculate round-trip latency on pong receipt."""
        now = time.time()
        ping_t = self._last_ping.get(session_id, now)
        rtt_ms = round((now - ping_t) * 1000, 2)
        self._latency_ms[session_id] = rtt_ms
        return rtt_ms

    def get_latency(self, session_id: str) -> float:
        """Return last recorded round-trip latency in ms."""
        return self._latency_ms.get(session_id, 15.0)


voice_heartbeat = VoiceHeartbeatMonitor()
