"""
Agent Execution Result Structures.
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class AgentExecutionStatus(BaseModel):
    status: str = Field("completed", description="completed | failed | pending | running | paused_for_approval")
    confidence: int = Field(85, ge=0, le=100)
    execution_time_seconds: float = Field(0.0, ge=0.0)


class AgentResult(BaseModel):
    """Standardized output returned by every Agent execution."""
    status: str = Field("completed", description="completed | failed | paused_for_approval")
    confidence: int = Field(85, ge=0, le=100)
    messages: List[str] = Field(default_factory=list, description="Human readable agent messages & reasoning")
    logs: List[str] = Field(default_factory=list, description="Structured internal execution log entries")
    artifacts: List[Dict[str, Any]] = Field(default_factory=list, description="Artifacts generated during execution")
    outputs: Dict[str, Any] = Field(default_factory=dict, description="Task output data payload")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary metadata tags")
