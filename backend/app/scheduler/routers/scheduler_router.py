"""
REST API Router for Background Scheduler Workspace.
"""
from typing import List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.api.deps import get_current_user
from app.database.mongodb.collections.user import User
from app.scheduler.scheduler_service import SchedulerService

router = APIRouter()
scheduler_service = SchedulerService()


class CreateJobRequest(BaseModel):
    name: str
    workflow_template_id: str
    cron_expression: Optional[str] = None
    priority: str = "medium"
    description: Optional[str] = "Custom background job"
    inputs: Optional[dict] = Field(default_factory=dict)


@router.get(
    "/scheduler/jobs",
    summary="List Scheduled Background Jobs",
    description="Fetches all recurring and scheduled workflow jobs.",
)
async def list_jobs(current_user: User = Depends(get_current_user)):
    """List scheduled jobs."""
    await scheduler_service.initialize_prebuilt_jobs(str(current_user.id))
    return await scheduler_service.list_jobs(str(current_user.id))


@router.post(
    "/scheduler/jobs",
    summary="Create Scheduled Job",
    description="Creates a new scheduled background workflow job.",
)
async def create_job(payload: CreateJobRequest, current_user: User = Depends(get_current_user)):
    """Create scheduled job."""
    return await scheduler_service.create_job(
        name=payload.name,
        workflow_template_id=payload.workflow_template_id,
        cron_expression=payload.cron_expression,
        priority=payload.priority,
        description=payload.description or "Custom background job",
        inputs=payload.inputs,
        owner_id=str(current_user.id),
    )


@router.post(
    "/scheduler/job/{job_id}/run",
    summary="Trigger Job Immediately",
    description="Manually triggers immediate execution of a scheduled job via WorkflowEngine.",
)
async def run_job_now(job_id: str, current_user: User = Depends(get_current_user)):
    """Trigger job execution immediately."""
    try:
        hist, exec_id = await scheduler_service.run_job_now(job_id=job_id, owner_id=str(current_user.id))
        return {"status": "triggered", "execution_id": exec_id, "history": hist}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/scheduler/job/{job_id}/history",
    summary="Get Job Run History",
    description="Fetches historical execution runs for a background job.",
)
async def get_history(job_id: str, limit: int = Query(50), current_user: User = Depends(get_current_user)):
    """Fetch job execution history."""
    return await scheduler_service.get_history(job_id=job_id, limit=limit)
