"""
CollaborationManager for Multi-Agent Collaboration Engine.

Responsibilities:
- Route agent messages (point-to-point, broadcast, group)
- Track active conversation threads
- Maintain collaboration state and metrics summary per job
"""
import uuid
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone

from app.agents.collaboration.messages.message import AgentMessage
from app.agents.collaboration.messages.bus import AgentMessageBus
from app.database.mongodb.collections.agent_collaboration import AgentCollaborationDocument

logger = logging.getLogger("backend.agents.collaboration.manager")


class CollaborationManager:
    """Manager coordinating multi-agent interactions, conversation threads, and routing."""

    def __init__(self, bus: Optional[AgentMessageBus] = None):
        self.bus = bus or AgentMessageBus.get_instance()
        self._conversations: Dict[str, Dict[str, Any]] = {}

    async def route_message(self, message: AgentMessage) -> AgentMessage:
        """Route message via bus and update collaboration state."""
        delivered = await self.bus.send(message)
        await self._update_job_collaboration_state(
            job_id=message.job_id,
            inc_messages=1,
            conversation_id=message.conversation_id,
        )
        return delivered

    async def start_conversation(
        self,
        job_id: str,
        topic: str,
        initiator: str,
        participants: List[str],
        initial_payload: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Start a new structured conversation thread between agents."""
        conv_id = f"conv_{uuid.uuid4().hex[:12]}"
        self._conversations[conv_id] = {
            "conversation_id": conv_id,
            "job_id": job_id,
            "topic": topic,
            "initiator": initiator,
            "participants": participants,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        # Broadcast initial message
        msg = AgentMessage(
            conversation_id=conv_id,
            job_id=job_id,
            from_agent=initiator,
            to_agent="group",
            message_type="proposal",
            payload={"topic": topic, "participants": participants, **(initial_payload or {})},
        )
        await self.bus.send(msg)

        await self._update_job_collaboration_state(
            job_id=job_id,
            inc_messages=1,
            conversation_id=conv_id,
        )

        logger.info(f"CollaborationManager started conversation '{conv_id}' on topic '{topic}' with participants {participants}")
        return conv_id

    async def get_active_conversations(self, job_id: str) -> List[Dict[str, Any]]:
        """Fetch active conversation threads for a job."""
        threads = [conv for conv in self._conversations.values() if conv.get("job_id") == job_id]
        if not threads:
            # Reconstruct from DB
            history = await self.bus.history(job_id=job_id)
            seen_convs: Dict[str, Dict[str, Any]] = {}
            for msg in history:
                cid = msg.conversation_id
                if cid not in seen_convs:
                    seen_convs[cid] = {
                        "conversation_id": cid,
                        "job_id": job_id,
                        "topic": msg.payload.get("topic", "Agent Interaction"),
                        "initiator": msg.from_agent,
                        "participants": [msg.from_agent, msg.to_agent],
                        "message_count": 1,
                        "latest_message_at": msg.timestamp.isoformat() if hasattr(msg.timestamp, 'isoformat') else str(msg.timestamp),
                    }
                else:
                    curr_count: int = seen_convs[cid]["message_count"]
                    seen_convs[cid]["message_count"] = curr_count + 1
                    seen_convs[cid]["latest_message_at"] = msg.timestamp.isoformat() if hasattr(msg.timestamp, 'isoformat') else str(msg.timestamp)
            threads = list(seen_convs.values())
        return threads

    async def get_collaboration_summary(self, job_id: str, owner_id: Optional[str] = None) -> Dict[str, Any]:
        """Fetch job-level collaboration state and metrics summary."""
        try:
            doc = await AgentCollaborationDocument.find_one(AgentCollaborationDocument.job_id == job_id)
            if doc:
                return {
                    "collaboration_id": doc.collaboration_id,
                    "job_id": doc.job_id,
                    "delegation_count": doc.delegation_count,
                    "conflict_count": doc.conflict_count,
                    "consensus_count": doc.consensus_count,
                    "message_count": doc.message_count,
                    "artifact_count": doc.artifact_count,
                    "active_conversations": doc.active_conversations,
                    "metrics_summary": doc.metrics_summary,
                    "updated_at": doc.updated_at.isoformat() if hasattr(doc.updated_at, 'isoformat') else str(doc.updated_at),
                }
        except Exception as e:
            logger.warning(f"Error fetching collaboration summary for '{job_id}': {str(e)}")

        # Fallback empty summary
        return {
            "job_id": job_id,
            "delegation_count": 0,
            "conflict_count": 0,
            "consensus_count": 0,
            "message_count": 0,
            "artifact_count": 0,
            "active_conversations": [],
            "metrics_summary": {},
        }

    async def record_interaction(self, job_id: str, interaction_type: str, details: Dict[str, Any]) -> None:
        """Record an explicit agent interaction event into collaboration state."""
        inc_del = 1 if interaction_type == "delegation" else 0
        inc_conf = 1 if interaction_type == "conflict" else 0
        inc_cons = 1 if interaction_type == "consensus" else 0
        inc_art = 1 if interaction_type == "artifact" else 0

        await self._update_job_collaboration_state(
            job_id=job_id,
            inc_delegations=inc_del,
            inc_conflicts=inc_conf,
            inc_consensus=inc_cons,
            inc_artifacts=inc_art,
            details=details,
        )

    async def _update_job_collaboration_state(
        self,
        job_id: str,
        inc_messages: int = 0,
        inc_delegations: int = 0,
        inc_conflicts: int = 0,
        inc_consensus: int = 0,
        inc_artifacts: int = 0,
        conversation_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Internal helper to upsert AgentCollaborationDocument in MongoDB."""
        try:
            doc = await AgentCollaborationDocument.find_one(AgentCollaborationDocument.job_id == job_id)
            if not doc:
                from bson import ObjectId
                doc = AgentCollaborationDocument(
                    collaboration_id=f"collab_{uuid.uuid4().hex[:12]}",
                    job_id=job_id,
                    owner_id=ObjectId(),  # Default fallback ID
                    active_conversations=[conversation_id] if conversation_id else [],
                    delegation_count=inc_delegations,
                    conflict_count=inc_conflicts,
                    consensus_count=inc_consensus,
                    message_count=inc_messages,
                    artifact_count=inc_artifacts,
                    metrics_summary=details or {},
                )
                await doc.insert()
            else:
                doc.message_count += inc_messages
                doc.delegation_count += inc_delegations
                doc.conflict_count += inc_conflicts
                doc.consensus_count += inc_consensus
                doc.artifact_count += inc_artifacts
                if conversation_id and conversation_id not in doc.active_conversations:
                    doc.active_conversations.append(conversation_id)
                if details:
                    doc.metrics_summary.update(details)
                doc.updated_at = datetime.now(timezone.utc)
                await doc.save()
        except Exception as e:
            logger.warning(f"Failed to update AgentCollaborationDocument for '{job_id}': {str(e)}")
