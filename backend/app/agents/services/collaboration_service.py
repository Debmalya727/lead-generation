"""
CollaborationService for Multi-Agent Collaboration Engine API.
"""
import logging
from typing import Dict, List, Optional, Any

from app.agents.collaboration.messages.bus import AgentMessageBus
from app.agents.collaboration.messages.message import AgentMessage
from app.agents.collaboration.coordination.manager import CollaborationManager
from app.agents.collaboration.delegation.engine import DelegationEngine
from app.agents.collaboration.artifacts.store import ArtifactStore
from app.agents.collaboration.consensus.engine import ConsensusEngine
from app.agents.collaboration.metrics.metrics_service import CollaborationMetricsService
from app.agents.schemas.collaboration import (
    SendMessageRequest,
    DelegationRequest,
    DelegationResponse,
)
from app.database.mongodb.collections.agent_collaboration import AgentConsensusDocument

logger = logging.getLogger("backend.agents.services.collaboration_service")


class CollaborationService:
    """Service layer managing collaboration API operations."""

    def __init__(self):
        self.bus = AgentMessageBus.get_instance()
        self.manager = CollaborationManager(self.bus)
        self.delegation_engine = DelegationEngine(self.bus)
        self.artifact_store = ArtifactStore()
        self.consensus_engine = ConsensusEngine()
        self.metrics_service = CollaborationMetricsService()

    async def get_messages(
        self,
        job_id: str,
        conversation_id: Optional[str] = None,
        agent_id: Optional[str] = None,
    ) -> List[AgentMessage]:
        """Fetch message history for job."""
        return await self.bus.history(job_id=job_id, conversation_id=conversation_id, agent_id=agent_id)

    async def send_message(self, job_id: str, payload: SendMessageRequest) -> AgentMessage:
        """Post an agent message."""
        msg = AgentMessage(
            job_id=job_id,
            task_id=payload.task_id,
            conversation_id=payload.conversation_id or f"conv_{job_id[:8]}",
            from_agent=payload.from_agent,
            to_agent=payload.to_agent,
            message_type=payload.message_type,
            payload=payload.payload,
        )
        return await self.manager.route_message(msg)

    async def get_artifacts(
        self,
        job_id: str,
        artifact_type: Optional[str] = None,
        owner_agent: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Fetch shared artifacts."""
        return await self.artifact_store.list_artifacts(job_id=job_id, artifact_type=artifact_type, owner_agent=owner_agent)

    async def get_consensus(self, job_id: str) -> List[Dict[str, Any]]:
        """Fetch consensus and conflict records."""
        try:
            docs = await AgentConsensusDocument.find(AgentConsensusDocument.job_id == job_id).sort("-resolved_at").to_list()
            return [
                {
                    "consensus_id": d.consensus_id,
                    "job_id": d.job_id,
                    "task_id": d.task_id,
                    "topic": d.topic,
                    "proposals": d.proposals,
                    "strategy_used": d.strategy_used,
                    "resolved_output": d.resolved_output,
                    "winning_agent": d.winning_agent,
                    "confidence": d.confidence,
                    "is_conflict": d.is_conflict,
                    "conflict_details": d.conflict_details,
                    "resolved_at": d.resolved_at.isoformat() if hasattr(d.resolved_at, 'isoformat') else str(d.resolved_at),
                }
                for d in docs
            ]
        except Exception as e:
            logger.warning(f"Error fetching consensus records for '{job_id}': {str(e)}")
            return []

    async def get_collaboration_summary(self, job_id: str) -> Dict[str, Any]:
        """Fetch job collaboration state summary."""
        return await self.manager.get_collaboration_summary(job_id)

    async def get_metrics(self, job_id: str) -> Dict[str, Any]:
        """Fetch job collaboration operational metrics."""
        return await self.metrics_service.get_job_metrics(job_id)

    async def delegate_task(self, job_id: str, owner_id: str, payload: DelegationRequest) -> DelegationResponse:
        """Delegate sub-task dynamically."""
        result = await self.delegation_engine.delegate(
            from_agent=payload.from_agent,
            target_agent_name=payload.target_agent,
            task_description=payload.task_description,
            job_id=job_id,
            owner_id=owner_id,
            inputs=payload.inputs,
            timeout_seconds=payload.timeout_seconds,
            max_retries=payload.max_retries,
            approval_required=payload.approval_required,
        )
        return DelegationResponse(
            status=result.status,
            confidence=result.confidence,
            messages=result.messages,
            outputs=result.outputs,
        )
