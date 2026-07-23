"""
REST API Router for Enterprise Platform Hardening & Diagnostic Health.
"""
from typing import List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.api.deps import get_current_user, get_platform_service
from app.database.mongodb.collections.user import User
from app.platform.services.platform_service import PlatformService

router = APIRouter()


class FeatureFlagRequest(BaseModel):
    flag_key: str
    is_enabled: bool
    name: Optional[str] = None


@router.get(
    "/health",
    summary="Get Operational System Health",
    description="Returns deep diagnostic health status across API, MongoDB, Redis, Celery workers, and Gateway.",
)
async def get_health(service: PlatformService = Depends(get_platform_service)):
    """Fetch health diagnostics."""
    return await service.get_health()


@router.get(
    "/metrics",
    summary="Get System Metrics",
    description="Returns telemetry metrics for workflows, tools, agents, latency, memory, and CPU utilization.",
)
async def get_metrics(service: PlatformService = Depends(get_platform_service)):
    """Fetch telemetry metrics."""
    return await service.get_metrics()


@router.get(
    "/system",
    summary="Get System Metadata",
    description="Returns platform runtime metadata and active hardening modules.",
)
async def get_system_info(service: PlatformService = Depends(get_platform_service)):
    """Fetch system metadata."""
    return await service.get_system_info()


@router.get(
    "/platform/audit-logs",
    summary="List Audit Log Trail",
    description="Fetches compliance audit log events.",
)
async def list_audit_logs(
    event_type: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    skip: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    service: PlatformService = Depends(get_platform_service),
):
    """List audit log records."""
    items, total = await service.list_audit_logs(event_type=event_type, limit=limit, skip=skip)
    return {"total_count": total, "items": items}


@router.get(
    "/platform/feature-flags",
    summary="List Feature Flags",
    description="Returns list of active feature flags and beta toggles.",
)
async def list_feature_flags(
    current_user: User = Depends(get_current_user),
    service: PlatformService = Depends(get_platform_service),
):
    """List feature flags."""
    return await service.list_feature_flags()


@router.post(
    "/platform/feature-flags",
    summary="Update Feature Flag",
    description="Toggle or create a feature flag status.",
)
async def set_feature_flag(
    payload: FeatureFlagRequest,
    current_user: User = Depends(get_current_user),
    service: PlatformService = Depends(get_platform_service),
):
    """Toggle feature flag status."""
    return await service.set_feature_flag(flag_key=payload.flag_key, is_enabled=payload.is_enabled, name=payload.name)


@router.get(
    "/platform/traces",
    summary="List Distributed Request Traces",
    description="Fetches distributed tracing spans.",
)
async def list_traces(
    trace_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    skip: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    service: PlatformService = Depends(get_platform_service),
):
    """List distributed trace spans."""
    items, total = await service.list_traces(trace_id=trace_id, limit=limit, skip=skip)
    return {"total_count": total, "items": items}
