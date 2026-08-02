"""
Enterprise Lead Discovery Platform REST API Router.
Exposes REST endpoints for starting discovery jobs, polling status, retrieving enriched leads,
deduplication merge logs, provider health monitoring, and analytics dashboards.
"""
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, status
from app.api.deps import get_current_user, get_discovery_module
from app.database.mongodb.collections.user import User
from app.modules.discovery.discovery_module import DiscoveryModule
from app.schemas.discovery import (
    DiscoveryStartRequest,
    JobStatusResponse,
    SaveLeadsRequest,
)

router = APIRouter()


@router.post(
    "/start",
    response_model=JobStatusResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start a new 9-stage lead discovery background job"
)
async def start_discovery(
    payload: DiscoveryStartRequest,
    current_user: User = Depends(get_current_user),
    discovery_module: DiscoveryModule = Depends(get_discovery_module)
):
    """Register a new lead discovery request and queue 9-stage Celery background pipeline."""
    return await discovery_module.start_discovery(
        payload=payload,
        owner_id=str(current_user.id)
    )


@router.get(
    "/providers",
    summary="List all discovery providers with capabilities and health status"
)
async def list_providers(
    discovery_module: DiscoveryModule = Depends(get_discovery_module)
):
    """Retrieve registered provider capabilities, circuit states, and health metrics."""
    return await discovery_module.get_provider_health()


@router.get(
    "/analytics/dashboard",
    summary="Get unified lead discovery platform analytics dashboard"
)
async def get_analytics_dashboard(
    current_user: User = Depends(get_current_user),
    discovery_module: DiscoveryModule = Depends(get_discovery_module)
):
    """Retrieve discovery volume, deduplication rates, quality distribution, and provider latency."""
    return await discovery_module.get_analytics_dashboard(owner_id=str(current_user.id))


@router.get(
    "/jobs/latest",
    response_model=JobStatusResponse,
    summary="Get user's most recent discovery job"
)
async def get_latest_job(
    current_user: User = Depends(get_current_user),
    discovery_module: DiscoveryModule = Depends(get_discovery_module)
):
    """Retrieve status, keyword, and location of current user's most recent job."""
    return await discovery_module.get_latest_job(owner_id=str(current_user.id))


@router.get(
    "/all/companies",
    summary="Get all canonical discovered leads across all jobs"
)
async def get_all_companies(
    current_user: User = Depends(get_current_user),
    discovery_module: DiscoveryModule = Depends(get_discovery_module)
):
    """Retrieve all normalized and enriched business leads for user."""
    return await discovery_module.get_all_discovered_companies(owner_id=str(current_user.id))


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
    """Retrieve status, error messages, and progress markers for a specific discovery job."""
    return await discovery_module.get_job_status(
        job_id=job_id,
        owner_id=str(current_user.id)
    )


@router.get(
    "/results/{job_id}",
    summary="Get canonical enriched business leads from a specific discovery job"
)
async def get_job_results(
    job_id: str,
    current_user: User = Depends(get_current_user),
    discovery_module: DiscoveryModule = Depends(get_discovery_module)
):
    """Retrieve the normalized, deduplicated, enriched, and scored leads for a job."""
    return await discovery_module.get_job_results(
        job_id=job_id,
        owner_id=str(current_user.id)
    )


@router.get(
    "/duplicates/{job_id}",
    summary="Get AI deduplication merge logs for a specific job"
)
async def get_job_duplicates(
    job_id: str,
    current_user: User = Depends(get_current_user),
    discovery_module: DiscoveryModule = Depends(get_discovery_module)
):
    """Retrieve audit merge logs showing duplicate matched records and confidence scores."""
    return await discovery_module.get_job_duplicates(
        job_id=job_id,
        owner_id=str(current_user.id)
    )


@router.post(
    "/cancel/{job_id}",
    summary="Cancel an active discovery job"
)
async def cancel_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
    discovery_module: DiscoveryModule = Depends(get_discovery_module)
):
    """Request dynamic termination of a running background discovery job."""
    return await discovery_module.cancel_job(
        job_id=job_id,
        owner_id=str(current_user.id)
    )


@router.post(
    "/results/{job_id}/save",
    summary="Import selected leads to CRM database"
)
async def save_leads(
    job_id: str,
    payload: SaveLeadsRequest,
    current_user: User = Depends(get_current_user),
    discovery_module: DiscoveryModule = Depends(get_discovery_module)
):
    """Import selected leads into CRM collection and dispatch LeadCRMCreatedEvent."""
    return await discovery_module.save_selected_leads(
        job_id=job_id,
        payload=payload,
        owner_id=str(current_user.id)
    )
