"""
Extended Beanie MongoDB Document collections for Phase 12.7B Enterprise AI Gateway Extension.
Adds 12 new collections: policies, capabilities, sessions, prompt registry,
benchmarks, guardrail logs, evaluations, memory, and workflow artifacts.
"""
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from beanie import Document
from pydantic import Field


# ─── Section 1: AI Policy Engine ───

class AIPolicyDocument(Document):
    """Stores declarative routing policies mapping capabilities to provider/model."""

    policy_id: str = Field(..., description="Unique policy identifier")
    name: str = Field(..., description="Human readable policy name")
    description: Optional[str] = None

    capability: str = Field(..., description="Capability this policy handles: reasoning | vision | embedding | etc.")
    provider: str = Field(..., description="Target provider: gemini | openai | claude | etc.")
    model: str = Field(..., description="Target model identifier")

    priority: int = Field(100, description="Lower = higher priority. Policy with lowest priority wins.")
    is_active: bool = Field(True)

    # Conditions that trigger this policy
    conditions: Dict[str, Any] = Field(default_factory=dict, description="e.g. {org_id: 'acme', user_tier: 'enterprise'}")

    # Overrides at org level
    org_id: Optional[str] = Field(None, description="If set, policy applies only to this organization")

    created_by: str = Field("system")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "ai_policies"
        indexes = [
            [("capability", 1), ("priority", 1)],
            [("is_active", 1)],
            [("org_id", 1)],
        ]


class CapabilityRegistryDocument(Document):
    """Registry of all known AI capabilities with metadata."""

    capability_id: str = Field(..., description="Unique capability identifier: reasoning | vision | etc.")
    name: str = Field(..., description="Human readable capability name")
    description: str = Field("", description="Capability description")

    default_provider: str = Field("gemini", description="Default provider for this capability")
    default_model: str = Field("gemini-1.5-flash", description="Default model for this capability")

    is_active: bool = Field(True)
    tags: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "capability_registry"
        indexes = [
            [("capability_id", 1)],
            [("is_active", 1)],
        ]


# ─── Section 2: AI Session Manager ───

class AISessionDocument(Document):
    """Tracks per-request AI gateway sessions with full telemetry."""

    session_id: str = Field(..., description="Unique session identifier")
    correlation_id: Optional[str] = None

    conversation_id: Optional[str] = None
    workflow_id: Optional[str] = None
    user_id: Optional[str] = None
    org_id: Optional[str] = None
    agent_id: Optional[str] = None

    capability: Optional[str] = Field(None, description="Resolved capability name")
    provider: str = Field("", description="Provider used")
    model: str = Field("", description="Model used")

    # Metrics
    prompt_tokens: int = Field(0)
    completion_tokens: int = Field(0)
    total_tokens: int = Field(0)
    estimated_cost: float = Field(0.0)
    latency_ms: float = Field(0.0)
    retry_count: int = Field(0)
    fallback_count: int = Field(0)

    # State
    streaming: bool = Field(False)
    cached: bool = Field(False)
    status: str = Field("active", description="active | completed | failed | expired")

    # Prompt history (last N)
    prompt_history: List[str] = Field(default_factory=list, description="Recent prompt hashes for context window tracking")
    context_window_used: int = Field(0, description="Estimated tokens used in context window")
    cache_references: List[str] = Field(default_factory=list, description="Cache key references")

    # Guardrail results
    guardrail_passed: Optional[bool] = None
    guardrail_flags: List[str] = Field(default_factory=list)

    # Policy
    policy_id: Optional[str] = None
    selected_policy: Optional[str] = None

    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None

    class Settings:
        name = "ai_sessions"
        indexes = [
            [("session_id", 1)],
            [("correlation_id", 1)],
            [("user_id", 1)],
            [("org_id", 1)],
            [("status", 1)],
            [("started_at", -1)],
        ]


# ─── Section 3: Prompt Registry ───

