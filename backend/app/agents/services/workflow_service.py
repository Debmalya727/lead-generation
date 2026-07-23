"""
WorkflowService for Phase 11 — Milestone 4: Autonomous Workflow & Tool Orchestration Engine.
"""
import logging
from typing import Dict, List, Optional, Any
from bson import ObjectId

from app.agents.workflow.workflow_engine.engine import WorkflowEngine
from app.agents.tools.tool_registry.registry import ToolRegistry
from app.agents.tools.tool_executor.executor import ToolExecutor
from app.database.mongodb.collections.agent_workflow import (
    WorkflowExecutionDocument,
    WorkflowStepDocument,
    WorkflowCheckpointDocument,
)

logger = logging.getLogger("backend.agents.services.workflow_service")


class WorkflowService:
    """Service orchestrating workflow and tool API calls."""

    def __init__(self):
        self.engine = WorkflowEngine()
        self.tool_executor = ToolExecutor()

    async def run_workflow(
        self,
        workflow_id: str,
        owner_id: str,
        company_name: Optional[str] = None,
        lead_id: Optional[str] = None,
        inputs: Optional[Dict[str, Any]] = None,
        policy_id: Optional[str] = None,
    ) -> WorkflowExecutionDocument:
        """Run workflow by ID."""
        return await self.engine.run_workflow(
            workflow_id=workflow_id,
            owner_id=owner_id,
            company_name=company_name,
            lead_id=lead_id,
            custom_inputs=inputs,
            policy_id=policy_id,
        )

    async def list_executions(
        self,
        owner_id: str,
        status: Optional[str] = None,
        limit: int = 50,
        skip: int = 0,
    ) -> tuple[List[WorkflowExecutionDocument], int]:
        """List workflow executions for an owner."""
        query = []
        if ObjectId.is_valid(owner_id):
            query.append(WorkflowExecutionDocument.owner_id == ObjectId(owner_id))
        if status:
            query.append(WorkflowExecutionDocument.status == status)

        total = await WorkflowExecutionDocument.find(*query).count()
        docs = await WorkflowExecutionDocument.find(*query).sort("-created_at").skip(skip).limit(limit).to_list()
        return docs, total

    async def get_execution(self, execution_id: str, owner_id: str) -> Optional[WorkflowExecutionDocument]:
        """Fetch workflow execution by ID."""
        return await WorkflowExecutionDocument.find_one(WorkflowExecutionDocument.execution_id == execution_id)

    async def get_steps(self, execution_id: str) -> List[WorkflowStepDocument]:
        """Fetch workflow step executions."""
        return await WorkflowStepDocument.find(WorkflowStepDocument.execution_id == execution_id).sort("step_id").to_list()

    async def get_checkpoints(self, execution_id: str) -> List[WorkflowCheckpointDocument]:
        """Fetch workflow checkpoint snapshots."""
        return await WorkflowCheckpointDocument.find(WorkflowCheckpointDocument.execution_id == execution_id).sort("-created_at").to_list()

    def list_tools(self) -> List[Dict[str, Any]]:
        """List metadata for all registered tools."""
        return ToolRegistry.list_tools()

    def get_tool(self, tool_id: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a single tool."""
        tool = ToolRegistry.get(tool_id)
        return tool.to_dict() if tool else None

    async def execute_tool(self, tool_id: str, inputs: Dict[str, Any], invoker: str = "User") -> Dict[str, Any]:
        """Execute a registered tool directly."""
        return await self.tool_executor.execute_tool(tool_id=tool_id, inputs=inputs, invoker_agent=invoker)

    async def cancel_workflow(self, execution_id: str, owner_id: str) -> WorkflowExecutionDocument:
        """Cancel workflow execution."""
        return await self.engine.cancel_workflow(execution_id, owner_id)

    async def resume_workflow(self, execution_id: str, owner_id: str) -> WorkflowExecutionDocument:
        """Resume workflow execution from latest checkpoint."""
        return await self.engine.resume_workflow(execution_id, owner_id)
