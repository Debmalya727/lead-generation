"""
Phase 13.9 — Enterprise Call Queue Manager.
Manages inbound call routing queues with priority, wait times, and skill-based routing.
"""
from __future__ import annotations

import asyncio
import logging
import uuid
from collections import deque
from datetime import datetime, timezone
from typing import Any, Deque, Dict, List, Optional

logger = logging.getLogger("backend.telephony.call_queue_manager")


class QueuedCall:
    """Represents a call waiting in queue."""

    def __init__(
        self,
        call_id: str,
        provider: str,
        from_number: str,
        to_number: str,
        priority: int = 5,
        required_skill: Optional[str] = None,
        lead_id: Optional[str] = None,
    ):
        self.call_id = call_id
        self.provider = provider
        self.from_number = from_number
        self.to_number = to_number
        self.priority = priority
        self.required_skill = required_skill
        self.lead_id = lead_id
        self.queued_at = datetime.now(timezone.utc)
        self.queue_position: int = 0

    def wait_seconds(self) -> float:
        return (datetime.now(timezone.utc) - self.queued_at).total_seconds()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "call_id": self.call_id,
            "provider": self.provider,
            "from_number": self.from_number,
            "to_number": self.to_number,
            "priority": self.priority,
            "required_skill": self.required_skill,
            "lead_id": self.lead_id,
            "queue_position": self.queue_position,
            "wait_seconds": round(self.wait_seconds(), 2),
            "queued_at": self.queued_at.isoformat(),
        }


class CallQueueManager:
    """Priority-based call queue with skill-based routing support."""

    def __init__(self):
        # key: skill_tag → sorted deque of QueuedCall
        self._queues: Dict[str, Deque[QueuedCall]] = {
            "sales": deque(),
            "support": deque(),
            "enterprise": deque(),
            "general": deque(),
        }
        self._lock = asyncio.Lock()

    async def enqueue(
        self,
        call_id: str,
        provider: str,
        from_number: str,
        to_number: str,
        priority: int = 5,
        required_skill: str = "general",
        lead_id: Optional[str] = None,
    ) -> QueuedCall:
        """Add a call to the appropriate skill queue."""
        queue_key = required_skill if required_skill in self._queues else "general"
        qc = QueuedCall(
            call_id=call_id,
            provider=provider,
            from_number=from_number,
            to_number=to_number,
            priority=priority,
            required_skill=queue_key,
            lead_id=lead_id,
        )
        async with self._lock:
            # Insert by priority (lower value = higher priority)
            q = list(self._queues[queue_key])
            q.append(qc)
            q.sort(key=lambda x: x.priority)
            self._queues[queue_key] = deque(q)
            qc.queue_position = list(self._queues[queue_key]).index(qc) + 1

        logger.info(f"[CallQueue] Enqueued call '{call_id}' → queue='{queue_key}' priority={priority}")
        return qc

    async def dequeue(self, queue_key: str = "general") -> Optional[QueuedCall]:
        """Pop the highest-priority call from a queue."""
        async with self._lock:
            q = self._queues.get(queue_key, deque())
            if q:
                call = q.popleft()
                logger.info(f"[CallQueue] Dequeued call '{call.call_id}' from '{queue_key}'")
                return call
        return None

    def queue_stats(self) -> Dict[str, Any]:
        """Return live queue lengths and average wait times per skill queue."""
        stats = {}
        for key, q in self._queues.items():
            calls = list(q)
            avg_wait = sum(c.wait_seconds() for c in calls) / len(calls) if calls else 0.0
            stats[key] = {
                "depth": len(calls),
                "avg_wait_seconds": round(avg_wait, 2),
                "calls": [c.to_dict() for c in calls[:5]],  # first 5 only
            }
        return stats

    def remove_call(self, call_id: str) -> bool:
        """Remove a specific call from any queue (on answer/abandon)."""
        for key, q in self._queues.items():
            calls = [c for c in q if c.call_id != call_id]
            if len(calls) < len(q):
                self._queues[key] = deque(calls)
                logger.info(f"[CallQueue] Removed call '{call_id}' from queue '{key}'")
                return True
        return False

    def list_queued_calls(self) -> List[Dict[str, Any]]:
        all_calls = []
        for q in self._queues.values():
            all_calls.extend([c.to_dict() for c in q])
        return all_calls


call_queue_manager = CallQueueManager()
