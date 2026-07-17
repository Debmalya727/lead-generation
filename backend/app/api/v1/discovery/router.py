from typing import List
from fastapi import APIRouter, Depends, status
from app.api.deps import get_current_user, get_discovery_module
from app.database.mongodb.collections.user import User
from app.modules.discovery.discovery_module import DiscoveryModule
from app.schemas.discovery import DiscoveryStartRequest, DiscoveredLeadResponse, JobStatusResponse, SaveLeadsRequest

router = APIRouter()


@router.post(
    "/start",
    response_model=JobStatusResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start a new lead discovery background job"
)
async def start_discovery(
    payload: DiscoveryStartRequest,
    current_user: User = Depends(get_current_user),
    discovery_module: DiscoveryModule = Depends(get_discovery_module)
):
    """Register a new lead discovery request and queue background scraping execution."""
    return await discovery_module.start_discovery(
        payload=payload,
        owner_id=str(current_user.id)
    )


@router.get(
    "/{job_id}",
    response_model=JobStatusResponse,
    summary="Get discovery job status and progress details"
)
async def get_job_status(
    job_id: str,
    current_user: User = Depends(get_current_user),
    discovery_module: DiscoveryModule = Depends(get_discovery_module)
):
    """Retrieve status, error messages, and progress markers for a specific job."""
    return await discovery_module.get_job_status(
        job_id=job_id,
        owner_id=str(current_user.id)
    )


@router.get(
    "/results/{job_id}",
    response_model=List[DiscoveredLeadResponse],
    summary="Get discovered business leads from a specific job"
)
async def get_job_results(
    job_id: str,
    current_user: User = Depends(get_current_user),
    discovery_module: DiscoveryModule = Depends(get_discovery_module)
):
    """Retrieve the parsed and deduplicated list of leads discovered by a specific job."""
    return await discovery_module.get_job_results(
        job_id=job_id,
        owner_id=str(current_user.id)
    )


@router.post(
    "/cancel/{job_id}",
    summary="Cancel a running discovery job"
)
async def cancel_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
    discovery_module: DiscoveryModule = Depends(get_discovery_module)
):
    """Request termination of an active background lead discovery job."""
    return await discovery_module.cancel_job(
        job_id=job_id,
        owner_id=str(current_user.id)
    )


@router.post(
    "/results/{job_id}/save",
    summary="Save selected leads to main leads list"
)
async def save_leads(
    job_id: str,
    payload: SaveLeadsRequest,
    current_user: User = Depends(get_current_user),
    discovery_module: DiscoveryModule = Depends(get_discovery_module)
):
    """Save selected leads from job extraction into the main businesses database, skipping duplicates."""
    return await discovery_module.save_selected_leads(
        job_id=job_id,
        payload=payload,
        owner_id=str(current_user.id)
    )
