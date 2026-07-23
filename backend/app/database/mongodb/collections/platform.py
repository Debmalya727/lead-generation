"""
Beanie MongoDB Document collections for Phase 12.5: Enterprise Platform Hardening.

Collections:
- AuditLogDocument (audit_logs)
- FeatureFlagDocument (feature_flags)
- SystemMetricDocument (system_metrics)
- RequestTraceDocument (request_traces)
"""
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from beanie import Document, PydanticObjectId
from pydantic import BaseModel, Field


class AuditLogDocument(Document):
    """Document storing audit trail logs for all critical platform operations."""

    audit_id: str = Field(..., description="Unique audit event ID e.g. aud_123")
    event_type: str = Field(..., description="workflow_started | workflow_cancelled | tool_executed | policy_rejected | checkpoint_created | conversation_started | etc.")
    actor_id: Optional[str] = Field("System", description="User ID or Agent/System actor")
    
    correlation_id: Optional[str] = Field(None, description="Request correlation ID")
    resource_type: str = Field("workflow", description="workflow | tool | conversation | policy | system")
    resource_id: Optional[str] = None
    
    details: Dict[str, Any] = Field(default_factory=dict)
    ip_address: Optional[str] = None
    status: str = Field("success", description="success | failure | rejected")
    
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "audit_logs"
        indexes = [
            [("audit_id", 1)],
            [("event_type", 1), ("timestamp", -1)],
            [("actor_id", 1)],
            [("correlation_id", 1)],
        ]


class FeatureFlagDocument(Document):
    """Document managing dynamic feature flags and beta toggles."""

    flag_key: str = Field(..., description="Unique flag key e.g. 'voice_ai'")
    name: str = Field(..., description="Human-readable flag name")
    description: str = Field(..., description="Flag purpose & scope")
    
    is_enabled: bool = Field(False)
    environment: str = Field("production", description="production | staging | dev")
    allowed_roles: List[str] = Field(default_factory=list, description="Roles permitted when enabled")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "feature_flags"
        indexes = [
            [("flag_key", 1)],
            [("is_enabled", 1)],
        ]


class SystemMetricDocument(Document):
    """Document persisting aggregated system metrics and performance statistics."""

    metric_id: str = Field(..., description="Unique metric record ID")
    metric_name: str = Field(..., description="workflow_duration | tool_failure_rate | memory_usage_mb | etc.")
    value: float = Field(..., description="Metric numeric value")
    
    unit: str = Field("ms", description="ms | count | percent | MB")
    dimensions: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "system_metrics"
        indexes = [
            [("metric_name", 1), ("timestamp", -1)],
            [("metric_id", 1)],
        ]


class RequestTraceDocument(Document):
    """Document storing distributed traces and span hierarchies."""

    trace_id: str = Field(..., description="Global distributed trace ID")
    span_id: str = Field(..., description="Individual span ID")
    parent_span_id: Optional[str] = None
    
    name: str = Field(..., description="Span name e.g. 'WorkflowEngine.execute_step'")
    component: str = Field("gateway", description="gateway | workflow | agent | tool | rag")
    
    duration_ms: float = Field(0.0)
    status: str = Field("ok", description="ok | error")
    attributes: Dict[str, Any] = Field(default_factory=dict)
    
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "request_traces"
        indexes = [
            [("trace_id", 1)],
            [("span_id", 1)],
            [("component", 1), ("timestamp", -1)],
        ]
