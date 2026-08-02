"""
Beanie MongoDB Document collections for Phase 12.7A: Enterprise AI Gateway.
"""
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from beanie import Document
from pydantic import Field


class AIRequestDocument(Document):
    """Logs incoming requests routed to the AI Gateway."""

    correlation_id: str = Field(..., description="Distributed tracing correlation ID")
    user_id: Optional[str] = None
    org_id: Optional[str] = None
    
    conversation_id: Optional[str] = None
    workflow_id: Optional[str] = None
    agent_id: Optional[str] = None
    plugin_id: Optional[str] = None
    
    prompt: str = Field(..., description="Prompt payload text")
    system_prompt: Optional[str] = None
    
    provider: str = Field(..., description="Requested AI provider name")
    model: str = Field(..., description="Requested model identifier")
    
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "ai_requests"
        indexes = [
            [("correlation_id", 1)],
            [("user_id", 1)],
            [("org_id", 1)],
            [("timestamp", -1)],
        ]


class AIResponseDocument(Document):
    """Logs completion/generation responses from the AI Gateway."""

    correlation_id: str = Field(..., description="Associated request tracing correlation ID")
    response_text: str = Field(..., description="Full response text/json payload")
    
    prompt_tokens: int = Field(0)
    completion_tokens: int = Field(0)
    total_tokens: int = Field(0)
    estimated_cost: float = Field(0.0)
    
    latency_ms: float = Field(0.0)
    provider_used: str = Field(..., description="Actual provider used (may differ if fell back)")
    model_used: str = Field(..., description="Actual model used")
    
    retry_count: int = Field(0)
    fallback_count: int = Field(0)
    cached: bool = Field(False)
    
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "ai_responses"
        indexes = [
            [("correlation_id", 1)],
            [("provider_used", 1)],
            [("timestamp", -1)],
        ]


class ModelRegistryDocument(Document):
    """Persists model pricing, context length, capabilities, and availability."""

    provider: str = Field(..., description="openai | gemini | claude | deepseek | etc.")
    model_id: str = Field(..., description="Identifier name e.g. 'gemini-1.5-flash'")
    name: str = Field(..., description="Friendly name")
    
    capabilities: List[str] = Field(default_factory=list, description="vision | tools | structured | streaming")
    context_window: int = Field(128000)
    
    input_token_price: float = Field(0.0, description="Cost in USD per 1M input tokens")
    output_token_price: float = Field(0.0, description="Cost in USD per 1M output tokens")
    
    is_active: bool = Field(True)
    is_embedding: bool = Field(False)

    class Settings:
        name = "model_registry"
        indexes = [
            [("provider", 1), ("model_id", 1)],
            [("is_active", 1)],
        ]


class ProviderRegistryDocument(Document):
    """Tracks active LLM and embedding providers and connection profiles."""

    provider: str = Field(..., description="gemini | openai | claude | openrouter | ollama | groq | deepseek")
    base_url: str = Field(..., description="API base endpoint url")
    max_retries: int = Field(3)
    timeout_seconds: int = Field(30)
    is_active: bool = Field(True)

    class Settings:
        name = "provider_registry"
        indexes = [
            [("provider", 1)],
            [("is_active", 1)],
        ]


class PromptTemplateDocument(Document):
    """Tracks prompt templates, variables, tags, and lifecycle status across categories."""

    template_id: str = Field(..., description="Unique prompt template ID")
    name: str = Field(..., description="Prompt template name")
    category: str = Field("conversation", description="conversation | research | outreach | score | summary | reasoning | coding | custom")
    tags: List[str] = Field(default_factory=list, description="Searchable tags")
    
    system_prompt_template: Optional[str] = None
    user_prompt_template: str = Field(...)
    
    variables: List[str] = Field(default_factory=list, description="Required variable placeholder keys")
    current_version: int = Field(1)
    version_tag: str = Field("v1.0.0")
    status: str = Field("DRAFT", description="DRAFT | IN_REVIEW | APPROVED | REJECTED | PUBLISHED | ARCHIVED")
    published_version: Optional[int] = None
    
    hit_count: int = Field(0)
    average_rating: float = Field(5.0)
    
    created_by: str = Field("System")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "prompt_templates"
        indexes = [
            [("template_id", 1)],
            [("category", 1)],
            [("status", 1)],
        ]


