"""
Circuit Breaker Pattern for Enterprise Discovery Providers.
Prevents cascading failures by pausing requests to failing external directory providers.
"""
import time
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("backend.discovery.circuit_breaker")


class CircuitBreaker:
    """
    Manages circuit state (CLOSED, OPEN, HALF_OPEN) for a provider.
    - CLOSED: Normal operation. Errors increment failure counter.
    - OPEN: Provider failed threshold times. Rejects requests immediately for recovery period.
    - HALF_OPEN: Recovery period elapsed. Allows test probe request.
    """

    def __init__(self, provider_name: str, failure_threshold: int = 5, recovery_timeout: float = 60.0):
        self.provider_name = provider_name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        
        self.state = "closed" # "closed", "open", "half_open"
        self.failure_count = 0
        self.success_count = 0
        self.total_requests = 0
        self.last_failure_time: Optional[float] = None
        self.last_success_time: Optional[float] = None
        self.last_error: Optional[str] = None
        self.latencies: list = []

    def allow_request(self) -> bool:
        """Check if request is permitted under current circuit state."""
        now = time.time()
        if self.state == "closed":
            return True
        elif self.state == "open":
            if self.last_failure_time and (now - self.last_failure_time >= self.recovery_timeout):
                logger.info(f"Circuit Breaker for '{self.provider_name}' transitioning from OPEN -> HALF_OPEN (probing)")
                self.state = "half_open"
                return True
            return False
        elif self.state == "half_open":
            return True
        return True

    def record_success(self, latency_ms: float = 0.0) -> None:
        """Record successful call and reset failure counter if in HALF_OPEN state."""
        self.total_requests += 1
        self.success_count += 1
        self.last_success_time = time.time()
        
        if latency_ms > 0:
            self.latencies.append(latency_ms)
            if len(self.latencies) > 50:
                self.latencies.pop(0)

        if self.state in ("open", "half_open"):
            logger.info(f"Circuit Breaker for '{self.provider_name}' recovered! Transitioning to CLOSED state.")
            self.state = "closed"
            self.failure_count = 0

    def record_failure(self, error: Exception) -> None:
        """Record failed call and open circuit if failure threshold reached."""
        self.total_requests += 1
        self.failure_count += 1
        self.last_failure_time = time.time()
        self.last_error = str(error)

        if self.failure_count >= self.failure_threshold and self.state != "open":
            logger.warning(
                f"Circuit Breaker for '{self.provider_name}' OPENED due to {self.failure_count} consecutive failures. "
                f"Last error: {self.last_error}"
            )
            self.state = "open"

    def get_avg_latency(self) -> float:
        if not self.latencies:
            return 0.0
        return round(sum(self.latencies) / len(self.latencies), 2)

    def get_status_dict(self) -> Dict[str, Any]:
        return {
            "provider": self.provider_name,
            "circuit_state": self.state,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "total_requests": self.total_requests,
            "avg_latency_ms": self.get_avg_latency(),
            "last_error": self.last_error,
        }
