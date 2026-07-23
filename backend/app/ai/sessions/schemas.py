"""
AI Session Manager schemas for Phase 12.7B.
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone


class AISessionCreate(BaseModel):
    """Input schema to create a new AI session."""
    conversation_id: Optional[str] = None
    workflow_id: Optional[str] = None
    user_id: Optional[str] = None
    org_id: Optional[str] = None
    agent_id: Optional[str] = None
    capability: Optional[str] = None
    provider: str = ""
    model: str = ""
    streaming: bool = False


class AISessionUpdate(BaseModel):
    """Schema for updating session metrics after a completion."""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    estimated_cost: float = 0.0
    latency_ms: float = 0.0
    retry_count: int = 0
    fallback_count: int = 0
    cached: bool = False
    provider: Optional[str] = None
    model: Optional[str] = None
    guardrail_passed: Optional[bool] = None
    guardrail_flags: List[str] = Field(default_factory=list)
    policy_id: Optional[str] = None
    selected_policy: Optional[str] = None
    cache_key: Optional[str] = None
    prompt_hash: Optional[str] = None
