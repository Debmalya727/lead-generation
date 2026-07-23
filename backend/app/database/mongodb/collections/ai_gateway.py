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
    """Tracks prompt templates and variables across LeadForgeAI categories."""

    template_id: str = Field(..., description="Unique prompt template ID")
    name: str = Field(..., description="Prompt template name")
    category: str = Field("conversation", description="conversation | research | lead_discovery | outreach | report | summary")
    
    system_prompt_template: Optional[str] = None
    user_prompt_template: str = Field(...)
    
    variables: List[str] = Field(default_factory=list, description="Required variable placeholder keys")
    created_by: str = Field("System")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "prompt_templates"
        indexes = [
            [("template_id", 1)],
            [("category", 1)],
        ]


class PromptVersionDocument(Document):
    """Tracks historical prompt version revisions and structural diff logs."""

    template_id: str = Field(..., description="Associated prompt template ID")
    version: int = Field(1, description="Sequential version index")
    
    system_prompt: Optional[str] = None
    user_prompt: str = Field(...)
    
    changes_description: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "prompt_versions"
        indexes = [
            [("template_id", 1), ("version", -1)],
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
