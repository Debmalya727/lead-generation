from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse

from app.api.deps import get_current_user, get_agent_service, get_collaboration_service
from app.database.mongodb.collections.user import User
from app.agents.services.agent_service import AgentService
from app.agents.services.collaboration_service import CollaborationService
from app.agents.schemas.agent import (
    AgentRunRequest,
    AgentJobResponse,
    AgentJobListResponse,
    AgentEventResponse,
    AgentApprovalRequest,
    ExecutiveReportResponse,
    AgentRegistryItemResponse,
)
from app.agents.schemas.collaboration import (
    AgentMessageSchema,
    SendMessageRequest,
    AgentArtifactSchema,
    ConsensusDecisionSchema,
    DelegationRequest,
    DelegationResponse,
    CollaborationMetricsSchema,
    CollaborationSummaryResponse,
)
from app.agents.collaboration.streaming.stream_manager import StreamingManager

router = APIRouter()


@router.post(
    "/run",
    response_model=AgentJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit Goal for Autonomous Execution",
    description="Decompose natural language goal into a DAG ExecutionPlan and enqueue job in Celery worker execution queue.",
)
async def submit_agent_job(
    payload: AgentRunRequest,
    current_user: User = Depends(get_current_user),
    service: AgentService = Depends(get_agent_service),
):
    """Submit goal for autonomous agent runtime execution."""
    job = await service.submit_job(
        goal=payload.goal,
        owner_id=str(current_user.id),
        lead_id=payload.lead_id,
        execution_mode=payload.execution_mode,
        company_name=payload.company_name,
    )
    return job


@router.get(
    "/jobs",
    response_model=AgentJobListResponse,
    summary="List Workspace Agent Jobs",
)
async def list_agent_jobs(
    status_filter: str = Query(None, alias="status"),
    lead_id: str = Query(None),
    limit: int = Query(50, ge=1, le=100),
    skip: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    service: AgentService = Depends(get_agent_service),
):
    """List agent execution jobs with pagination and filters."""
    jobs, total_count = await service.list_jobs(
        owner_id=str(current_user.id),
        status=status_filter,
        lead_id=lead_id,
        limit=limit,
        skip=skip,
    )
    return AgentJobListResponse(total_count=total_count, items=jobs)


@router.get(
    "/registry/agents",
    response_model=List[AgentRegistryItemResponse],
    summary="List Registered Agents",
    description="Returns all registered AI agents and their capabilities.",
)
async def list_registered_agents(
    current_user: User = Depends(get_current_user),
    service: AgentService = Depends(get_agent_service),
):
    """List all registered AI agents in the runtime registry."""
    return service.list_registered_agents()


@router.get(
    "/{job_id}",
    response_model=AgentJobResponse,
    summary="Get Agent Job Status & Plan",
)
async def get_agent_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
    service: AgentService = Depends(get_agent_service),
):
    """Fetch AgentJob details by ID."""
    job = await service.get_job(job_id, str(current_user.id))
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Job '{job_id}' not found.")
    return job


@router.get(
    "/{job_id}/timeline",
    response_model=List[AgentEventResponse],
    summary="Get Execution Event Timeline",
)
async def get_job_timeline(
    job_id: str,
    current_user: User = Depends(get_current_user),
    service: AgentService = Depends(get_agent_service),
):
    """Fetch chronological event timeline for a job."""
    events = await service.get_job_events(job_id, str(current_user.id))
    return events


@router.get(
    "/{job_id}/events",
    response_model=List[AgentEventResponse],
    summary="Get Raw State Events",
)
async def get_job_events(
    job_id: str,
    current_user: User = Depends(get_current_user),
    service: AgentService = Depends(get_agent_service),
):
    """Fetch raw state transition events for job."""
    events = await service.get_job_events(job_id, str(current_user.id))
    return events


@router.get(
    "/{job_id}/graph",
    summary="Get DAG Task Graph Topology",
)
async def get_job_graph(
    job_id: str,
    current_user: User = Depends(get_current_user),
    service: AgentService = Depends(get_agent_service),
):
    """Fetch task graph topology JSON structure."""
    job = await service.get_job(job_id, str(current_user.id))
    if not job or not job.plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Job '{job_id}' not found.")
    return job.plan.task_graph_json


@router.post(
    "/{job_id}/cancel",
    response_model=AgentJobResponse,
    summary="Cancel Job Execution",
)
async def cancel_job_endpoint(
    job_id: str,
    current_user: User = Depends(get_current_user),
    service: AgentService = Depends(get_agent_service),
):
    """Cancel job execution."""
    return await service.cancel_job(job_id, str(current_user.id))


@router.post(
    "/{job_id}/retry",
    response_model=AgentJobResponse,
    summary="Retry Job Execution",
)
async def retry_job_endpoint(
    job_id: str,
    current_user: User = Depends(get_current_user),
    service: AgentService = Depends(get_agent_service),
):
    """Retry failed or cancelled job execution."""
    return await service.retry_job(job_id, str(current_user.id))


