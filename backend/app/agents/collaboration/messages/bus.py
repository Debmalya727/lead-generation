"""
Agent Message Bus for Multi-Agent Collaboration Engine.

Enables decoupled agent-to-agent message passing supporting:
- Point-to-point messaging (send)
- Workspace broadcast (broadcast)
- Conversation thread reply (reply)
- History retrieval (history)
"""
import uuid
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone

from app.agents.collaboration.messages.message import AgentMessage
from app.database.mongodb.collections.agent_collaboration import AgentMessageDocument

logger = logging.getLogger("backend.agents.collaboration.bus")


class AgentMessageBus:
    """Central Agent Message Bus delivering agent messages and maintaining conversation history."""

    _instance: Optional['AgentMessageBus'] = None

    def __init__(self):
        self._listeners: Dict[str, List[Any]] = {}

    @classmethod
    def get_instance(cls) -> 'AgentMessageBus':
        """Singleton instance retriever."""
        if cls._instance is None:
            cls._instance = AgentMessageBus()
        return cls._instance

    async def send(self, message: AgentMessage) -> AgentMessage:
        """Deliver a point-to-point or targeted message."""
        logger.info(f"AgentMessageBus sending message '{message.message_id}' from '{message.from_agent}' to '{message.to_agent}'")
        message.status = "delivered"
        await self._persist(message)
        return message

    async def broadcast(
        self,
        job_id: str,
        from_agent: str,
        payload: Dict[str, Any],
        task_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        confidence: int = 100,
    ) -> AgentMessage:
        """Broadcast a message to all agents listening on job_id scope."""
        conv_id = conversation_id or f"conv_{uuid.uuid4().hex[:12]}"
        message = AgentMessage(
            job_id=job_id,
            task_id=task_id,
            conversation_id=conv_id,
            from_agent=from_agent,
            to_agent="broadcast",
            message_type="broadcast",
            payload=payload,
            confidence=confidence,
            status="delivered",
        )
        logger.info(f"AgentMessageBus broadcast from '{from_agent}' on job '{job_id}' (conv: '{conv_id}')")
        await self._persist(message)
        return message

    async def reply(
        self,
        parent_message: AgentMessage,
        from_agent: str,
        payload: Dict[str, Any],
        confidence: int = 100,
    ) -> AgentMessage:
        """Reply directly to an existing conversation thread."""
        reply_message = AgentMessage(
            job_id=parent_message.job_id,
            task_id=parent_message.task_id,
            conversation_id=parent_message.conversation_id,
            from_agent=from_agent,
            to_agent=parent_message.from_agent,
            message_type="reply",
            payload=payload,
            confidence=confidence,
            status="delivered",
        )
        logger.info(f"AgentMessageBus reply from '{from_agent}' to '{parent_message.from_agent}' in thread '{parent_message.conversation_id}'")
        await self._persist(reply_message)
        return reply_message

    async def history(
        self,
        job_id: str,
        conversation_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[AgentMessage]:
        """Fetch chronological message history for job or conversation thread."""
        try:
            query = [AgentMessageDocument.job_id == job_id]
            if conversation_id:
                query.append(AgentMessageDocument.conversation_id == conversation_id)
            if agent_id:
                # Agent either sent or received message
                query.append((AgentMessageDocument.from_agent == agent_id) | (AgentMessageDocument.to_agent == agent_id))

            docs = await AgentMessageDocument.find(*query).sort("+timestamp").limit(limit).to_list()
            return [
                AgentMessage(
                    message_id=d.message_id,
                    conversation_id=d.conversation_id,
                    job_id=d.job_id,
                    task_id=d.task_id,
                    from_agent=d.from_agent,
                    to_agent=d.to_agent,
                    message_type=d.message_type,
                    payload=d.payload,
                    confidence=d.confidence,
                    status=d.status,
                    timestamp=d.timestamp,
                )
                for d in docs
            ]
        except Exception as e:
            logger.warning(f"Error fetching message history for job '{job_id}': {str(e)}")
            return []

    async def _persist(self, msg: AgentMessage) -> None:
        """Persist message to MongoDB agent_messages collection."""
        try:
            doc = AgentMessageDocument(
                message_id=msg.message_id,
                conversation_id=msg.conversation_id,
                job_id=msg.job_id,
                task_id=msg.task_id,
                from_agent=msg.from_agent,
                to_agent=msg.to_agent,
                message_type=msg.message_type,
                payload=msg.payload,
                confidence=msg.confidence,
                status=msg.status,
                timestamp=msg.timestamp,
            )
            await doc.insert()
        except Exception as e:
            logger.warning(f"Failed to persist AgentMessageDocument '{msg.message_id}': {str(e)}")
