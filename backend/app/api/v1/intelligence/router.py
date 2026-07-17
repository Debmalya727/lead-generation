from fastapi import APIRouter, Depends, status
from app.api.deps import get_current_user, get_intelligence_module
from app.database.mongodb.collections.user import User
from app.modules.intelligence.intelligence_module import IntelligenceModule
from app.schemas.intelligence import (
    IntelligenceAnalyzeRequest,
    IntelligenceResponse,
    IntelligenceStatusResponse,
)

router = APIRouter()


@router.post(
    "/analyze",
    response_model=IntelligenceStatusResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Start or re-trigger AI intelligence analysis for a lead",
)
async def start_analysis(
    payload: IntelligenceAnalyzeRequest,
    current_user: User = Depends(get_current_user),
    intel_module: IntelligenceModule = Depends(get_intelligence_module),
):
    """
    Queue an AI-powered website analysis for the specified lead.
    If analysis already exists for this lead, it will be reset and re-run.
    """
    return await intel_module.start_analysis(
        payload=payload,
        owner_id=str(current_user.id),
    )


@router.get(
    "/job/{job_id}",
    response_model=IntelligenceStatusResponse,
    summary="Poll intelligence analysis job progress by job ID",
)
async def get_job_status(
    job_id: str,
    current_user: User = Depends(get_current_user),
    intel_module: IntelligenceModule = Depends(get_intelligence_module),
):
    """
    Poll the current status and progress of an analysis job by its internal document ID.
    Used for live progress bar updates during analysis.
    """
    return await intel_module.get_job_status(
        job_id=job_id,
        owner_id=str(current_user.id),
    )


@router.get(
    "/{lead_id}",
    response_model=IntelligenceResponse,
    summary="Get complete intelligence report for a lead",
)
async def get_intelligence(
    lead_id: str,
    current_user: User = Depends(get_current_user),
    intel_module: IntelligenceModule = Depends(get_intelligence_module),
):
    """
    Retrieve the full structured intelligence report previously extracted for a lead.
    Returns 404 if no analysis has been run yet.
    """
    return await intel_module.get_by_lead(
        lead_id=lead_id,
        owner_id=str(current_user.id),
    )


@router.delete(
    "/{lead_id}",
    summary="Delete the intelligence report for a lead",
)
async def delete_intelligence(
    lead_id: str,
    current_user: User = Depends(get_current_user),
    intel_module: IntelligenceModule = Depends(get_intelligence_module),
):
    """
    Permanently delete the intelligence report associated with a lead.
    The lead itself is not affected.
    """
    return await intel_module.delete_intelligence(
        lead_id=lead_id,
        owner_id=str(current_user.id),
    )