@router.post(
    "/{job_id}/approve",
    response_model=AgentJobResponse,
    summary="Approve Human Approval Task Node",
)
async def approve_task_endpoint(
    job_id: str,
    payload: AgentApprovalRequest,
    current_user: User = Depends(get_current_user),
    service: AgentService = Depends(get_agent_service),
):
    """Approve a paused task node and resume DAG execution."""
    return await service.approve_task_node(job_id, payload.task_id, str(current_user.id))


@router.get(
    "/{job_id}/report",
    response_model=ExecutiveReportResponse,
    summary="Get Executive Sales Report",
    description="Retrieve the final consolidated executive sales report generated by ExecutiveAgent for a completed business pipeline job.",
)
async def get_executive_report(
    job_id: str,
    current_user: User = Depends(get_current_user),
    service: AgentService = Depends(get_agent_service),
):
    """Fetch the executive report for a completed business pipeline job."""
    report = await service.get_executive_report(job_id, str(current_user.id))
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Executive report for job '{job_id}' not found. Ensure the job is completed and ran in business pipeline mode.",
        )
    return report


# ──────────────────────────────────────────────────────────────────────────────
# Phase 11 — Milestone 3: Collaboration API Endpoints
# ──────────────────────────────────────────────────────────────────────────────

@router.get(
    "/{job_id}/messages",
    response_model=List[AgentMessageSchema],
    summary="Get Agent Messages History",
    description="Fetch chronological message history passed between agents during job execution.",
)
async def get_agent_messages(
    job_id: str,
    conversation_id: Optional[str] = Query(None),
    agent_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    service: CollaborationService = Depends(get_collaboration_service),
):
    """Fetch agent message history."""
    return await service.get_messages(job_id, conversation_id=conversation_id, agent_id=agent_id)


@router.post(
    "/{job_id}/message",
    response_model=AgentMessageSchema,
    summary="Post Agent Message",
    description="Send a message between agents or trigger a broadcast.",
)
async def post_agent_message(
    job_id: str,
    payload: SendMessageRequest,
    current_user: User = Depends(get_current_user),
    service: CollaborationService = Depends(get_collaboration_service),
):
    """Post an agent message."""
    return await service.send_message(job_id, payload)


@router.get(
    "/{job_id}/artifacts",
    response_model=List[AgentArtifactSchema],
    summary="Get Shared Agent Artifacts",
    description="Fetch versioned shared artifacts generated by agents for this job.",
)
async def get_agent_artifacts(
    job_id: str,
    artifact_type: Optional[str] = Query(None),
    owner_agent: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    service: CollaborationService = Depends(get_collaboration_service),
):
    """Fetch shared agent artifacts."""
    return await service.get_artifacts(job_id, artifact_type=artifact_type, owner_agent=owner_agent)


@router.get(
    "/{job_id}/consensus",
    response_model=List[ConsensusDecisionSchema],
    summary="Get Consensus & Conflict Resolution Log",
    description="Fetch consensus decisions and detected conflict resolutions for this job.",
)
async def get_agent_consensus(
    job_id: str,
    current_user: User = Depends(get_current_user),
    service: CollaborationService = Depends(get_collaboration_service),
):
    """Fetch consensus decisions."""
    return await service.get_consensus(job_id)


@router.get(
    "/{job_id}/collaboration",
    response_model=CollaborationSummaryResponse,
    summary="Get Collaboration Summary State",
    description="Fetch overall job collaboration summary, conversation count, delegations, and conflicts.",
)
async def get_collaboration_summary(
    job_id: str,
    current_user: User = Depends(get_current_user),
    service: CollaborationService = Depends(get_collaboration_service),
):
    """Fetch collaboration state summary."""
    return await service.get_collaboration_summary(job_id)


@router.get(
    "/{job_id}/metrics",
    response_model=CollaborationMetricsSchema,
    summary="Get Operational Collaboration Metrics",
    description="Fetch agent utilization %, execution latency, parallel efficiency, and interaction counts.",
)
async def get_collaboration_metrics(
    job_id: str,
    current_user: User = Depends(get_current_user),
    service: CollaborationService = Depends(get_collaboration_service),
):
    """Fetch collaboration metrics."""
    return await service.get_metrics(job_id)


@router.post(
    "/{job_id}/delegate",
    response_model=DelegationResponse,
    summary="Delegate Sub-Task Between Agents",
    description="Trigger inter-agent delegation of a sub-task with timeout, retry, and failure recovery.",
)
async def delegate_subtask(
    job_id: str,
    payload: DelegationRequest,
    current_user: User = Depends(get_current_user),
    service: CollaborationService = Depends(get_collaboration_service),
):
    """Delegate sub-task dynamically."""
    return await service.delegate_task(job_id, str(current_user.id), payload)


@router.get(
    "/{job_id}/stream",
    summary="Live SSE Event Stream",
    description="Subscribe to real-time Server-Sent Events (SSE) stream for live agent messages, delegations, artifacts, and progress.",
)
async def stream_job_events(
    job_id: str,
    current_user: User = Depends(get_current_user),
):
    """Stream real-time SSE events for job."""
    sm = StreamingManager.get_instance()
    return StreamingResponse(sm.subscribe(job_id), media_type="text/event-stream")

