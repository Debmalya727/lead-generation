"""
Beanie MongoDB Document collections for Phase 11 — Milestone 4: Autonomous Workflow & Tool Orchestration Engine.

Collections:
- WorkflowTemplateDocument (Pre-built & custom reusable workflow templates)
- WorkflowExecutionDocument (Job-level workflow execution records)
- WorkflowStepDocument (Individual step execution tracking)
- WorkflowCheckpointDocument (Execution state snapshots for resumption & recovery)
- ToolExecutionDocument (Logs of tool invocations, inputs, outputs, & cost tracking)
- WorkflowPolicyDocument (Execution policies, governance rules, and approval constraints)
"""
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from beanie import Document, PydanticObjectId
from pydantic import BaseModel, Field


class WorkflowTemplateDocument(Document):
    """Document storing reusable workflow definitions."""

    template_id: str = Field(..., description="Unique template identifier")
    name: str = Field(..., description="Human-readable template name")
    description: str = Field(..., description="Template detailed description")
    category: str = Field("sales_intelligence", description="sales_discovery | lead_qualification | sales_intelligence | research | outreach | executive_report")
    
    version: int = Field(1, ge=1)
    steps: List[Dict[str, Any]] = Field(default_factory=list, description="Ordered workflow step specifications")
    default_policy: Dict[str, Any] = Field(default_factory=dict, description="Default policy rules")
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "workflow_templates"
        indexes = [
            [("template_id", 1)],
            [("category", 1)],
            [("created_at", -1)],
        ]


class WorkflowExecutionDocument(Document):
    """Document tracking master workflow execution lifecycle."""

    execution_id: str = Field(..., description="Unique workflow execution ID")
    workflow_id: str = Field(..., description="Workflow template or custom ID")
    owner_id: PydanticObjectId
    
    job_id: Optional[str] = Field(None, description="Associated AgentJob ID if linked")
    lead_id: Optional[str] = Field(None, description="Associated Lead ID")
    company_name: Optional[str] = Field(None, description="Target company name")
    
    status: str = Field("pending", description="pending | running | waiting | paused | cancelled | failed | completed | checkpointed")
    progress: float = Field(0.0, ge=0.0, le=100.0)
    
    current_step_id: Optional[str] = None
    execution_stats: Dict[str, Any] = Field(default_factory=dict)
    context_data: Dict[str, Any] = Field(default_factory=dict, description="Global workflow variable memory")
    error_message: Optional[str] = None
    
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "workflow_executions"
        indexes = [
            [("execution_id", 1)],
            [("owner_id", 1), ("status", 1)],
            [("job_id", 1)],
            [("created_at", -1)],
        ]


class WorkflowStepDocument(Document):
    """Document tracking execution of an individual workflow step node."""

    step_execution_id: str = Field(..., description="Unique step execution record ID")
    execution_id: str = Field(..., description="Parent WorkflowExecution ID")
    step_id: str = Field(..., description="Step specification ID (e.g. step_01_research)")
    
    name: str = Field(..., description="Step name")
    step_type: str = Field("tool", description="tool | agent | condition | loop | approval | checkpoint")
    target: str = Field(..., description="Target tool ID or agent ID to invoke")
    
    status: str = Field("pending", description="pending | running | waiting | completed | failed | skipped | paused_for_approval")
    inputs: Dict[str, Any] = Field(default_factory=dict)
    outputs: Dict[str, Any] = Field(default_factory=dict)
    
    execution_time_seconds: float = Field(0.0, ge=0.0)
    retry_count: int = Field(0, ge=0)
    error_message: Optional[str] = None
    
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Settings:
        name = "workflow_steps"
        indexes = [
            [("execution_id", 1), ("step_id", 1)],
            [("execution_id", 1), ("status", 1)],
            [("step_execution_id", 1)],
        ]


class WorkflowCheckpointDocument(Document):
    """Document storing workflow state snapshots for crash recovery & resumption."""

    checkpoint_id: str = Field(..., description="Unique checkpoint snapshot ID")
    execution_id: str = Field(..., description="Associated WorkflowExecution ID")
    step_id: str = Field(..., description="Step ID at which checkpoint was created")
    
    state_snapshot: Dict[str, Any] = Field(default_factory=dict, description="Full state memory snapshot")
    completed_step_ids: List[str] = Field(default_factory=list)
    pending_step_ids: List[str] = Field(default_factory=list)
    
    reason: str = Field("step_complete", description="step_complete | approval_pause | failure_recovery | manual")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "workflow_checkpoints"
        indexes = [
            [("execution_id", 1), ("created_at", -1)],
            [("checkpoint_id", 1)],
        ]


class ToolExecutionDocument(Document):
    """Document logging tool executions, input parameters, output results, & cost metrics."""

    tool_execution_id: str = Field(..., description="Unique tool execution log ID")
    tool_id: str = Field(..., description="Target tool ID")
    execution_id: Optional[str] = Field(None, description="Associated WorkflowExecution ID")
    step_id: Optional[str] = Field(None, description="Associated step ID")
    
    invoker_agent: str = Field("System", description="Agent or System initiating tool execution")
    inputs: Dict[str, Any] = Field(default_factory=dict)
    outputs: Dict[str, Any] = Field(default_factory=dict)
    
    status: str = Field("success", description="success | error | timeout | permission_denied")
    execution_time_seconds: float = Field(0.0, ge=0.0)
    cost_estimate: float = Field(0.0, ge=0.0)
    error_message: Optional[str] = None
    
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "tool_executions"
        indexes = [
            [("tool_id", 1), ("timestamp", -1)],
            [("execution_id", 1)],
            [("tool_execution_id", 1)],
        ]


class WorkflowPolicyDocument(Document):
    """Document storing policy rules and governance constraints."""

    policy_id: str = Field(..., description="Unique policy identifier")
    name: str = Field(..., description="Policy rule name")
    description: str = Field(..., description="Governance policy details")
    
    approval_required: bool = Field(False)
    allowed_tools: List[str] = Field(default_factory=list, description="Whitelist of allowed tool IDs (empty = all allowed)")
    execution_limits: Dict[str, Any] = Field(default_factory=dict, description="Max runtime seconds, max retries, max steps")
    token_budget: int = Field(50000, description="Max token budget per workflow run")
    required_confidence: int = Field(70, ge=0, le=100)
    compliance_rules: List[str] = Field(default_factory=list)
    
    is_active: bool = Field(True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "workflow_policies"
        indexes = [
            [("policy_id", 1)],
            [("is_active", 1)],
        ]
