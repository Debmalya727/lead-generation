"""
StreamingManager for Multi-Agent Collaboration Engine.

Publishes live SSE (Server-Sent Events) and event streams for:
- Agent Messages
- Delegations
- Artifact Generation
- Progress Updates
- Consensus Decisions
- Conflict Detections
"""
import json
import asyncio
import logging
from typing import Dict, List, AsyncGenerator, Any, Optional
from datetime import datetime, timezone

logger = logging.getLogger("backend.agents.collaboration.streaming")


class StreamingManager:
    """Singleton streaming manager coordinating SSE event queues per job_id."""

    _instance: Optional['StreamingManager'] = None
    _subscribers: Dict[str, List[asyncio.Queue]] = {}

    @classmethod
    def get_instance(cls) -> 'StreamingManager':
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = StreamingManager()
        return cls._instance

    def publish(self, job_id: str, event_type: str, payload: Dict[str, Any], source_agent: str = "System") -> None:
        """Publish a real-time event to all active job subscribers."""
        queues = self._subscribers.get(job_id, [])
        if not queues:
            return

        event_data = {
            "job_id": job_id,
            "event_type": event_type,
            "source_agent": source_agent,
            "payload": payload,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        logger.debug(f"StreamingManager publishing '{event_type}' on job '{job_id}' to {len(queues)} subscribers")
        for q in queues:
            try:
                q.put_nowait(event_data)
            except asyncio.QueueFull:
                pass

    async def subscribe(self, job_id: str) -> AsyncGenerator[str, None]:
        """Async generator yielding SSE formatted event strings for a job."""
        queue: asyncio.Queue = asyncio.Queue(maxsize=100)
        if job_id not in self._subscribers:
            self._subscribers[job_id] = []
        self._subscribers[job_id].append(queue)

        try:
            # Yield initial connection ping
            yield f"data: {json.dumps({'event_type': 'connected', 'job_id': job_id})}\n\n"

            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=15.0)
                    yield f"data: {json.dumps(event)}\n\n"
                    if event.get("event_type") == "execution_finished":
                        break
                except asyncio.TimeoutError:
                    # Keepalive heartbeat
                    yield f": heartbeat\n\n"
        finally:
            if job_id in self._subscribers and queue in self._subscribers[job_id]:
                self._subscribers[job_id].remove(queue)
                if not self._subscribers[job_id]:
                    del self._subscribers[job_id]
