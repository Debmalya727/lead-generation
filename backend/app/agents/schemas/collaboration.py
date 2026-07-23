"""
Pydantic v2 Schemas for Multi-Agent Collaboration Engine REST API.
"""
from typing import List, Dict, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class AgentMessageSchema(BaseModel):
    message_id: str
    conversation_id: str
    job_id: str
    task_id: Optional[str] = None
    from_agent: str
    to_agent: str
    message_type: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    confidence: int
    status: str
    timestamp: datetime


class SendMessageRequest(BaseModel):
    from_agent: str = Field(..., description="Sender agent ID")
    to_agent: str = Field(..., description="Recipient agent ID or 'broadcast'/'group'")
    message_type: str = Field("point_to_point", description="point_to_point | broadcast | delegation | proposal")
    payload: Dict[str, Any] = Field(default_factory=dict)
    conversation_id: Optional[str] = Field(None, description="Optional conversation thread ID")
    task_id: Optional[str] = Field(None)


class AgentArtifactSchema(BaseModel):
    artifact_id: str
    job_id: str
    task_id: Optional[str] = None
    owner_agent: str
    artifact_type: str
    title: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    content: Dict[str, Any] = Field(default_factory=dict)
    confidence: int
    version: int
    parent_version_id: Optional[str] = None
    created_at: datetime


class ConsensusDecisionSchema(BaseModel):
    consensus_id: str
    job_id: str
    task_id: Optional[str] = None
    topic: str
    proposals: List[Dict[str, Any]] = Field(default_factory=list)
    strategy_used: str
    resolved_output: Dict[str, Any] = Field(default_factory=dict)
    winning_agent: Optional[str] = None
    confidence: int
    is_conflict: bool
    conflict_details: Optional[Dict[str, Any]] = None
    resolved_at: datetime


class DelegationRequest(BaseModel):
    from_agent: str = Field(..., description="Delegating agent ID")
    target_agent: str = Field(..., description="Target recipient agent ID")
    task_description: str = Field(..., description="Sub-task goal instructions")
    inputs: Dict[str, Any] = Field(default_factory=dict)
    timeout_seconds: int = Field(30, ge=5, le=300)
    max_retries: int = Field(2, ge=0, le=5)
    approval_required: bool = Field(False)


class DelegationResponse(BaseModel):
    status: str
    confidence: int
    messages: List[str] = Field(default_factory=list)
    outputs: Dict[str, Any] = Field(default_factory=dict)


class CollaborationMetricsSchema(BaseModel):
    job_id: str
    message_count: int
    artifact_count: int
    consensus_count: int
    conflict_count: int
    delegation_count: int
    total_sequential_latency_seconds: float
    actual_job_latency_seconds: float
    parallel_efficiency: float
    agent_utilization_percent: Dict[str, float] = Field(default_factory=dict)


class CollaborationSummaryResponse(BaseModel):
    job_id: str
    delegation_count: int
    conflict_count: int
    consensus_count: int
    message_count: int
    artifact_count: int
    active_conversations: List[Any] = Field(default_factory=list)
    metrics_summary: Dict[str, Any] = Field(default_factory=dict)
