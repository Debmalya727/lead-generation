"""
Beanie MongoDB Document collections for Phase 12.7C: Enterprise AI Orchestration Platform.
Adds 10 collections: ai_workflows, ai_workflow_runs, ai_workflow_nodes,
ai_workflow_edges, ai_execution_plans, ai_pipeline_templates, ai_queue,
ai_dead_letter_queue, provider_health, resource_metrics.
"""
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from beanie import Document
from pydantic import Field


class AIWorkflowDocument(Document):
    """Stores workflow definitions."""

    workflow_id: str = Field(..., description="Unique workflow identifier")
    name: str = Field(..., description="Workflow name")
    description: Optional[str] = None
    category: str = Field("custom", description="research | discovery | scoring | outreach | report | rag | custom")

    version: int = Field(1)
    status: str = Field("active", description="active | draft | deprecated | archived")

    initial_node_id: str = Field(..., description="ID of entry node")
    nodes: List[Dict[str, Any]] = Field(default_factory=list, description="Node definitions payload")
    edges: List[Dict[str, Any]] = Field(default_factory=list, description="Edge connection definitions payload")

    metadata: Dict[str, Any] = Field(default_factory=dict)

    created_by: str = Field("system")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "ai_workflows"
        indexes = [
            [("workflow_id", 1)],
            [("category", 1)],
            [("status", 1)],
        ]


class AIWorkflowRunDocument(Document):
    """Tracks execution instances of an AI workflow."""

    run_id: str = Field(..., description="Unique execution run identifier")
    workflow_id: str = Field(..., description="Target workflow ID")
    correlation_id: str = Field(..., description="Tracing correlation ID")

    session_id: Optional[str] = None
    user_id: Optional[str] = None
    org_id: Optional[str] = None
    priority: str = Field("Interactive", description="Critical | Enterprise | Realtime | Interactive | Background | Low")

    status: str = Field("pending", description="pending | running | paused | completed | failed | cancelled")

    inputs: Dict[str, Any] = Field(default_factory=dict)
    outputs: Dict[str, Any] = Field(default_factory=dict)

    current_node_id: Optional[str] = None
    completed_node_ids: List[str] = Field(default_factory=list)
    failed_node_ids: List[str] = Field(default_factory=list)
    node_results: Dict[str, Any] = Field(default_factory=dict)

    total_latency_ms: float = Field(0.0)
    total_tokens: int = Field(0)
    total_cost: float = Field(0.0)

    error_message: Optional[str] = None
    checkpoint_state: Optional[Dict[str, Any]] = None

    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None

    class Settings:
        name = "ai_workflow_runs"
        indexes = [
            [("run_id", 1)],
            [("workflow_id", 1)],
            [("correlation_id", 1)],
            [("status", 1)],
            [("started_at", -1)],
        ]


class AIWorkflowNodeDocument(Document):
    """Persists node configurations."""

    node_id: str = Field(..., description="Unique node ID within a workflow")
    workflow_id: str = Field(...)
    node_type: str = Field(..., description="PromptNode | ReasoningNode | GenerationNode | ToolNode | etc.")
    name: str = Field(...)

    capability: Optional[str] = None
    config: Dict[str, Any] = Field(default_factory=dict)

    timeout_seconds: float = Field(30.0)
    max_retries: int = Field(3)
    fallback_node_id: Optional[str] = None

    class Settings:
        name = "ai_workflow_nodes"
        indexes = [
            [("workflow_id", 1), ("node_id", 1)],
            [("node_type", 1)],
        ]


class AIWorkflowEdgeDocument(Document):
    """Persists DAG edge connections between nodes."""

    edge_id: str = Field(..., description="Unique edge identifier")
    workflow_id: str = Field(...)
    from_node_id: str = Field(...)
    to_node_id: str = Field(...)

    condition_expression: Optional[str] = Field(None, description="Optional condition rule expression")

    class Settings:
        name = "ai_workflow_edges"
        indexes = [
            [("workflow_id", 1)],
            [("from_node_id", 1), ("to_node_id", 1)],
        ]


