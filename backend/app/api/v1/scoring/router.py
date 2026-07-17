from fastapi import APIRouter, Depends, status
from app.api.deps import get_current_user, get_scoring_module
from app.database.mongodb.collections.user import User
from app.modules.scoring.scoring_module import ScoringModule
from app.schemas.scoring import (
    ScoringAnalyzeRequest,
    ScoringResponse,
    ScoringStatusResponse,
)

router = APIRouter()


@router.post(
    "/analyze",
    response_model=ScoringStatusResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Start or re-trigger AI lead scoring for a lead",
)
async def start_scoring(
    payload: ScoringAnalyzeRequest,
    current_user: User = Depends(get_current_user),
    scoring_module: ScoringModule = Depends(get_scoring_module),
):
    """
    Queue an AI-powered lead scoring job for the specified lead.
    Combines deterministic rule engine scoring with LLM reasoning.
    If a score already exists for this lead, it will be reset and re-computed.
    """
    return await scoring_module.start_scoring(
        payload=payload,
        owner_id=str(current_user.id),
    )


@router.get(
    "/job/{job_id}",
    response_model=ScoringStatusResponse,
    summary="Poll scoring job progress by job ID",
)
async def get_job_status(
    job_id: str,
    current_user: User = Depends(get_current_user),
    scoring_module: ScoringModule = Depends(get_scoring_module),
):
    """
    Poll the current status and progress of a scoring job by its document ID.
    Used for live progress bar updates on the frontend.
    """
    return await scoring_module.get_job_status(
        job_id=job_id,
        owner_id=str(current_user.id),
    )


@router.get(
    "/{lead_id}",
    response_model=ScoringResponse,
    summary="Get the complete scoring report for a lead",
)
async def get_score(
    lead_id: str,
    current_user: User = Depends(get_current_user),
    scoring_module: ScoringModule = Depends(get_scoring_module),
):
    """
    Retrieve the full structured scoring report previously computed for a lead.
    Returns 404 if no scoring has been run yet.
    """
    return await scoring_module.get_by_lead(
        lead_id=lead_id,
        owner_id=str(current_user.id),
    )


@router.delete(
    "/{lead_id}",
    summary="Delete the scoring report for a lead",
)
async def delete_score(
    lead_id: str,
    current_user: User = Depends(get_current_user),
    scoring_module: ScoringModule = Depends(get_scoring_module),
):
    """
    Permanently delete the scoring report associated with a lead.
    The lead itself is not affected.
    """
    return await scoring_module.delete_score(
        lead_id=lead_id,
        owner_id=str(current_user.id),
    )
