"""
AI Workflow Orchestrator — WorkflowRuntime for start, pause, resume, cancel, and checkpointing.
"""
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import logging

from app.database.mongodb.collections.ai_orchestrator import AIWorkflowRunDocument

logger = logging.getLogger("backend.ai.orchestrator.runtime")


class WorkflowRuntime:
    """Manages workflow runtime state transitions."""

    async def get_run(self, run_id: str) -> Optional[AIWorkflowRunDocument]:
        """Fetch workflow execution run by ID."""
        return await AIWorkflowRunDocument.find_one(AIWorkflowRunDocument.run_id == run_id)

    async def pause_run(self, run_id: str, checkpoint_state: Optional[Dict[str, Any]] = None) -> bool:
        """Pause a running workflow run."""
        doc = await self.get_run(run_id)
        if doc and doc.status == "running":
            doc.status = "paused"
            if checkpoint_state:
                doc.checkpoint_state = checkpoint_state
            await doc.save()
            logger.info(f"WorkflowRuntime: Paused run '{run_id}'")
            return True
        return False

    async def resume_run(self, run_id: str) -> bool:
        """Resume a paused workflow run."""
        doc = await self.get_run(run_id)
        if doc and doc.status == "paused":
            doc.status = "running"
            await doc.save()
            logger.info(f"WorkflowRuntime: Resumed run '{run_id}'")
            return True
        return False

    async def cancel_run(self, run_id: str) -> bool:
        """Cancel an active workflow run."""
        doc = await self.get_run(run_id)
        if doc and doc.status in ("pending", "running", "paused"):
            doc.status = "cancelled"
            doc.completed_at = datetime.now(timezone.utc)
            await doc.save()
            logger.info(f"WorkflowRuntime: Cancelled run '{run_id}'")
            return True
        return False


workflow_runtime = WorkflowRuntime()
