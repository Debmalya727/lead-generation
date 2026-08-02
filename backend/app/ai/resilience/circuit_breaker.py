"""
Enterprise Circuit Breaker State Machine for Phase 12.7 Enterprise AI Platform.
States: CLOSED -> OPEN -> HALF_OPEN -> CLOSED.
Protects AI provider endpoints from cascading failures and handles automatic recovery.
"""
import time
import logging
from typing import Dict, Any

logger = logging.getLogger("backend.ai.resilience.circuit_breaker")


class CircuitBreaker:
    """Enterprise Circuit Breaker for an individual AI provider endpoint."""

    def __init__(
        self,
        provider: str,
        failure_threshold: int = 5,
        recovery_timeout_seconds: float = 30.0,
        half_open_success_threshold: int = 2,
    ):
        self.provider = provider
        self.failure_threshold = failure_threshold
        self.recovery_timeout_seconds = recovery_timeout_seconds
        self.half_open_success_threshold = half_open_success_threshold

        self.state = "CLOSED"  # CLOSED | OPEN | HALF_OPEN
        self.consecutive_failures = 0
        self.half_open_successes = 0
        self.last_state_change = time.time()
        self.last_failure_time = 0.0

    def allow_request(self) -> bool:
        """Check whether a request is allowed to proceed based on circuit state."""
        now = time.time()
        if self.state == "CLOSED":
            return True
        elif self.state == "OPEN":
            if now - self.last_failure_time >= self.recovery_timeout_seconds:
                self._transition_to("HALF_OPEN")
                return True
            return False
        elif self.state == "HALF_OPEN":
            return True
        return True

    def record_success(self) -> None:
        """Record successful call to provider endpoint."""
        if self.state == "HALF_OPEN":
            self.half_open_successes += 1
            if self.half_open_successes >= self.half_open_success_threshold:
                self._transition_to("CLOSED")
        elif self.state == "CLOSED":
            self.consecutive_failures = 0

    def record_failure(self, error: Exception) -> None:
        """Record failed call to provider endpoint."""
        self.consecutive_failures += 1
        self.last_failure_time = time.time()
        if self.state == "CLOSED" and self.consecutive_failures >= self.failure_threshold:
            self._transition_to("OPEN")
        elif self.state == "HALF_OPEN":
            self._transition_to("OPEN")

    def _transition_to(self, new_state: str) -> None:
        prev = self.state
        self.state = new_state
        self.last_state_change = time.time()
        if new_state == "CLOSED":
            self.consecutive_failures = 0
            self.half_open_successes = 0
        elif new_state == "HALF_OPEN":
            self.half_open_successes = 0

        logger.warning(f"⚡ [CircuitBreaker] '{self.provider}' state transition: {prev} -> {new_state}")

    def get_status(self) -> Dict[str, Any]:
        return {
            "provider": self.provider,
            "state": self.state,
            "consecutive_failures": self.consecutive_failures,
            "half_open_successes": self.half_open_successes,
            "last_state_change": self.last_state_change,
        }


class CircuitBreakerRegistry:
    """Registry maintaining circuit breakers across all 9 AI providers."""

    def __init__(self):
        self._breakers: Dict[str, CircuitBreaker] = {}

    def get_breaker(self, provider: str) -> CircuitBreaker:
        key = provider.lower().strip()
        if key not in self._breakers:
            self._breakers[key] = CircuitBreaker(key)
        return self._breakers[key]

    def allow_request(self, provider: str) -> bool:
        return self.get_breaker(provider).allow_request()

    def record_success(self, provider: str) -> None:
        self.get_breaker(provider).record_success()

    def record_failure(self, provider: str, error: Exception) -> None:
        self.get_breaker(provider).record_failure(error)

    def get_all_statuses(self) -> Dict[str, Dict[str, Any]]:
        providers = ["gemini", "groq", "mistral", "openrouter", "openai", "claude", "deepseek", "ollama", "vllm"]
        for p in providers:
            self.get_breaker(p)
        return {p: b.get_status() for p, b in self._breakers.items()}


circuit_breaker_registry = CircuitBreakerRegistry()
circuit_breaker = circuit_breaker_registry
