"""
Pydantic v2 Validation Schemas for Enterprise Agent Runtime API.
"""
from typing import List, Dict, Optional, Any, Literal
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class AgentRunRequest(BaseModel):
    goal: str = Field(..., description="Natural language goal instruction for the autonomous agent runtime")
    lead_id: Optional[str] = Field(None, description="Optional lead context ID — triggers business pipeline mode when provided")
    execution_mode: Literal["auto", "business_pipeline", "custom"] = Field(
        "auto",
        description="auto: LLM-driven planner | business_pipeline: deterministic 6-agent sales pipeline | custom: reserved for future"
    )
    company_name: Optional[str] = Field(None, description="Optional company name hint for business pipeline")
    approval_required: bool = Field(False, description="If true, each task node will require human approval before execution")


class ExecutionTaskSchema(BaseModel):
    task_id: str
    name: str
    agent_name: str
    description: str
    dependencies: List[str] = Field(default_factory=list)
    priority: int
    retry_count: int
    max_retries: int
    timeout_seconds: int
    parallelizable: bool
    approval_required: bool
    status: str
    inputs: Dict[str, Any] = Field(default_factory=dict)
    outputs: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None
    execution_time_seconds: float
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class ExecutionPlanSchema(BaseModel):
    plan_id: str
    goal: str
    tasks: List[ExecutionTaskSchema] = Field(default_factory=list)
    task_graph_json: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class AgentJobResponse(BaseModel):
    job_id: str
    goal: str
    lead_id: Optional[Any] = None
    owner_id: Any
    status: str
    progress: float
    plan: Optional[ExecutionPlanSchema] = None
    current_task_id: Optional[str] = None
    execution_stats: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    @field_validator("owner_id", "lead_id", mode="before")
    @classmethod
    def convert_objectid_to_str(cls, v: Any) -> Optional[str]:
        if v is not None:
            return str(v)
        return None


class AgentJobListResponse(BaseModel):
    total_count: int
    items: List[AgentJobResponse] = Field(default_factory=list)


class AgentEventResponse(BaseModel):
    event_id: str
    job_id: str
    owner_id: Any
    event_type: str
    source_agent: str
    task_id: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime

    @field_validator("owner_id", mode="before")
    @classmethod
    def convert_objectid_to_str(cls, v: Any) -> Optional[str]:
        if v is not None:
            return str(v)
        return None


class AgentApprovalRequest(BaseModel):
    task_id: str = Field(..., description="Task node ID to approve for execution")


class AgentRegistryItemResponse(BaseModel):
    agent_id: str
    name: str
    version: str
    description: str
    capabilities: List[str]


class ExecutiveReportResponse(BaseModel):
    report_id: str
    job_id: str
    lead_id: Optional[Any] = None
    owner_id: Any
    goal: str
    company_name: str
    executive_summary: str
    opportunity_score: int
    sales_playbook: Dict[str, Any]
    top_pain_points: List[str]
    winning_value_proposition: str
    key_differentiators: List[str]
    risk_assessment: List[Dict[str, Any]]
    recommended_actions: List[Dict[str, Any]]
    execution_checklist: List[Dict[str, Any]]
    best_outreach_channel: str
    estimated_deal_size: str
    estimated_close_timeline: str
    overall_confidence: int
    data_quality_notes: str
    research_section: Dict[str, Any]
    memory_section: Dict[str, Any]
    strategy_section: Dict[str, Any]
    outreach_section: Dict[str, Any]
    review_section: Dict[str, Any]
    created_at: datetime

    @field_validator("owner_id", "lead_id", mode="before")
    @classmethod
    def convert_objectid_to_str(cls, v: Any) -> Optional[str]:
        if v is not None:
            return str(v)
        return None

