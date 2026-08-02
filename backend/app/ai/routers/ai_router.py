"""
REST APIs for Phase 12.7A Enterprise AI Gateway.
Endpoints:
- GET /api/v1/ai/providers
- GET /api/v1/ai/models
- GET /api/v1/ai/prompts
- POST /api/v1/ai/prompts
- POST /api/v1/ai/chat
- POST /api/v1/ai/embeddings
- GET /api/v1/ai/costs
- GET /api/v1/ai/tokens
"""
import os
import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Query, Response, status
from fastapi.responses import StreamingResponse, PlainTextResponse
from pydantic import BaseModel, Field

from app.ai.registry.provider_registry import ProviderRegistry
from app.ai.registry.model_registry import ModelRegistry
from app.ai.prompts.prompt_manager import prompt_manager
from app.ai.embeddings.embedding_service import embedding_service
from app.ai.gateway.gateway import ai_gateway
from app.ai.streaming.streaming import streaming_engine
from app.database.mongodb.collections.ai_gateway import (
    PromptTemplateDocument,
    PromptVersionDocument,
    TokenUsageDocument,
    CostUsageDocument,
)

logger = logging.getLogger("backend.ai.routers")

router = APIRouter(prefix="/ai", tags=["AI Gateway"])


# ─── Request / Response Schemas ───

class ChatCompletionRequest(BaseModel):
    prompt: str = Field(..., description="Prompt user instruction text")
    system_prompt: Optional[str] = Field("", description="System instruction guidelines")
    provider: str = Field("gemini", description="AI Provider identifier")
    model: str = Field("gemini-1.5-flash", description="Model identifier")
    stream: bool = Field(False, description="Whether to stream response over SSE")
    user_id: Optional[str] = None
    org_id: Optional[str] = None
    workflow_id: Optional[str] = None
    conversation_id: Optional[str] = None
    agent_id: Optional[str] = None
    plugin_id: Optional[str] = None


class EmbeddingRequest(BaseModel):
    text: str = Field(..., description="Plaintext content to generate embedding vector for")


class PromptSaveRequest(BaseModel):
    template_id: str = Field(..., description="Unique prompt template ID")
    name: str = Field(..., description="Prompt template name")
    category: str = Field("conversation", description="conversation | research | outreach | score | summary | reasoning | coding | custom")
    tags: List[str] = Field(default_factory=list, description="Searchable tags")
    user_prompt_template: str = Field(..., description="Variables formatted template")
    system_prompt_template: Optional[str] = Field(None)
    variables: List[str] = Field(default_factory=list, description="Variables list keys")
    changes_description: Optional[str] = Field(None, description="Change history description log")
    author: str = Field("System")


class PromptRollbackRequest(BaseModel):
    target_version: int = Field(..., description="Version number to rollback to")


class PromptApprovalRequest(BaseModel):
    status: str = Field(..., description="DRAFT | IN_REVIEW | APPROVED | REJECTED | PUBLISHED | ARCHIVED")


class PromptPublishRequest(BaseModel):
    version: Optional[int] = Field(None, description="Version number to publish")


class PromptTestRequest(BaseModel):
    variables: Dict[str, Any] = Field(default_factory=dict, description="Variables values")
    provider: str = Field("gemini", description="AI Provider")
    model: str = Field("gemini-1.5-flash", description="Model ID")


class PromptABTestCreateRequest(BaseModel):
    test_id: str = Field(..., description="Unique A/B experiment test ID")
    template_id: str = Field(..., description="Associated prompt template ID")
    name: str = Field(..., description="Experiment name")
    variant_a_version: int = Field(...)
    variant_b_version: int = Field(...)
    traffic_split_percent: float = Field(50.0)


# ─── Endpoints ───

@router.get("/providers")
def get_providers():
    """Retrieve registered AI providers."""
    classes = ProviderRegistry.list_providers()
    return [{"provider": name, "status": "active"} for name in classes.keys()]


