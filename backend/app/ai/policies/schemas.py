"""
Pydantic schemas for the AI Policy Engine (Phase 12.7B).
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class PolicyCondition(BaseModel):
    """Condition for when a policy applies."""
    org_id: Optional[str] = None
    user_tier: Optional[str] = None          # free | pro | enterprise
    min_context_tokens: Optional[int] = None  # Trigger if context > threshold
    max_cost_per_request: Optional[float] = None


class PolicyAction(BaseModel):
    """The routing action a policy prescribes."""
    provider: str = Field(..., description="Target provider")
    model: str = Field(..., description="Target model")
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None


class PolicyRule(BaseModel):
    """A single policy rule binding a capability to conditions and an action."""
    policy_id: str
    name: str
    capability: str
    priority: int = 100
    is_active: bool = True
    conditions: PolicyCondition = Field(default_factory=PolicyCondition)
    action: PolicyAction
    org_id: Optional[str] = None
    description: Optional[str] = None


class PolicySet(BaseModel):
    """A named collection of policy rules."""
    name: str
    rules: List[PolicyRule] = Field(default_factory=list)


class PolicyResolution(BaseModel):
    """Result of resolving a capability against the policy engine."""
    capability: str
    provider: str
    model: str
    policy_id: Optional[str] = None
    policy_name: Optional[str] = None
    resolved_from: str = "default"  # "policy" | "default" | "fallback"