class AIExecutionPlanDocument(Document):
    """Stores decomposed execution plans."""

    plan_id: str = Field(..., description="Unique plan identifier")
    workflow_id: Optional[str] = None
    prompt: str = Field(...)

    required_capabilities: List[str] = Field(default_factory=list)
    execution_order: List[str] = Field(default_factory=list)
    strategy: str = Field("sequential", description="sequential | parallel | cost_optimized | latency_optimized | fallback_heavy")

    node_plans: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "ai_execution_plans"
        indexes = [
            [("plan_id", 1)],
            [("created_at", -1)],
        ]


class AIPipelineTemplateDocument(Document):
    """Registry of built-in pipeline templates."""

    template_id: str = Field(..., description="Unique template identifier")
    name: str = Field(..., description="Template name")
    description: str = Field(...)
    category: str = Field("system")

    workflow_spec: Dict[str, Any] = Field(default_factory=dict)
    is_built_in: bool = Field(True)

    class Settings:
        name = "ai_pipeline_templates"
        indexes = [
            [("template_id", 1)],
            [("category", 1)],
        ]


class AIQueueDocument(Document):
    """Priority task queue item for AI orchestration."""

    queue_id: str = Field(..., description="Unique queue item ID")
    workflow_run_id: str = Field(...)
    node_id: str = Field(...)

    priority: str = Field("Interactive", description="Critical | Enterprise | Realtime | Interactive | Background | Low")
    priority_level: int = Field(3, description="1=Critical, 2=Enterprise, 3=Realtime, 4=Interactive, 5=Background, 6=Low")

    payload: Dict[str, Any] = Field(default_factory=dict)
    status: str = Field("queued", description="queued | processing | completed | failed | dead_letter")

    retry_count: int = Field(0)
    max_retries: int = Field(3)
    error_log: List[str] = Field(default_factory=list)

    enqueued_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    processed_at: Optional[datetime] = None

    class Settings:
        name = "ai_queue"
        indexes = [
            [("queue_id", 1)],
            [("status", 1), ("priority_level", 1)],
            [("enqueued_at", 1)],
        ]


class AIDeadLetterQueueDocument(Document):
    """Dead letter queue for permanently failed workflow tasks."""

    dlq_id: str = Field(..., description="Unique DLQ item ID")
    original_queue_id: str = Field(...)
    workflow_run_id: str = Field(...)
    node_id: str = Field(...)

    payload: Dict[str, Any] = Field(default_factory=dict)
    failure_reason: str = Field(...)
    failed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    retried: bool = Field(False)
    retried_at: Optional[datetime] = None

    class Settings:
        name = "ai_dead_letter_queue"
        indexes = [
            [("dlq_id", 1)],
            [("failed_at", -1)],
        ]


class ProviderHealthDocument(Document):
    """Tracks provider circuit breaker states and health statistics."""

    provider: str = Field(..., description="Provider identifier name e.g. 'gemini'")
    state: str = Field("CLOSED", description="CLOSED | OPEN | HALF_OPEN")

    consecutive_failures: int = Field(0)
    total_failures: int = Field(0)
    total_successes: int = Field(0)

    last_failure_at: Optional[datetime] = None
    last_success_at: Optional[datetime] = None
    cooldown_until: Optional[datetime] = None

    avg_latency_ms: float = Field(0.0)
    error_rate: float = Field(0.0)

    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "provider_health"
        indexes = [
            [("provider", 1)],
            [("state", 1)],
        ]


class ResourceMetricsDocument(Document):
    """Aggregated latency/cost/throughput metrics per model/provider."""

    provider: str = Field(...)
    model: str = Field(...)

    total_requests: int = Field(0)
    successful_requests: int = Field(0)
    failed_requests: int = Field(0)

    avg_latency_ms: float = Field(0.0)
    p95_latency_ms: float = Field(0.0)

    total_tokens: int = Field(0)
    total_cost: float = Field(0.0)

    success_rate: float = Field(1.0)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "resource_metrics"
        indexes = [
            [("provider", 1), ("model", 1)],
        ]
