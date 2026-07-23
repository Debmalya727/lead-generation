"""
AI Execution Planner — Pydantic schemas for Phase 12.7C.
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class TaskStepSpec(BaseModel):
    """Specification for a single execution step in an AI plan."""
    step_id: str
    capability: str
    name: str
    description: Optional[str] = None
    node_type: str = "GenerationNode"
    dependencies: List[str] = Field(default_factory=list)
    config: Dict[str, Any] = Field(default_factory=dict)


class AIExecutionPlan(BaseModel):
    """Full execution plan constructed by AI Execution Planner."""
    plan_id: str
    prompt: str
    strategy: str = Field("sequential", description="sequential | parallel | cost_optimized | latency_optimized | fallback_heavy")
    required_capabilities: List[str] = Field(default_factory=list)
    steps: List[TaskStepSpec] = Field(default_factory=list)
    execution_order: List[str] = Field(default_factory=list)
    created_at_ts: float = 0.0
