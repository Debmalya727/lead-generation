"""
Beanie MongoDB Document collections for Phase 11 — Milestone 1: Enterprise Agent Runtime.

Collections:
- ExecutionTask (Embedded or referenced task node in DAG Task Graph)
- ExecutionPlan (DAG Execution Plan)
- AgentEvent (State transition event emitted during execution)
- AgentJob (Master orchestration job tracking agent execution lifecycle)
"""
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from beanie import Document, PydanticObjectId
from pydantic import BaseModel, Field


class ExecutionTask(BaseModel):
    task_id: str = Field(..., description="Unique task identifier in DAG graph (e.g. task_01_research)")
    name: str = Field(..., description="Human readable task name")
    agent_name: str = Field(..., description="Name of registered agent responsible for executing task")
    description: str = Field(..., description="Detailed task goal and instructions")
    
    dependencies: List[str] = Field(default_factory=list, description="IDs of tasks that must complete before this task starts")
    priority: int = Field(1, ge=1, le=10)
    retry_count: int = Field(0, ge=0)
    max_retries: int = Field(3, ge=0)
    timeout_seconds: int = Field(300, ge=10)
    parallelizable: bool = Field(True)
    approval_required: bool = Field(False, description="Flag indicating human approval is required before execution")

    status: str = Field("pending", description="pending | running | completed | failed | cancelled | paused_for_approval")
    inputs: Dict[str, Any] = Field(default_factory=dict)
    outputs: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None
    execution_time_seconds: float = Field(0.0, ge=0.0)

    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class ExecutionPlan(BaseModel):
    plan_id: str = Field(..., description="Unique execution plan ID")
    goal: str = Field(..., description="Natural language goal input")
    tasks: List[ExecutionTask] = Field(default_factory=list, description="DAG Task nodes")
    task_graph_json: Dict[str, Any] = Field(default_factory=dict, description="Topology graph adjacency structure")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AgentEvent(Document):
    event_id: str = Field(..., description="Unique event identifier")
    job_id: str = Field(..., description="Associated AgentJob ID")
    owner_id: PydanticObjectId

    event_type: str = Field(
        ...,
        description="task_started | task_finished | task_failed | agent_started | agent_finished | plan_created | plan_updated | execution_finished | task_approval_required | job_failed"
    )
    source_agent: str = Field("AgentRuntime")
    task_id: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "agent_events"
        indexes = [
            [("owner_id", 1), ("job_id", 1)],
            [("job_id", 1), ("timestamp", -1)],
            [("event_type", 1)],
        ]


class AgentJob(Document):
    job_id: str = Field(..., description="Unique orchestration job ID")
    goal: str = Field(..., description="User submitted natural language goal")
    lead_id: Optional[PydanticObjectId] = None
    owner_id: PydanticObjectId

    status: str = Field("pending", description="pending | running | completed | failed | cancelled | paused_for_approval")
    progress: float = Field(0.0, ge=0.0, le=100.0)
    
    plan: Optional[ExecutionPlan] = None
    current_task_id: Optional[str] = None
    execution_stats: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None

    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "agent_jobs"
        indexes = [
            [("owner_id", 1), ("lead_id", 1)],
            [("owner_id", 1), ("status", 1)],
            [("job_id", 1)],
            [("created_at", -1)],
        ]