@router.get("/models")
def get_models():
    """Retrieve supported models, capabilities, context windows, and pricing structures."""
    models_dict = ModelRegistry.list_models()
    return [
        {
            "model_id": model_id,
            "provider": info["provider"],
            "name": info["name"],
            "capabilities": info["capabilities"],
            "context_window": info["context_window"],
            "input_token_price": info["input_token_price"],
            "output_token_price": info["output_token_price"],
            "is_embedding": info["is_embedding"],
        }
        for model_id, info in models_dict.items()
    ]


@router.get("/prompts")
async def list_prompt_templates(
    query: Optional[str] = Query(None, description="Search query string"),
    category: Optional[str] = Query(None, description="Filter category"),
    tag: Optional[str] = Query(None, description="Filter tag"),
    status: Optional[str] = Query(None, description="Filter status"),
):
    """List and search prompt templates with category, tag, and status filtering."""
    return await prompt_manager.list_templates(query=query, category=category, tag=tag, status=status)


@router.get("/prompts/{template_id}")
async def get_prompt_template(template_id: str):
    """Fetch single prompt template by ID."""
    try:
        doc = await prompt_manager.get_template(template_id)
        return doc if isinstance(doc, dict) else doc.model_dump()
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/prompts", status_code=status.HTTP_201_CREATED)
async def save_prompt_template(payload: PromptSaveRequest):
    """Save or update prompt template, capturing structural version revisions."""
    try:
        doc = await prompt_manager.save_template(
            template_id=payload.template_id,
            name=payload.name,
            category=payload.category,
            user_prompt_template=payload.user_prompt_template,
            system_prompt_template=payload.system_prompt_template,
            tags=payload.tags,
            changes_description=payload.changes_description,
            author=payload.author,
        )
        return doc.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/prompts/{template_id}/history")
async def get_prompt_history(template_id: str):
    """Fetch complete version history for a prompt template."""
    return await prompt_manager.get_version_history(template_id)


@router.get("/prompts/{template_id}/diff")
async def get_prompt_diff(
    template_id: str,
    version_a: int = Query(..., description="First version number"),
    version_b: int = Query(..., description="Second version number"),
):
    """Generate side-by-side unified diff between two prompt versions."""
    try:
        return await prompt_manager.generate_diff(template_id, version_a, version_b)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/prompts/{template_id}/rollback")
async def rollback_prompt_version(template_id: str, payload: PromptRollbackRequest):
    """Rollback prompt template to a historical version."""
    try:
        doc = await prompt_manager.rollback_version(template_id, payload.target_version)
        return doc.model_dump()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/prompts/{template_id}/approval")
async def update_prompt_approval(template_id: str, payload: PromptApprovalRequest):
    """Transition approval workflow state (DRAFT -> IN_REVIEW -> APPROVED -> REJECTED)."""
    try:
        doc = await prompt_manager.update_approval(template_id, payload.status)
        return doc.model_dump()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/prompts/{template_id}/publish")
async def publish_prompt_version(template_id: str, payload: PromptPublishRequest):
    """Publish prompt version for production execution."""
    try:
        doc = await prompt_manager.publish_version(template_id, payload.version)
        return doc.model_dump()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/prompts/{template_id}/test")
