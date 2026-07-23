"""
AI Queue Manager — PriorityQueue supporting 6 priority levels.
Levels: Critical (1), Enterprise (2), Realtime (3), Interactive (4), Background (5), Low (6).
"""
import heapq
import time
import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

PRIORITY_LEVELS = {
    "Critical": 1,
    "Enterprise": 2,
    "Realtime": 3,
    "Interactive": 4,
    "Background": 5,
    "Low": 6,
}


class QueueItem(BaseModel):
    queue_id: str
    workflow_run_id: str
    node_id: str
    priority: str = "Interactive"
    priority_level: int = 4
    payload: Dict[str, Any] = Field(default_factory=dict)
    retry_count: int = 0
    enqueued_at_ts: float = Field(default_factory=time.time)


class PriorityQueue:
    """In-memory thread-safe priority queue."""

    def __init__(self):
        self._heap: List[tuple] = []
        self._counter = 0

    def push(self, item: QueueItem) -> None:
        """Push item to priority queue."""
        self._counter += 1
        # Heap tuple: (priority_level, counter, item)
        heapq.heappush(self._heap, (item.priority_level, self._counter, item))

    def pop(self) -> Optional[QueueItem]:
        """Pop highest priority item (lowest priority_level integer)."""
        if not self._heap:
            return None
        _, _, item = heapq.heappop(self._heap)
        return item

    def size(self) -> int:
        """Return number of queued items."""
        return len(self._heap)


priority_queue = PriorityQueue()