class PromptRegistryDocument(Document):
    """Lifecycle-managed prompt registry with approval workflow."""

    registry_id: str = Field(..., description="Unique registry entry ID")
    name: str = Field(..., description="Prompt name")
    category: str = Field("conversation", description="conversation | research | outreach | analysis | system")
    tags: List[str] = Field(default_factory=list)
    description: Optional[str] = None

    system_prompt: Optional[str] = None
    user_prompt_template: str = Field(...)
    variables: List[str] = Field(default_factory=list)

    # Lifecycle
    status: str = Field("draft", description="draft | review | approved | production | deprecated | archived")
    version: int = Field(1)
    current_version_id: Optional[str] = None

    # Ownership & audit
    created_by: str = Field("system")
    reviewed_by: Optional[str] = None
    approved_by: Optional[str] = None
    promoted_to_production_by: Optional[str] = None

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    approved_at: Optional[datetime] = None

    class Settings:
        name = "prompt_registry"
        indexes = [
            [("registry_id", 1)],
            [("status", 1)],
            [("category", 1)],
            [("tags", 1)],
        ]


class PromptApprovalDocument(Document):
    """Approval workflow events for prompt registry entries."""

    approval_id: str = Field(..., description="Unique approval event ID")
    registry_id: str = Field(..., description="Target prompt registry entry ID")

    action: str = Field(..., description="submit_review | approve | reject | promote | deprecate | archive | rollback")
    performed_by: str = Field("system")
    comments: Optional[str] = None

    from_status: str = Field(..., description="Status before action")
    to_status: str = Field(..., description="Status after action")

    version: int = Field(1)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "prompt_approvals"
        indexes = [
            [("registry_id", 1), ("timestamp", -1)],
            [("action", 1)],
        ]


# ─── Section 4: Model Benchmark Registry ───

