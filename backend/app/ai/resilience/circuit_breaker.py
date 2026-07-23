"""
AI Resilience — CircuitBreaker supporting CLOSED, OPEN, and HALF_OPEN states with automatic recovery.
"""
from typing import Dict, Any, Optional
import time
import logging
from datetime import datetime, timezone

from app.ai.resilience.health_tracker import health_tracker
from app.ai.resilience.failure_monitor import failure_monitor

logger = logging.getLogger("backend.ai.resilience.circuit_breaker")


class CircuitBreaker:
    """
    Circuit Breaker pattern for provider resilience:
    - CLOSED: Normal operation. Requests flow through.
    - OPEN: Provider is failing. Requests immediately fail / fallback to alternate.
    - HALF_OPEN: Cooldown period expired. Probing to check if provider recovered.
    """

    def __init__(self, cooldown_seconds: float = 30.0):
        self.cooldown_seconds = cooldown_seconds
        self._states: Dict[str, str] = {}  # provider → CLOSED | OPEN | HALF_OPEN
        self._cooldown_until: Dict[str, float] = {}

    def get_state(self, provider: str) -> str:
        """Get current circuit state for a provider."""
        current_state = self._states.get(provider, "CLOSED")

        if current_state == "OPEN":
            # Check if cooldown period expired
            cooldown = self._cooldown_until.get(provider, 0)
            if time.time() >= cooldown:
                logger.info(f"CircuitBreaker [{provider}]: Cooldown expired. State transition OPEN → HALF_OPEN")
                self._states[provider] = "HALF_OPEN"
                return "HALF_OPEN"

        return current_state

    def is_available(self, provider: str) -> bool:
        """Returns True if requests are allowed to provider."""
        state = self.get_state(provider)
        return state in ("CLOSED", "HALF_OPEN")

    def record_success(self, provider: str, latency_ms: float = 0.0) -> None:
        """Record success and handle recovery."""
        health_tracker.record_success(provider, latency_ms)
        state = self._states.get(provider, "CLOSED")

        if state == "HALF_OPEN":
            logger.info(f"CircuitBreaker [{provider}]: Probe successful! State transition HALF_OPEN → CLOSED")
            self._states[provider] = "CLOSED"
            self._cooldown_until.pop(provider, None)

    def record_failure(self, provider: str) -> None:
        """Record failure and handle tripping circuit."""
        health_tracker.record_failure(provider)

        if failure_monitor.should_trip_circuit(provider):
            logger.warning(f"CircuitBreaker [{provider}]: Failure threshold breached! Tripping circuit CLOSED/HALF_OPEN → OPEN")
            self._states[provider] = "OPEN"
            self._cooldown_until[provider] = time.time() + self.cooldown_seconds


circuit_breaker = CircuitBreaker()
