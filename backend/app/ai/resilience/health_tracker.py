"""
AI Resilience — HealthTracker tracking provider health metrics and rolling success/error counts.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import logging

logger = logging.getLogger("backend.ai.resilience.health")


class HealthTracker:
    """Tracks real-time health metrics per provider."""

    def __init__(self):
        self._stats: Dict[str, Dict[str, Any]] = {}

    def get_health(self, provider: str) -> Dict[str, Any]:
        """Return provider health record."""
        if provider not in self._stats:
            self._stats[provider] = {
                "provider": provider,
                "state": "CLOSED",
                "consecutive_failures": 0,
                "total_successes": 0,
                "total_failures": 0,
                "avg_latency_ms": 0.0,
                "error_rate": 0.0,
            }
        return self._stats[provider]

    def record_success(self, provider: str, latency_ms: float = 0.0) -> None:
        """Record successful execution."""
        h = self.get_health(provider)
        h["consecutive_failures"] = 0
        h["total_successes"] += 1
        total = h["total_successes"] + h["total_failures"]
        h["error_rate"] = round(h["total_failures"] / max(total, 1), 4)

    def record_failure(self, provider: str) -> None:
        """Record failed execution."""
        h = self.get_health(provider)
        h["consecutive_failures"] += 1
        h["total_failures"] += 1
        total = h["total_successes"] + h["total_failures"]
        h["error_rate"] = round(h["total_failures"] / max(total, 1), 4)


health_tracker = HealthTracker()
