"""
AI Queue Manager — QueueManager top-level orchestrator with dead-letter queue and retry capabilities.
"""
import uuid
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from app.ai.queue.priority_queue import priority_queue, QueueItem, PRIORITY_LEVELS
from app.database.mongodb.collections.ai_orchestrator import (
    AIQueueDocument,
    AIDeadLetterQueueDocument,
)

logger = logging.getLogger("backend.ai.queue.manager")


class QueueManager:
    """Manages priority task queueing, dead-letter routing, and retry operations."""

    async def enqueue(
        self,
        workflow_run_id: str,
        node_id: str,
        payload: Dict[str, Any],
        priority: str = "Interactive",
    ) -> QueueItem:
        """Enqueue task into PriorityQueue and persist in MongoDB."""
        queue_id = f"q_{uuid.uuid4().hex[:12]}"
        priority_level = PRIORITY_LEVELS.get(priority, 4)

        item = QueueItem(
            queue_id=queue_id,
            workflow_run_id=workflow_run_id,
            node_id=node_id,
            priority=priority,
            priority_level=priority_level,
            payload=payload,
        )

        priority_queue.push(item)

        try:
            doc = AIQueueDocument(
                queue_id=queue_id,
                workflow_run_id=workflow_run_id,
                node_id=node_id,
                priority=priority,
                priority_level=priority_level,
                payload=payload,
                status="queued",
            )
            await doc.insert()
        except Exception as e:
            logger.debug(f"QueueManager: Queue doc persistence skipped: {e}")

        logger.info(f"QueueManager: Enqueued item '{queue_id}' (priority={priority}, level={priority_level})")
        return item

    async def move_to_dead_letter(
        self,
        queue_id: str,
        workflow_run_id: str,
        node_id: str,
        payload: Dict[str, Any],
        failure_reason: str,
    ) -> AIDeadLetterQueueDocument:
        """Move permanently failed task to Dead Letter Queue."""
        dlq_id = f"dlq_{uuid.uuid4().hex[:12]}"
        doc = AIDeadLetterQueueDocument(
            dlq_id=dlq_id,
            original_queue_id=queue_id,
            workflow_run_id=workflow_run_id,
            node_id=node_id,
            payload=payload,
            failure_reason=failure_reason,
        )
        await doc.insert()
        logger.warning(f"QueueManager: Moved item '{queue_id}' to DLQ (dlq_id={dlq_id}, reason='{failure_reason}')")
        return doc

    async def retry_dlq_item(self, dlq_id: str) -> Optional[QueueItem]:
        """Retry a task from the dead-letter queue."""
        doc = await AIDeadLetterQueueDocument.find_one(AIDeadLetterQueueDocument.dlq_id == dlq_id)
        if not doc:
            return None

        doc.retried = True
        doc.retried_at = datetime.now(timezone.utc)
        await doc.save()

        return await self.enqueue(
            workflow_run_id=doc.workflow_run_id,
            node_id=doc.node_id,
            payload=doc.payload,
            priority="Critical",
        )

    async def get_queue_stats(self) -> Dict[str, Any]:
        """Return metrics on priority queue and dead-letter queue."""
        dlq_count = await AIDeadLetterQueueDocument.find(AIDeadLetterQueueDocument.retried == False).count()
        return {
            "in_memory_depth": priority_queue.size(),
            "dlq_unresolved_count": dlq_count,
            "supported_priorities": list(PRIORITY_LEVELS.keys()),
        }


queue_manager = QueueManager()
