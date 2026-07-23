"""
CheckpointEngine for Phase 11 — Milestone 4: Autonomous Workflow & Tool Orchestration Engine.

Manages execution state persistence, crash recovery snapshots, and workflow resumption.
"""
import uuid
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone

from app.database.mongodb.collections.agent_workflow import WorkflowCheckpointDocument

logger = logging.getLogger("backend.agents.workflow.checkpoints")


class CheckpointEngine:
    """Engine managing workflow state snapshots & crash recovery checkpoints."""

    async def save_checkpoint(
        self,
        execution_id: str,
        step_id: str,
        state_snapshot: Dict[str, Any],
        completed_step_ids: List[str],
        pending_step_ids: List[str],
        reason: str = "step_complete",
    ) -> Dict[str, Any]:
        """Save a new workflow execution state checkpoint snapshot."""
        checkpoint_id = f"chk_{uuid.uuid4().hex[:12]}"
        doc = WorkflowCheckpointDocument(
            checkpoint_id=checkpoint_id,
            execution_id=execution_id,
            step_id=step_id,
            state_snapshot=state_snapshot,
            completed_step_ids=completed_step_ids,
            pending_step_ids=pending_step_ids,
            reason=reason,
            created_at=datetime.now(timezone.utc),
        )
        await doc.insert()
        logger.info(f"CheckpointEngine: Saved snapshot '{checkpoint_id}' for execution '{execution_id}' at step '{step_id}'")
        return self._to_dict(doc)

    async def get_latest_checkpoint(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Fetch latest checkpoint snapshot for an execution."""
        doc = await WorkflowCheckpointDocument.find(
            WorkflowCheckpointDocument.execution_id == execution_id,
        ).sort("-created_at").first_or_none()
        return self._to_dict(doc) if doc else None

    async def list_checkpoints(self, execution_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Fetch all checkpoints for an execution."""
        docs = await WorkflowCheckpointDocument.find(
            WorkflowCheckpointDocument.execution_id == execution_id,
        ).sort("-created_at").limit(limit).to_list()
        return [self._to_dict(d) for d in docs]

    def _to_dict(self, doc: WorkflowCheckpointDocument) -> Dict[str, Any]:
        return {
            "checkpoint_id": doc.checkpoint_id,
            "execution_id": doc.execution_id,
            "step_id": doc.step_id,
            "state_snapshot": doc.state_snapshot,
            "completed_step_ids": doc.completed_step_ids,
            "pending_step_ids": doc.pending_step_ids,
            "reason": doc.reason,
            "created_at": doc.created_at.isoformat() if hasattr(doc.created_at, 'isoformat') else str(doc.created_at),
        }
