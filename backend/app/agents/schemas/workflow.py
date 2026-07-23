"""
Pydantic v2 Schemas for Workflow & Tool Orchestration Engine.
"""
from typing import List, Dict, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field


class WorkflowRunRequest(BaseModel):
    workflow_id: str = Field(..., description="Template ID e.g. 'sales_discovery' or custom workflow ID")
    company_name: Optional[str] = Field(None, description="Target company name")
    lead_id: Optional[str] = Field(None, description="Target Lead ID")
    inputs: Dict[str, Any] = Field(default_factory=dict, description="Custom workflow input variables")
    policy_id: Optional[str] = Field(None, description="Optional governance policy ID")


class WorkflowStepResponse(BaseModel):
    step_execution_id: str
    execution_id: str
    step_id: str
    name: str
    step_type: str
    target: str
    status: str
    inputs: Dict[str, Any] = Field(default_factory=dict)
    outputs: Dict[str, Any] = Field(default_factory=dict)
    execution_time_seconds: float
    retry_count: int
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class WorkflowExecutionResponse(BaseModel):
    execution_id: str
    workflow_id: str
    job_id: Optional[str] = None
    lead_id: Optional[str] = None
    company_name: Optional[str] = None
    status: str
    progress: float
    current_step_id: Optional[str] = None
    execution_stats: Dict[str, Any] = Field(default_factory=dict)
    context_data: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime


class WorkflowExecutionListResponse(BaseModel):
    total_count: int
    items: List[WorkflowExecutionResponse]


class WorkflowCheckpointResponse(BaseModel):
    checkpoint_id: str
    execution_id: str
    step_id: str
    state_snapshot: Dict[str, Any] = Field(default_factory=dict)
    completed_step_ids: List[str] = Field(default_factory=list)
    pending_step_ids: List[str] = Field(default_factory=list)
    reason: str
    created_at: datetime


class ToolMetadataResponse(BaseModel):
    tool_id: str
    name: str
    description: str
    category: str
    version: str
    input_schema: Dict[str, Any] = Field(default_factory=dict)
    output_schema: Dict[str, Any] = Field(default_factory=dict)
    permissions: List[str] = Field(default_factory=list)
    timeout: int
    cost_estimate: float


class ToolExecuteRequest(BaseModel):
    inputs: Dict[str, Any] = Field(default_factory=dict)
    invoker_agent: str = Field("User", description="Invoker agent ID or name")
    max_retries: int = Field(1, ge=0, le=5)


class ToolExecutionResponse(BaseModel):
    status: str
    tool_id: str
    outputs: Dict[str, Any] = Field(default_factory=dict)
    execution_time_seconds: float
    cost_estimate: float
    error_message: Optional[str] = None