async def test_prompt_template(template_id: str, payload: PromptTestRequest):
    """Execute interactive test run of prompt template through AIGateway."""
    try:
        return await prompt_manager.test_prompt(
            template_id=template_id,
            variables=payload.variables,
            provider=payload.provider,
            model=payload.model,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/prompts/ab-tests", status_code=status.HTTP_201_CREATED)
async def create_ab_test(payload: PromptABTestCreateRequest):
    """Create A/B testing experiment comparing two prompt version variants."""
    try:
        doc = await prompt_manager.create_ab_test(
            test_id=payload.test_id,
            template_id=payload.template_id,
            name=payload.name,
            variant_a_version=payload.variant_a_version,
            variant_b_version=payload.variant_b_version,
            traffic_split_percent=payload.traffic_split_percent,
        )
        return doc.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/prompts/ab-tests/{test_id}")
async def get_ab_test_telemetry(test_id: str):
    """Query A/B experiment telemetry metrics."""
    try:
        doc = await prompt_manager.get_ab_test(test_id)
        return doc.model_dump()
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/chat")
async def chat_completions(payload: ChatCompletionRequest):
    """Execute completions through unified AIGateway."""
    try:
        if payload.stream:
            # Execute completion synchronously first to get full text, then stream over SSE
            res = await ai_gateway.generate_completion(
                prompt=payload.prompt,
                system_prompt=payload.system_prompt or "",
                provider=payload.provider,
                model=payload.model,
                user_id=payload.user_id,
                org_id=payload.org_id,
                workflow_id=payload.workflow_id,
                conversation_id=payload.conversation_id,
                agent_id=payload.agent_id,
                plugin_id=payload.plugin_id,
            )
            return StreamingResponse(
                streaming_engine.stream_completion(
                    text_content=res["response_text"],
                    correlation_id=res["correlation_id"],
                    provider=res["provider_used"],
                    model=res["model_used"],
                ),
                media_type="text/event-stream"
            )
        else:
            res = await ai_gateway.generate_completion(
                prompt=payload.prompt,
                system_prompt=payload.system_prompt or "",
                provider=payload.provider,
                model=payload.model,
                user_id=payload.user_id,
                org_id=payload.org_id,
                workflow_id=payload.workflow_id,
                conversation_id=payload.conversation_id,
                agent_id=payload.agent_id,
                plugin_id=payload.plugin_id,
            )
            return res
    except Exception as e:
        logger.error(f"Chat completions gateway endpoint failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/embeddings")
async def generate_embeddings(payload: EmbeddingRequest):
    """Generate dense embeddings vector coordinate array."""
    try:
        vec = await embedding_service.embed_text(payload.text)
        return {
            "embedding": vec,
            "dimensions": len(vec),
            "model": os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/costs")
async def get_cost_usage(
    identifier_type: Optional[str] = Query(None, description="user | organization | workflow | conversation | agent | plugin")
):
    """Query cumulative USD cost stats."""
    if identifier_type:
        docs = await CostUsageDocument.find(CostUsageDocument.identifier_type == identifier_type).to_list()
    else:
        docs = await CostUsageDocument.find_all().to_list()
    return [d.model_dump() for d in docs]


@router.get("/tokens")
async def get_token_usage(
    identifier_type: Optional[str] = Query(None, description="user | organization | workflow | conversation | agent | plugin")
):
    """Query cumulative Token count statistics."""
    if identifier_type:
        docs = await TokenUsageDocument.find(TokenUsageDocument.identifier_type == identifier_type).to_list()
    else:
        docs = await TokenUsageDocument.find_all().to_list()
    return [d.model_dump() for d in docs]


# ─── Enterprise AI Provider Platform Endpoints ───

@router.get("/provider/health")
def get_provider_health():
    """Retrieve live health status and rolling statistics across all 9 AI providers."""
    from app.ai.gateway.health_manager import provider_health_manager
    from app.ai.resilience.circuit_breaker import circuit_breaker_registry

    health_data = provider_health_manager.get_all_stats()
    circuit_data = circuit_breaker_registry.get_all_statuses()

    return [
        {
            **stats,
            "circuit_breaker_state": circuit_data.get(prov, {}).get("state", "CLOSED"),
        }
        for prov, stats in health_data.items()
    ]


@router.get("/provider/models")
def get_provider_models():
    """Retrieve full Model Registry metadata, capabilities, context length, pricing, and scores."""
    return get_models()


@router.get("/provider/stats")
def get_provider_stats():
    """Retrieve telemetry, latency p95, success rate, and error breakdown per provider."""
    from app.ai.gateway.health_manager import provider_health_manager
    return provider_health_manager.get_all_stats()


@router.get("/provider/cost")
async def get_provider_cost(
    identifier_type: Optional[str] = Query(None, description="user | organization | workflow | conversation | agent | plugin | provider | model | endpoint")
):
    """Retrieve accumulated dollar cost breakdown by organization, user, provider, model, or endpoint."""
    return await get_cost_usage(identifier_type)


@router.get("/provider/usage")
async def get_provider_usage(
    identifier_type: Optional[str] = Query(None, description="user | organization | workflow | conversation | agent | plugin | provider | model | endpoint")
):
    """Retrieve token usage metrics across all providers, models, organizations, and endpoints."""
    return await get_token_usage(identifier_type)


@router.get("/provider/rankings")
def get_provider_rankings():
    """Retrieve real-time dynamic provider ranking scores."""
    from app.ai.router.ranking_engine import ranking_engine
    return ranking_engine.rank_providers()


# ─── Enterprise AI Cache Endpoints ───

class CacheWarmRequest(BaseModel):
    items: List[Dict[str, Any]] = Field(..., description="List of prompt/response or context items to pre-load")


class CacheClearRequest(BaseModel):
    scope: str = Field("all", description="Cache scope to purge: all | prompt | response | embedding | context")


@router.get("/cache/stats")
async def get_cache_stats():
    """Retrieve live Enterprise AI Cache telemetry, hit/miss ratios, saved latency, tokens, and USD cost."""
    from app.ai.cache.ai_cache import ai_cache
    return await ai_cache.get_stats()


@router.post("/cache/clear")
def clear_cache(payload: CacheClearRequest):
    """Purge AI Cache entries by scope (all | prompt | response | embedding | context)."""
    from app.ai.cache.ai_cache import ai_cache
    return ai_cache.clear(scope=payload.scope)


@router.post("/cache/warm")
def warm_cache(payload: CacheWarmRequest):
    """Pre-load cache entries for prompt templates or RAG context documents."""
    from app.ai.cache.ai_cache import ai_cache
    return ai_cache.warm(payload.items)


@router.get("/cache/export")
def export_cache():
    """Export snapshot of active cache keys, memory metrics, and hit/miss telemetry."""
    from app.ai.cache.ai_cache import ai_cache
    return ai_cache.export_snapshot()


# ─── Enterprise AI Tool Calling Endpoints ───

class ToolExecuteRequest(BaseModel):
    tool_name: str = Field(..., description="Target tool identifier name")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="JSON input arguments")
    user_scopes: Optional[List[str]] = Field(None, description="Granted permission scopes e.g. ['crm:read', 'email:send']")
    correlation_id: Optional[str] = Field(None, description="Tracing correlation ID")


@router.get("/tools")
def list_registered_tools(category: Optional[str] = Query(None, description="Filter category")):
    """Retrieve list of registered enterprise tools with schemas, scopes, and telemetry."""
    from app.ai.tools.tool_registry import tool_registry
    tools = tool_registry.list_tools(category=category)
    return [
        {
            "name": t.name,
            "description": t.description,
            "category": t.category,
            "permission_scope": t.permission_scope,
            "version": t.version,
            "parameters_schema": t.parameters_schema,
            "execution_count": t.execution_count,
            "error_count": t.error_count,
            "average_latency_ms": t.average_latency_ms,
            "success_rate_percent": t.success_rate_percent,
        }
        for t in tools
    ]


@router.get("/tools/schemas/openai")
def get_openai_tool_schemas(category: Optional[str] = Query(None, description="Filter category")):
    """Export tools formatted in OpenAI standard function calling schema."""
    from app.ai.tools.tool_registry import tool_registry
    return tool_registry.to_openai_tools(category=category)


@router.get("/tools/schemas/gemini")
def get_gemini_tool_schemas(category: Optional[str] = Query(None, description="Filter category")):
    """Export tools formatted in Google Gemini function declaration schema."""
    from app.ai.tools.tool_registry import tool_registry
    return tool_registry.to_gemini_tools(category=category)


@router.get("/tools/metrics")
def get_tool_metrics():
    """Retrieve aggregate tool telemetry metrics across all domains."""
    from app.ai.tools.tool_registry import tool_registry
    return tool_registry.get_metrics()


@router.get("/tools/logs")
def get_tool_execution_logs(limit: int = Query(50, description="Max logs to return")):
    """Fetch execution audit logs from ToolSandbox."""
    from app.ai.tools.tool_sandbox import tool_sandbox
    return tool_sandbox.get_execution_logs(limit=limit)


@router.get("/tools/{tool_name}")
def get_tool_definition(tool_name: str):
    """Fetch details and parameter schema for a single registered tool."""
    from app.ai.tools.tool_registry import tool_registry
    try:
        t = tool_registry.get_tool(tool_name)
        return {
            "name": t.name,
            "description": t.description,
            "category": t.category,
            "permission_scope": t.permission_scope,
            "version": t.version,
            "parameters_schema": t.parameters_schema,
            "execution_count": t.execution_count,
            "error_count": t.error_count,
            "average_latency_ms": t.average_latency_ms,
            "success_rate_percent": t.success_rate_percent,
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/tools/execute")
async def execute_tool_sandboxed(payload: ToolExecuteRequest):
    """Execute a tool through the security sandbox execution bridge."""
    from app.ai.tools.tool_sandbox import tool_sandbox
    return await tool_sandbox.execute_tool(
        tool_name=payload.tool_name,
        arguments=payload.arguments,
        user_scopes=payload.user_scopes,
        correlation_id=payload.correlation_id or "corr_rest_exec",
    )


# ─── Enterprise AI Agent Platform Endpoints ───

class AgentCreateRequest(BaseModel):
    agent_id: str = Field(..., description="Unique agent ID name")
    name: str = Field(..., description="Agent display name")
    role: str = Field(..., description="Role title")
    description: str = Field(...)
    system_prompt: str = Field(...)
    assigned_tools: List[str] = Field(default_factory=list)
    permission_scopes: List[str] = Field(default_factory=list)


class AgentRunRequest(BaseModel):
    goal: str = Field(..., description="Autonomous task goal string")
    user_scopes: Optional[List[str]] = Field(None, description="Granted scopes")


class AgentTeamRunRequest(BaseModel):
    team_name: str = Field(..., description="Team identifier name")
    participating_agent_ids: List[str] = Field(..., description="Agents on the team")
    goal: str = Field(..., description="Collective team goal")
    user_scopes: Optional[List[str]] = Field(None)


class AgentMarketplaceInstallRequest(BaseModel):
    template_id: str = Field(..., description="Marketplace template ID")


@router.get("/agents")
def list_registered_agents():
    """List all active registered enterprise agents."""
    from app.ai.agents.agent_platform import agent_platform
    return [
        {
            "agent_id": a.agent_id,
            "name": a.name,
            "role": a.role,
            "description": a.description,
            "status": a.status,
            "assigned_tools": a.assigned_tools,
            "permission_scopes": a.permission_scopes,
            "success_rate_percent": a.success_rate_percent,
            "total_runs": a.total_runs,
        }
        for a in agent_platform.list_agents()
    ]


@router.get("/agents/marketplace")
def list_marketplace_agent_templates():
    """Catalog of pre-configured Enterprise Agent Marketplace templates."""
    from app.ai.agents.agent_platform import agent_platform
    return [
        {
            "agent_id": a.agent_id,
            "name": a.name,
            "role": a.role,
            "description": a.description,
            "assigned_tools": a.assigned_tools,
            "permission_scopes": a.permission_scopes,
        }
        for a in agent_platform.list_marketplace_templates()
    ]


@router.post("/agents/marketplace/install")
def install_marketplace_agent(payload: AgentMarketplaceInstallRequest):
    """1-Click install Marketplace agent template."""
    from app.ai.agents.agent_platform import agent_platform
    try:
        a = agent_platform.install_marketplace_agent(payload.template_id)
        return {"status": "installed", "agent_id": a.agent_id, "name": a.name}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/agents/metrics")
def get_agent_metrics():
    """Retrieve aggregate telemetry and performance metrics for AI Agents."""
    from app.ai.agents.agent_platform import agent_platform
    return agent_platform.get_analytics()


@router.get("/agents/{agent_id}")
def get_agent_definition(agent_id: str):
    """Fetch details and status for a single registered AI Agent."""
    from app.ai.agents.agent_platform import agent_platform
    try:
        a = agent_platform.get_agent(agent_id)
        return {
            "agent_id": a.agent_id,
            "name": a.name,
            "role": a.role,
            "description": a.description,
            "system_prompt": a.system_prompt,
            "status": a.status,
            "assigned_tools": a.assigned_tools,
            "permission_scopes": a.permission_scopes,
            "total_runs": a.total_runs,
            "successful_runs": a.successful_runs,
            "failed_runs": a.failed_runs,
            "success_rate_percent": a.success_rate_percent,
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/agents")
def register_agent(payload: AgentCreateRequest):
    """Register a new custom AI Agent."""
    from app.ai.agents.agent_platform import agent_platform
    a = agent_platform.register_agent(
        agent_id=payload.agent_id,
        name=payload.name,
        role=payload.role,
        description=payload.description,
        system_prompt=payload.system_prompt,
        assigned_tools=payload.assigned_tools,
        permission_scopes=payload.permission_scopes,
    )
    return {"status": "registered", "agent_id": a.agent_id}


@router.post("/agents/{agent_id}/run")
async def run_agent_goal(agent_id: str, payload: AgentRunRequest):
    """Run autonomous single agent task execution with planning, sandboxed tool calls, and reflection."""
    from app.ai.agents.agent_platform import agent_platform
    return await agent_platform.run_agent(
        agent_id=agent_id,
        goal=payload.goal,
        user_scopes=payload.user_scopes,
    )


@router.post("/agents/teams/run")
async def run_agent_team_goal(payload: AgentTeamRunRequest):
    """Run multi-agent team execution with task delegation and consensus synthesis."""
    from app.ai.agents.agent_platform import agent_platform
    return await agent_platform.run_agent_team(
        team_name=payload.team_name,
        participating_agent_ids=payload.participating_agent_ids,
        goal=payload.goal,
        user_scopes=payload.user_scopes,
    )


# ─── Enterprise Observability Platform Endpoints ───

class AlertTriggerRequest(BaseModel):
    alert_type: str = Field("LATENCY_ANOMALY", description="LATENCY_ANOMALY | ERROR_SPIKE | BUDGET_OVERRUN | SLA_BREACH")
    severity: str = Field("WARNING", description="INFO | WARNING | CRITICAL")
    source_component: str = Field("Manual Test")
    message: str = Field(...)
    metrics_snapshot: Optional[Dict[str, Any]] = None


@router.get("/metrics", response_class=PlainTextResponse)
def export_prometheus_metrics_endpoint():
    """Prometheus text format exporter endpoint."""
    from app.ai.observability.observability import observability_engine
    return observability_engine.export_prometheus_metrics()


@router.get("/observability/overview")
def get_observability_overview():
    """Retrieve system SLA compliance score, P95 latency, requests count, and active alerts summary."""
    from app.ai.observability.observability import observability_engine
    return observability_engine.get_overview()


@router.get("/observability/traces")
def get_distributed_traces(limit: int = Query(50, description="Max traces to return")):
    """List recent distributed request traces and OpenTelemetry span telemetry."""
    from app.ai.observability.observability import observability_engine
    return observability_engine.list_traces(limit=limit)


@router.get("/observability/alerts")
def get_observability_alerts(limit: int = Query(50, description="Max alerts to return")):
    """List active SLA breaches, statistical latency anomalies, and system alerts."""
    from app.ai.observability.observability import observability_engine
    return observability_engine.list_alerts(limit=limit)


@router.post("/observability/alerts/trigger")
async def trigger_observability_alert(payload: AlertTriggerRequest):
    """Manually dispatch a system alert event."""
    from app.ai.observability.observability import observability_engine
    return await observability_engine.dispatch_alert(
        alert_type=payload.alert_type,
        severity=payload.severity,
        source_component=payload.source_component,
        message=payload.message,
        metrics_snapshot=payload.metrics_snapshot,
    )


# ─── Enterprise Security Hardening Platform Endpoints ───

class SecretEncryptRequest(BaseModel):
    plaintext: str = Field(..., description="Secret string to encrypt")


class SecretDecryptRequest(BaseModel):
    ciphertext: str = Field(..., description="Encrypted ciphertext string")


class PromptScanRequest(BaseModel):
    prompt: str = Field(..., description="LLM prompt text to scan for injection")


class FileScanRequest(BaseModel):
    filename: str = Field(...)
    file_b64: str = Field(..., description="Base64 encoded file content")


@router.get("/security/overview")
def get_security_overview():
    """Retrieve SOC 2 & GDPR compliance scores, active threat count, and WAF blocks summary."""
    from app.ai.security.security_engine import security_engine
    return security_engine.get_compliance_status()


@router.get("/security/audit-logs")
def get_security_audit_logs(limit: int = Query(50, description="Max audit logs to return")):
    """List security audit events, WAF blocks, and key rotation logs."""
    from app.ai.security.security_engine import security_engine
    return security_engine.list_audit_logs(limit=limit)


@router.post("/security/encrypt")
def encrypt_secret_endpoint(payload: SecretEncryptRequest):
    """Encrypt secret string using AES-256-GCM + HMAC-SHA256."""
    from app.ai.security.security_engine import security_engine
    ciphertext = security_engine.encrypt_secret(payload.plaintext)
    return {"ciphertext": ciphertext, "key_version": security_engine._active_key_version}


@router.post("/security/decrypt")
def decrypt_secret_endpoint(payload: SecretDecryptRequest):
    """Decrypt secret ciphertext using active master encryption key."""
    from app.ai.security.security_engine import security_engine
    try:
        plaintext = security_engine.decrypt_secret(payload.ciphertext)
        return {"plaintext": plaintext}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/security/rotate-keys")
async def rotate_master_keys_endpoint():
    """Trigger 1-Click Master Encryption Key Rotation."""
    from app.ai.security.security_engine import security_engine
    return await security_engine.rotate_master_key()


@router.post("/security/scan-prompt")
def scan_prompt_injection_endpoint(payload: PromptScanRequest):
    """Scan LLM prompt text for jailbreak attempts, system overrides, and prompt leaks."""
    from app.ai.security.security_engine import security_engine
    return security_engine.scan_prompt_injection(payload.prompt)


@router.post("/security/scan-file")
def scan_file_malware_endpoint(payload: FileScanRequest):
    """Scan base64 file content for executable binaries, malware headers, and dangerous extensions."""
    import base64
    from app.ai.security.security_engine import security_engine
    try:
        raw_bytes = base64.b64decode(payload.file_b64)
        return security_engine.scan_file_binary(raw_bytes, payload.filename)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid Base64 payload: {str(e)}")


# ─── Enterprise Resend Email & Outreach Platform Endpoints ───

class EmailSendRequest(BaseModel):
    to_email: str = Field(...)
    subject: str = Field(...)
    html_content: str = Field(...)
    variables: Optional[Dict[str, Any]] = None


class TemplateCompileRequest(BaseModel):
    template_str: str = Field(...)
    variables: Dict[str, Any] = Field(default_factory=dict)
    is_mjml: bool = Field(False)


class CampaignLaunchRequest(BaseModel):
    name: str = Field(...)
    subject: str = Field(...)
    template_html: str = Field(...)
    recipients: List[Dict[str, Any]] = Field(...)


@router.post("/email/send")
async def send_email_endpoint(payload: EmailSendRequest):
    """Send transactional email via Resend API with open/click tracking and rate limit retry engine."""
    from app.email.email_engine import email_engine
    try:
        return await email_engine.send_email(
            to_email=payload.to_email,
            subject=payload.subject,
            html_content=payload.html_content,
            variables=payload.variables,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/email/compile-template")
def compile_template_endpoint(payload: TemplateCompileRequest):
    """Compile MJML/HTML template with variable tags."""
    from app.email.email_engine import email_engine
    content = payload.template_str
    if payload.is_mjml:
        content = email_engine.compile_mjml(content)
    compiled_html = email_engine.compile_template(content, payload.variables)
    return {"compiled_html": compiled_html}


@router.post("/email/campaigns")
async def launch_campaign_endpoint(payload: CampaignLaunchRequest):
    """Launch batch email outreach campaign across recipient lead list."""
    from app.email.email_engine import email_engine
    return await email_engine.launch_campaign(
        name=payload.name,
        template_html=payload.template_html,
        subject=payload.subject,
        recipients=payload.recipients,
    )


@router.post("/email/webhooks/resend")
async def resend_webhook_endpoint(payload: Dict[str, Any]):
    """Process incoming Resend webhook events (sent, delivered, opened, clicked, bounced, complained)."""
    from app.email.email_engine import email_engine
    return await email_engine.process_resend_webhook(payload)


@router.get("/email/analytics")
def get_email_analytics():
    """Retrieve system-wide email delivery rate, open rate, CTR %, bounce rate, and suppressed count."""
    from app.email.email_engine import email_engine
    return email_engine.get_analytics()


@router.get("/email/webhooks/events")
def get_email_webhook_events(limit: int = Query(50, description="Max webhook events to return")):
    """List recent Resend webhook telemetry events."""
    from app.email.email_engine import email_engine
    return email_engine.list_webhook_events(limit=limit)


# ─── Enterprise AI Playground Platform Endpoints ───

class PlaygroundExecuteRequest(BaseModel):
    prompt: str = Field(...)
    provider: str = Field("gemini")
    model: Optional[str] = None
    system_prompt: Optional[str] = None
    temperature: float = Field(0.7)
    top_p: float = Field(0.9)
    max_tokens: int = Field(1024)
    json_mode: bool = Field(False)


class PlaygroundCompareRequest(BaseModel):
    prompt: str = Field(...)
    targets: List[Dict[str, str]] = Field(...)
    system_prompt: Optional[str] = None
    temperature: float = Field(0.7)
    top_p: float = Field(0.9)
    max_tokens: int = Field(1024)
    json_mode: bool = Field(False)


class PlaygroundSessionSaveRequest(BaseModel):
    title: str = Field(...)
    prompt: str = Field(...)
    runs: List[Dict[str, Any]] = Field(...)
    system_prompt: Optional[str] = None
    hyperparameters: Optional[Dict[str, Any]] = None


class PlaygroundExportRequest(BaseModel):
    session_data: Dict[str, Any] = Field(...)
    format_type: str = Field("markdown", description="json | markdown")


@router.post("/playground/execute")
async def execute_playground_single(payload: PlaygroundExecuteRequest):
    """Execute single model prompt with hyperparameters and telemetry metrics."""
    from app.ai.playground.playground_engine import playground_engine
    return await playground_engine.execute_single(
        prompt=payload.prompt,
        provider=payload.provider,
        model=payload.model,
        system_prompt=payload.system_prompt,
        temperature=payload.temperature,
        top_p=payload.top_p,
        max_tokens=payload.max_tokens,
        json_mode=payload.json_mode,
    )


@router.post("/playground/compare")
async def execute_playground_compare(payload: PlaygroundCompareRequest):
    """Run parallel side-by-side prompt execution across multiple providers/models."""
    from app.ai.playground.playground_engine import playground_engine
    return await playground_engine.execute_compare(
        prompt=payload.prompt,
        targets=payload.targets,
        system_prompt=payload.system_prompt,
        temperature=payload.temperature,
        top_p=payload.top_p,
        max_tokens=payload.max_tokens,
        json_mode=payload.json_mode,
    )


@router.post("/playground/sessions")
async def save_playground_session_endpoint(payload: PlaygroundSessionSaveRequest):
    """Persist AI Playground session into database and memory."""
    from app.ai.playground.playground_engine import playground_engine
    return await playground_engine.save_session(
        title=payload.title,
        prompt=payload.prompt,
        runs=payload.runs,
        system_prompt=payload.system_prompt,
        hyperparameters=payload.hyperparameters,
    )


@router.get("/playground/sessions")
def list_playground_sessions_endpoint(limit: int = Query(50, description="Max sessions to return")):
    """List saved AI Playground sessions and comparative histories."""
    from app.ai.playground.playground_engine import playground_engine
    return playground_engine.list_sessions(limit=limit)


@router.post("/playground/export", response_class=PlainTextResponse)
def export_playground_results_endpoint(payload: PlaygroundExportRequest):
    """Export comparative execution results to JSON or formatted Markdown."""
    from app.ai.playground.playground_engine import playground_engine
    return playground_engine.export_session_results(payload.session_data, payload.format_type)
