"""
Event Bus for Enterprise Agent Runtime.

Emits structured state transition events during DAG execution and persists them to MongoDB.
"""
import uuid
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from app.database.mongodb.repositories.agent_repository import AgentRepository
from app.database.mongodb.collections.agent_runtime import AgentEvent

logger = logging.getLogger("backend.agents.event_bus")


class EventBus:
    """Event Bus emitting structured execution state events."""

    def __init__(self, agent_repo: Optional[AgentRepository] = None):
        self.agent_repo = agent_repo or AgentRepository()

    async def emit(
        self,
        job_id: str,
        owner_id: str,
        event_type: str,
        source_agent: str = "AgentRuntime",
        task_id: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
    ) -> AgentEvent:
        """Emit and persist a state transition event."""
        event_id = f"evt_{uuid.uuid4().hex[:12]}"
        
        event_data = {
            "event_id": event_id,
            "job_id": job_id,
            "owner_id": owner_id,
            "event_type": event_type,
            "source_agent": source_agent,
            "task_id": task_id,
            "payload": payload or {},
            "timestamp": datetime.now(timezone.utc),
        }

        logger.info(f"EventBus Emitted Event [{event_type}] for Job '{job_id}' (Task: {task_id or 'N/A'})")
        
        try:
            return await self.agent_repo.create_event(event_data)
        except Exception as e:
            logger.warning(f"Failed to persist event {event_id}: {str(e)}")
            return AgentEvent(**event_data)
