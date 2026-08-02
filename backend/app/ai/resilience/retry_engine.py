"""
Enterprise Retry Engine for Phase 12.7 Enterprise AI Platform.
Implements exponential backoff with full jitter, per-provider retry policies,
timeout enforcement, and asyncio cancellation protection.
"""
import random
import asyncio
import logging
from typing import Callable, Any, Optional

logger = logging.getLogger("backend.ai.resilience.retry")


class RetryPolicy:
    """Configurable retry policy with exponential backoff and jitter."""

    def __init__(
        self,
        max_retries: int = 3,
        base_delay_seconds: float = 0.5,
        max_delay_seconds: float = 8.0,
        timeout_seconds: float = 30.0,
        jitter: bool = True,
    ):
        self.max_retries = max_retries
        self.base_delay_seconds = base_delay_seconds
        self.max_delay_seconds = max_delay_seconds
        self.timeout_seconds = timeout_seconds
        self.jitter = jitter

    def calculate_delay(self, attempt: int) -> float:
        """Calculate backoff delay for given attempt number."""
        calculated = min(self.max_delay_seconds, self.base_delay_seconds * (2 ** attempt))
        if self.jitter:
            return random.uniform(0, calculated)
        return calculated

    def is_retryable(self, error: Exception) -> bool:
        """Determine if an exception is transient and eligible for retry."""
        if isinstance(error, (asyncio.TimeoutError, TimeoutError)):
            return True
        err_msg = str(error).lower()
        non_retryable_terms = ["401", "unauthorized", "invalid_api_key", "403", "forbidden", "bad request"]
        if any(term in err_msg for term in non_retryable_terms):
            return False
        return True


class RetryEngine:
    """Execution engine wrapping provider async calls with retries, jitter, and timeouts."""

    @classmethod
    async def execute_with_retry(
        cls,
        func: Callable[[], Any],
        provider: str = "generic",
        policy: Optional[RetryPolicy] = None,
    ) -> Any:
        """Execute async function with exponential backoff, jitter, and timeout handling."""
        p = policy or RetryPolicy()
        last_exception = None

        for attempt in range(p.max_retries):
            try:
                # Enforce per-attempt timeout limit
                return await asyncio.wait_for(func(), timeout=p.timeout_seconds)
            except asyncio.CancelledError:
                logger.warning(f"⚡ [RetryEngine] Operation cancelled by caller for '{provider}'.")
                raise
            except Exception as e:
                last_exception = e
                if not p.is_retryable(e) or attempt == p.max_retries - 1:
                    logger.error(f"[RetryEngine] [{provider}] Permanent failure or max retries exhausted: {e}")
                    raise e

                delay = p.calculate_delay(attempt)
                logger.warning(
                    f"[RetryEngine] [{provider}] Retryable error on attempt {attempt + 1}/{p.max_retries}: {e}. "
                    f"Backing off for {delay:.2f}s..."
                )
                await asyncio.sleep(delay)

        if last_exception:
            raise last_exception
        raise RuntimeError(f"Retry execution failed for provider '{provider}'.")


retry_engine = RetryEngine()