class ModelBenchmarkDocument(Document):
    """Benchmark suite definition with test prompts and scoring dimensions."""

    benchmark_id: str = Field(..., description="Unique benchmark suite ID")
    name: str = Field(..., description="Benchmark suite name")
    description: Optional[str] = None

    test_prompts: List[str] = Field(default_factory=list, description="List of test prompt strings")
    target_providers: List[str] = Field(default_factory=list, description="List of providers to benchmark")
    target_models: List[str] = Field(default_factory=list, description="List of specific models to benchmark")

    metrics: List[str] = Field(
        default_factory=lambda: ["latency_ms", "tokens", "cost", "json_validity", "quality_score"],
        description="Metrics to collect"
    )

    is_active: bool = Field(True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "model_benchmarks"
        indexes = [
            [("benchmark_id", 1)],
            [("is_active", 1)],
        ]


class BenchmarkHistoryDocument(Document):
    """Historical results from benchmark runs."""

    run_id: str = Field(..., description="Unique benchmark run identifier")
    benchmark_id: str = Field(..., description="Associated benchmark suite")

    provider: str = Field(...)
    model: str = Field(...)

    prompt: str = Field(..., description="Test prompt used")
    response_text: str = Field(..., description="Raw response")

    latency_ms: float = Field(0.0)
    prompt_tokens: int = Field(0)
    completion_tokens: int = Field(0)
    estimated_cost: float = Field(0.0)

    json_valid: bool = Field(False)
    quality_score: float = Field(0.0, description="Heuristic quality score 0.0-1.0")
    hallucination_score: float = Field(0.0, description="Risk score 0.0-1.0 (lower is better)")

    run_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "benchmark_history"
        indexes = [
            [("benchmark_id", 1), ("run_at", -1)],
            [("provider", 1), ("model", 1)],
        ]


# ─── Section 5: AI Guardrails ───

class GuardrailLogDocument(Document):
    """Records guardrail validation results for every AI response."""

    log_id: str = Field(..., description="Unique guardrail log identifier")
    correlation_id: str = Field(..., description="Associated AI request correlation ID")
    session_id: Optional[str] = None

    passed: bool = Field(..., description="True if all guardrails passed")

    # Individual validator results
    json_valid: Optional[bool] = None
    pii_detected: bool = Field(False)
    profanity_detected: bool = Field(False)
    length_valid: Optional[bool] = None
    citations_valid: Optional[bool] = None
    hallucination_score: float = Field(0.0)
    confidence_score: float = Field(1.0)
    schema_valid: Optional[bool] = None

    flags: List[str] = Field(default_factory=list, description="List of validation flags triggered")
    details: Dict[str, Any] = Field(default_factory=dict, description="Detailed validator output")

    response_length: int = Field(0)
    validated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "guardrail_logs"
        indexes = [
            [("correlation_id", 1)],
            [("session_id", 1)],
            [("passed", 1)],
            [("validated_at", -1)],
        ]


# ─── Section 6: AI Evaluation Framework ───

class EvaluationRunDocument(Document):
    """Metadata for an AI evaluation run across multiple providers."""

    run_id: str = Field(..., description="Unique evaluation run ID")
    name: str = Field(..., description="Evaluation run name")

    test_prompt: str = Field(..., description="Prompt used for comparison")
    system_prompt: Optional[str] = None

    target_providers: List[str] = Field(default_factory=list)
    target_models: List[str] = Field(default_factory=list)

    status: str = Field("pending", description="pending | running | completed | failed")
    initiated_by: str = Field("system")

    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None

    class Settings:
        name = "evaluation_runs"
        indexes = [
            [("run_id", 1)],
            [("status", 1)],
            [("started_at", -1)],
        ]


class EvaluationScoreDocument(Document):
    """Per-provider/model scores within an evaluation run."""

    score_id: str = Field(..., description="Unique score record ID")
    run_id: str = Field(..., description="Parent evaluation run ID")

    provider: str = Field(...)
    model: str = Field(...)
    response_text: str = Field(...)

    latency_ms: float = Field(0.0)
    prompt_tokens: int = Field(0)
    completion_tokens: int = Field(0)
    estimated_cost: float = Field(0.0)

    json_valid: bool = Field(False)
    quality_score: float = Field(0.0)
    hallucination_score: float = Field(0.0)
    guardrail_passed: bool = Field(True)

    overall_score: float = Field(0.0, description="Composite normalized score 0.0-1.0")
    rank: int = Field(0, description="Rank within this run (1 = best)")

    scored_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "evaluation_scores"
        indexes = [
            [("run_id", 1), ("overall_score", -1)],
            [("provider", 1), ("model", 1)],
        ]


# ─── Section 7: AI Memory Manager ───

class AIMemoryDocument(Document):
    """Stores memory records linking prompts to cache keys and embedding IDs."""

    memory_id: str = Field(..., description="Unique memory record ID")

    prompt_hash: str = Field(..., description="SHA-256 hash of original prompt")
    prompt_version: Optional[str] = None
    embedding_ids: List[str] = Field(default_factory=list, description="Vector embedding document IDs")
    cache_keys: List[str] = Field(default_factory=list, description="Redis or MongoDB cache key references")

    # Context links
    user_id: Optional[str] = None
    org_id: Optional[str] = None
    workflow_id: Optional[str] = None
    conversation_id: Optional[str] = None
    session_id: Optional[str] = None

    # Summary reference
    summary_id: Optional[str] = None

    tags: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None

    class Settings:
        name = "ai_memory"
        indexes = [
            [("prompt_hash", 1)],
            [("user_id", 1)],
            [("workflow_id", 1)],
            [("session_id", 1)],
            [("created_at", -1)],
        ]


class WorkflowArtifactDocument(Document):
    """Structured workflow outputs and generated assets stored in AI memory."""

    artifact_id: str = Field(..., description="Unique artifact ID")
    artifact_type: str = Field(..., description="report | summary | outreach | lead_data | research | analysis | json_output")

    workflow_id: Optional[str] = None
    session_id: Optional[str] = None
    conversation_id: Optional[str] = None
    agent_id: Optional[str] = None

    content: Dict[str, Any] = Field(default_factory=dict, description="Structured artifact payload")
    content_hash: str = Field("", description="SHA-256 hash of content for deduplication")

    source_prompt_hash: Optional[str] = None
    evaluation_run_id: Optional[str] = None

    tags: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "workflow_artifacts"
        indexes = [
            [("artifact_id", 1)],
            [("workflow_id", 1)],
            [("artifact_type", 1)],
            [("content_hash", 1)],
            [("created_at", -1)],
        ]
