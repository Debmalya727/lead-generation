"""
AI Queue Manager — Dispatcher assigning priority items to workers.
"""
from typing import Any, Dict, Optional
import logging

from app.ai.queue.priority_queue import priority_queue, QueueItem

logger = logging.getLogger("backend.ai.queue.dispatcher")


class TaskDispatcher:
    """Dispatches priority queue items to execution handlers."""

    def dispatch_next(self) -> Optional[QueueItem]:
        """Fetch next highest priority item."""
        return priority_queue.pop()


task_dispatcher = TaskDispatcher()