class PromptVersionDocument(Document):
    """Tracks historical prompt version revisions and structural diff logs."""

    template_id: str = Field(..., description="Associated prompt template ID")
    version: int = Field(1, description="Sequential version index")
    version_tag: str = Field("v1.0.0", description="Semantic version string e.g. v1.0.0")
    
    system_prompt: Optional[str] = None
    user_prompt: str = Field(...)
    variables: List[str] = Field(default_factory=list)
    
    changes_description: Optional[str] = None
    author: str = Field("System")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "prompt_versions"
        indexes = [
            [("template_id", 1), ("version", -1)],
        ]


class PromptABTestDocument(Document):
    """Tracks A/B testing experiments comparing prompt version variants."""

    test_id: str = Field(..., description="Unique A/B experiment test ID")
    template_id: str = Field(..., description="Associated prompt template ID")
    name: str = Field(..., description="Experiment name")
    
    variant_a_version: int = Field(...)
    variant_b_version: int = Field(...)
    traffic_split_percent: float = Field(50.0)
    
    variant_a_hits: int = Field(0)
    variant_b_hits: int = Field(0)
    variant_a_score: float = Field(0.0)
    variant_b_score: float = Field(0.0)
    
    status: str = Field("ACTIVE", description="ACTIVE | PAUSED | COMPLETED")
    winning_variant: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "prompt_ab_tests"
        indexes = [
            [("test_id", 1)],
            [("template_id", 1)],
            [("status", 1)],
        ]


