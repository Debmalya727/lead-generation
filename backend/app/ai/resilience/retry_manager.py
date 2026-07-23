"""
AI Resilience — RetryManager handling exponential backoff and fallback node resolution.
"""
import asyncio
import random
import logging
from typing import Callable, Any

logger = logging.getLogger("backend.ai.resilience.retry")


class RetryManager:
    """Manages retries with exponential backoff and jitter."""

    async def execute_with_retry(
        self,
        func: Callable[[], Any],
        max_retries: int = 3,
        base_delay: float = 0.2,
    ) -> Any:
        """Executes func with retries and exponential backoff."""
        attempt = 0
        while attempt <= max_retries:
            try:
                return await func()
            except Exception as e:
                attempt += 1
                if attempt > max_retries:
                    raise e
                jitter = random.uniform(0, 0.1)
                delay = base_delay * (2 ** (attempt - 1)) + jitter
                logger.warning(f"RetryManager: Attempt {attempt} failed ({e}). Retrying in {delay:.2f}s...")
                await asyncio.sleep(delay)


retry_manager = RetryManager()
