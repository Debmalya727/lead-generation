"""
AI Resilience — FailureMonitor evaluating failure thresholds.
"""
from typing import Dict, Any
import logging

from app.ai.resilience.health_tracker import health_tracker

logger = logging.getLogger("backend.ai.resilience.monitor")


class FailureMonitor:
    """Monitors consecutive failure thresholds per provider."""

    def __init__(self, failure_threshold: int = 5):
        self.failure_threshold = failure_threshold

    def should_trip_circuit(self, provider: str) -> bool:
        """Returns True if provider exceeded consecutive failure threshold."""
        health = health_tracker.get_health(provider)
        return health.get("consecutive_failures", 0) >= self.failure_threshold


failure_monitor = FailureMonitor()