class ToolRegistryDocument(Document):
    """Persists registered tools, JSON schema signatures, permission scopes, and execution metrics."""

    name: str = Field(..., description="Unique tool identifier name")
    description: str = Field(..., description="Human and LLM readable tool description")
    category: str = Field("custom", description="crm | knowledge | calendar | email | voice | search | database | analytics | workflow")
    version: str = Field("v1.0.0", description="Semantic tool version string")
    
    permission_scope: str = Field("read", description="Required permission scope e.g. crm:read, email:send")
    parameters_schema: Dict[str, Any] = Field(default_factory=dict, description="JSON Schema specification of parameters")
    
    execution_count: int = Field(0)
    error_count: int = Field(0)
    total_duration_ms: float = Field(0.0)
    is_active: bool = Field(True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "tool_registry"
        indexes = [
            [("name", 1)],
            [("category", 1)],
            [("is_active", 1)],
        ]


class ToolExecutionLogDocument(Document):
    """Audits sandboxed tool execution calls, parameters, permissions, and results."""

    correlation_id: str = Field(..., description="Tracing correlation ID")
    tool_name: str = Field(..., description="Executed tool identifier name")
    
    user_id: Optional[str] = None
    granted_scopes: List[str] = Field(default_factory=list)
    
    input_args: Dict[str, Any] = Field(default_factory=dict)
    output_result: Optional[Any] = None
    status: str = Field("SUCCESS", description="SUCCESS | FAILED | PERMISSION_DENIED | VALIDATION_ERROR | TIMEOUT")
    error_message: Optional[str] = None
    
    duration_ms: float = Field(0.0)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "tool_execution_logs"
        indexes = [
            [("correlation_id", 1)],
            [("tool_name", 1)],
            [("status", 1)],
            [("timestamp", -1)],
        ]


class EnterpriseAgentDocument(Document):
    """Persists registered AI Agent personas, capabilities, permissions, tools, and telemetry."""

    agent_id: str = Field(..., description="Unique agent identifier name e.g. sdr_agent")
    name: str = Field(..., description="Human friendly agent name")
    role: str = Field(..., description="Agent role title e.g. SDR Representative")
    description: str = Field(...)
    
    system_prompt: str = Field(...)
    assigned_tools: List[str] = Field(default_factory=list, description="Tools assigned from ToolRegistry")
    permission_scopes: List[str] = Field(default_factory=list, description="Granted permission scopes e.g. ['crm:*', 'email:send']")
    
    provider: str = Field("gemini")
    model: str = Field("gemini-1.5-flash")
    status: str = Field("IDLE", description="IDLE | PLANNING | EXECUTING | REFLECTING | COMPLETED | FAILED")
    
    total_runs: int = Field(0)
    successful_runs: int = Field(0)
    failed_runs: int = Field(0)
    total_tokens: int = Field(0)
    total_cost_usd: float = Field(0.0)
    
    is_marketplace: bool = Field(False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "enterprise_agents"
        indexes = [
            [("agent_id", 1)],
            [("role", 1)],
            [("is_marketplace", 1)],
        ]


class AgentPlanDocument(Document):
    """Tracks task decomposition plans, sub-tasks, reflection logs, and self-evaluation scores."""

    plan_id: str = Field(..., description="Unique execution plan ID")
    agent_id: str = Field(...)
    goal: str = Field(...)
    
    sub_tasks: List[Dict[str, Any]] = Field(default_factory=list, description="Decomposed sub-task steps")
    reflections: List[Dict[str, Any]] = Field(default_factory=list, description="Reflection log step notes")
    self_evaluation_score: float = Field(1.0, description="Quality score 0.0 - 1.0")
    
    status: str = Field("COMPLETED", description="PLANNING | EXECUTING | REFLECTING | COMPLETED | FAILED")
    output_result: Optional[Any] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "agent_plans"
        indexes = [
            [("plan_id", 1)],
            [("agent_id", 1)],
            [("status", 1)],
        ]


class AgentTeamExecutionDocument(Document):
    """Tracks multi-agent team collaboration, delegation messages, and consensus results."""

    team_execution_id: str = Field(...)
    team_name: str = Field(...)
    participating_agents: List[str] = Field(default_factory=list)
    
    goal: str = Field(...)
    delegations: List[Dict[str, Any]] = Field(default_factory=list)
    consensus_result: Optional[Dict[str, Any]] = None
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "agent_team_executions"
        indexes = [
            [("team_execution_id", 1)],
        ]


class RequestTraceDocument(Document):
    """Persists distributed OpenTelemetry request traces, span telemetry, and correlation IDs."""

    trace_id: str = Field(..., description="OpenTelemetry trace ID")
    request_id: str = Field(..., description="Unique HTTP request ID")
    correlation_id: str = Field(..., description="Distributed tracing correlation ID")
    
    endpoint: str = Field(...)
    method: str = Field("POST")
    user_id: Optional[str] = None
    
    duration_ms: float = Field(...)
    status_code: int = Field(200)
    spans: List[Dict[str, Any]] = Field(default_factory=list, description="Nested span telemetry traces")
    
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "request_traces"
        indexes = [
            [("trace_id", 1)],
            [("correlation_id", 1)],
            [("request_id", 1)],
            [("timestamp", -1)],
        ]


class AnomalyAlertDocument(Document):
    """Audits statistical latency anomalies, error spikes, budget breaches, and SLA alerts."""

    alert_id: str = Field(..., description="Unique alert identifier")
    alert_type: str = Field(..., description="LATENCY_ANOMALY | ERROR_SPIKE | BUDGET_OVERRUN | SLA_BREACH | CIRCUIT_BREAKER")
    severity: str = Field("WARNING", description="INFO | WARNING | CRITICAL")
    
    source_component: str = Field(...)
    message: str = Field(...)
    metrics_snapshot: Dict[str, Any] = Field(default_factory=dict)
    
    status: str = Field("ACTIVE", description="ACTIVE | ACKNOWLEDGED | RESOLVED")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "anomaly_alerts"
        indexes = [
            [("alert_id", 1)],
            [("alert_type", 1)],
            [("severity", 1)],
            [("status", 1)],
        ]


class SecurityAuditEventDocument(Document):
    """Persists security audit events, WAF blocks, prompt injection attempts, and key rotation logs."""

    event_id: str = Field(..., description="Unique security event ID")
    event_type: str = Field(..., description="WAF_BLOCK | PROMPT_INJECTION | MALWARE_DETECTED | KEY_ROTATION | AUTH_FAILURE | ENCRYPTION_EVENT")
    severity: str = Field("WARNING", description="INFO | WARNING | HIGH | CRITICAL")
    
    source_ip: Optional[str] = None
    user_id: Optional[str] = None
    endpoint: Optional[str] = None
    
    description: str = Field(...)
    payload_snapshot: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "security_audit_events"
        indexes = [
            [("event_id", 1)],
            [("event_type", 1)],
            [("severity", 1)],
            [("timestamp", -1)],
        ]


class EmailTemplateDocument(Document):
    """Persists HTML and MJML email outreach templates with variable tags."""

    template_id: str = Field(..., description="Unique email template ID")
    name: str = Field(...)
    subject: str = Field(...)
    
    html_content: str = Field(...)
    mjml_content: Optional[str] = None
    variables: List[str] = Field(default_factory=list)
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "email_templates"
        indexes = [
            [("template_id", 1)],
        ]


class EmailCampaignDocument(Document):
    """Tracks email campaign batch dispatches, delivery, opens, clicks, and bounces."""

    campaign_id: str = Field(..., description="Unique campaign ID")
    name: str = Field(...)
    template_id: str = Field(...)
    
    recipients_count: int = Field(0)
    sent_count: int = Field(0)
    delivered_count: int = Field(0)
    opened_count: int = Field(0)
    clicked_count: int = Field(0)
    bounced_count: int = Field(0)
    complained_count: int = Field(0)
    
    status: str = Field("DRAFT", description="DRAFT | SCHEDULED | RUNNING | COMPLETED | FAILED")
    scheduled_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "email_campaigns"
        indexes = [
            [("campaign_id", 1)],
            [("status", 1)],
        ]


class EmailWebhookEventDocument(Document):
    """Audits incoming Resend webhook payload events (sent, delivered, opened, clicked, bounced, complained)."""

    event_id: str = Field(...)
    resend_email_id: str = Field(...)
    event_type: str = Field(...)  # email.sent | email.delivered | email.opened | email.clicked | email.bounced | email.complained
    
    recipient_email: str = Field(...)
    campaign_id: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)
    
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "email_webhook_events"
        indexes = [
            [("event_id", 1)],
            [("resend_email_id", 1)],
            [("event_type", 1)],
            [("recipient_email", 1)],
        ]


class PlaygroundSessionDocument(Document):
    """Persists AI Playground prompt sessions, provider comparisons, and hyperparameter snapshots."""

    session_id: str = Field(..., description="Unique playground session ID")
    title: str = Field(...)
    user_id: Optional[str] = None
    
    system_prompt: Optional[str] = None
    prompt: str = Field(...)
    hyperparameters: Dict[str, Any] = Field(default_factory=dict)
    
    runs: List[Dict[str, Any]] = Field(default_factory=list, description="Provider/model execution outputs and telemetry")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "playground_sessions"
        indexes = [
            [("session_id", 1)],
            [("user_id", 1)],
            [("created_at", -1)],
        ]


class TokenUsageDocument(Document):
    """Accumulates system token usage across organizational divisions."""

    identifier_type: str = Field(..., description="user | organization | workflow | conversation | agent | plugin")
    identifier_id: str = Field(..., description="Specific resource database ID")
    
    prompt_tokens: int = Field(0)
    completion_tokens: int = Field(0)
    embedding_tokens: int = Field(0)
    total_tokens: int = Field(0)
    
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "token_usage"
        indexes = [
            [("identifier_type", 1), ("identifier_id", 1)],
            [("updated_at", -1)],
        ]


class CostUsageDocument(Document):
    """Tracks cost attribution across users, workflows, and campaigns."""

    identifier_type: str = Field(..., description="user | organization | workflow | conversation | agent | plugin")
    identifier_id: str = Field(..., description="Specific resource database ID")
    
    estimated_cost: float = Field(0.0)
    currency: str = Field("USD")
    
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "cost_usage"
        indexes = [
            [("identifier_type", 1), ("identifier_id", 1)],
            [("updated_at", -1)],
        ]


class EmbeddingCacheDocument(Document):
    """Locally caches dense embeddings vector queries."""

    text_hash: str = Field(..., description="SHA-256 hash of embedded text content")
    text: str = Field(..., description="Plaintext content cached")
    embedding: List[float] = Field(..., description="Generated float vector coordinates")
    
    provider: str = Field(..., description="Provider used")
    model: str = Field(..., description="Model used")
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "embedding_cache"
        indexes = [
            [("text_hash", 1)],
        ]
