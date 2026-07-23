"""
REST API Router for Autonomous Workflow & Tool Orchestration Engine.
"""
from typing import List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import get_current_user, get_workflow_service
from app.database.mongodb.collections.user import User
from app.agents.services.workflow_service import WorkflowService
from app.agents.schemas.workflow import (
    WorkflowRunRequest,
    WorkflowExecutionResponse,
    WorkflowExecutionListResponse,
    WorkflowStepResponse,
    WorkflowCheckpointResponse,
    ToolMetadataResponse,
    ToolExecuteRequest,
    ToolExecutionResponse,
)

router = APIRouter()


@router.post(
    "/workflows/run",
    response_model=WorkflowExecutionResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Run Autonomous Workflow",
    description="Launch execution of a pre-built workflow template or custom workflow specification.",
)
async def run_workflow(
    payload: WorkflowRunRequest,
    current_user: User = Depends(get_current_user),
    service: WorkflowService = Depends(get_workflow_service),
):
    """Run workflow by ID."""
    return await service.run_workflow(
        workflow_id=payload.workflow_id,
        owner_id=str(current_user.id),
        company_name=payload.company_name,
        lead_id=payload.lead_id,
        inputs=payload.inputs,
        policy_id=payload.policy_id,
    )


@router.get(
    "/workflows",
    response_model=WorkflowExecutionListResponse,
    summary="List Workflow Executions",
)
async def list_workflows(
    status_filter: Optional[str] = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=100),
    skip: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    service: WorkflowService = Depends(get_workflow_service),
):
    """List workflow executions with status filtering."""
    items, total = await service.list_executions(owner_id=str(current_user.id), status=status_filter, limit=limit, skip=skip)
    return WorkflowExecutionListResponse(total_count=total, items=items)


@router.get(
    "/tools",
    response_model=List[ToolMetadataResponse],
    summary="List Registered Tools",
    description="Returns metadata, schema specifications, and timeouts for all tools registered in ToolRegistry.",
)
async def list_tools(
    current_user: User = Depends(get_current_user),
    service: WorkflowService = Depends(get_workflow_service),
):
    """List all registered tools."""
    return service.list_tools()


@router.get(
    "/tools/{tool_id}",
    response_model=ToolMetadataResponse,
    summary="Get Tool Details",
)
async def get_tool(
    tool_id: str,
    current_user: User = Depends(get_current_user),
    service: WorkflowService = Depends(get_workflow_service),
):
    """Fetch tool metadata by tool_id."""
    tool = service.get_tool(tool_id)
    if not tool:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Tool '{tool_id}' not found.")
    return tool


@router.post(
    "/tools/{tool_id}/execute",
    response_model=ToolExecutionResponse,
    summary="Execute Single Tool",
    description="Directly execute a tool with schema validation, timeouts, and cost tracking.",
)
async def execute_tool(
    tool_id: str,
    payload: ToolExecuteRequest,
    current_user: User = Depends(get_current_user),
    service: WorkflowService = Depends(get_workflow_service),
):
    """Execute a single tool."""
    return await service.execute_tool(tool_id=tool_id, inputs=payload.inputs, invoker=payload.invoker_agent)


@router.get(
    "/workflows/{execution_id}",
    response_model=WorkflowExecutionResponse,
    summary="Get Workflow Execution Details",
)
async def get_workflow_execution(
    execution_id: str,
    current_user: User = Depends(get_current_user),
    service: WorkflowService = Depends(get_workflow_service),
):
    """Fetch workflow execution by ID."""
    execution = await service.get_execution(execution_id, str(current_user.id))
    if not execution:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Workflow execution '{execution_id}' not found.")
    return execution


@router.get(
    "/workflows/{execution_id}/steps",
    response_model=List[WorkflowStepResponse],
    summary="Get Workflow Execution Steps",
)
async def get_workflow_steps(
    execution_id: str,
    current_user: User = Depends(get_current_user),
    service: WorkflowService = Depends(get_workflow_service),
):
    """Fetch step executions for a workflow."""
    return await service.get_steps(execution_id)


@router.get(
    "/workflows/{execution_id}/checkpoints",
    response_model=List[WorkflowCheckpointResponse],
    summary="Get Workflow Execution Checkpoints",
)
async def get_workflow_checkpoints(
    execution_id: str,
    current_user: User = Depends(get_current_user),
    service: WorkflowService = Depends(get_workflow_service),
):
    """Fetch state checkpoints for a workflow."""
    return await service.get_checkpoints(execution_id)


@router.post(
    "/workflows/{execution_id}/cancel",
    response_model=WorkflowExecutionResponse,
    summary="Cancel Workflow Execution",
)
async def cancel_workflow(
    execution_id: str,
    current_user: User = Depends(get_current_user),
    service: WorkflowService = Depends(get_workflow_service),
):
    """Cancel a running workflow execution."""
    return await service.cancel_workflow(execution_id, str(current_user.id))


@router.post(
    "/workflows/{execution_id}/resume",
    response_model=WorkflowExecutionResponse,
    summary="Resume Workflow Execution",
)
async def resume_workflow(
    execution_id: str,
    current_user: User = Depends(get_current_user),
    service: WorkflowService = Depends(get_workflow_service),
):
    """Resume a paused workflow from its latest checkpoint."""
    return await service.resume_workflow(execution_id, str(current_user.id))
