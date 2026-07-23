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
from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import StreamingResponse
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
    category: str = Field("conversation", description="conversation | research | outreach | score | summary")
    user_prompt_template: str = Field(..., description="Variables formatted template")
    system_prompt_template: Optional[str] = Field(None)
    variables: List[str] = Field(default_factory=list, description="Variables list keys")
    changes_description: Optional[str] = Field(None, description="Change history description log")


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
async def list_prompt_templates():
    """List all registered prompt templates from database."""
    # Ensure built-in prompts are seeded
    await prompt_manager.initialize_builtin_prompts()
    docs = await PromptTemplateDocument.find_all().to_list()
    return [d.model_dump() for d in docs]


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
            variables=payload.variables,
            changes_description=payload.changes_description,
        )
        return doc.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
