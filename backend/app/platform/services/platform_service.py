"""
PlatformService for Phase 12.5: Enterprise Platform Hardening.
"""
import logging
from typing import Dict, List, Optional, Any, Tuple

from app.platform.gateway.interaction_gateway import InteractionGateway
from app.platform.health.health_service import HealthService
from app.platform.feature_flags.feature_flag_manager import FeatureFlagManager
from app.platform.audit.audit_logger import AuditLogger
from app.platform.tracing.trace_manager import TraceManager
from app.database.mongodb.collections.platform import (
    AuditLogDocument,
    FeatureFlagDocument,
    RequestTraceDocument,
)

logger = logging.getLogger("backend.platform.service")


class PlatformService:
    """Service orchestrating platform hardening, health, metrics, flags, audit logs, and traces."""

    def __init__(self):
        self.gateway = InteractionGateway()
        self.health_service = HealthService()
        self.feature_flag_manager = FeatureFlagManager()
        self.audit_logger = AuditLogger()
        self.trace_manager = TraceManager()

    async def get_health(self) -> Dict[str, Any]:
        """Fetch system health status."""
        return await self.health_service.get_health_status()

    async def get_metrics(self) -> Dict[str, Any]:
        """Fetch system metrics summary."""
        return await self.health_service.get_metrics_summary()

    async def get_system_info(self) -> Dict[str, Any]:
        """Fetch system platform information."""
        return await self.health_service.get_system_info()

    async def list_audit_logs(self, event_type: Optional[str] = None, limit: int = 50, skip: int = 0) -> Tuple[List[AuditLogDocument], int]:
        """List audit logs."""
        return await self.audit_logger.list_audit_logs(event_type=event_type, limit=limit, skip=skip)

    async def list_feature_flags(self) -> List[Dict[str, Any]]:
        """List feature flags."""
        return await self.feature_flag_manager.list_flags()

    async def set_feature_flag(self, flag_key: str, is_enabled: bool, name: Optional[str] = None) -> FeatureFlagDocument:
        """Set feature flag status."""
        return await self.feature_flag_manager.set_flag(flag_key, is_enabled, name=name)

    async def list_traces(self, trace_id: Optional[str] = None, limit: int = 50, skip: int = 0) -> Tuple[List[RequestTraceDocument], int]:
        """List distributed traces."""
        return await self.trace_manager.list_traces(trace_id=trace_id, limit=limit, skip=skip)
