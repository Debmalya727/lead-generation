"""
AI Workflow Orchestrator — Pydantic schemas for Phase 12.7C.
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class WorkflowRunRequest(BaseModel):
    workflow_id: Optional[str] = Field(None, description="Target workflow ID (or template_id)")
    template_id: Optional[str] = Field(None, description="Target pipeline template ID")
    inputs: Dict[str, Any] = Field(default_factory=dict, description="Input parameters dictionary")
    priority: str = Field("Interactive", description="Critical | Enterprise | Realtime | Interactive | Background | Low")
    user_id: Optional[str] = None
    org_id: Optional[str] = None
    session_id: Optional[str] = None


class WorkflowCreateRequest(BaseModel):
    workflow_id: str
    name: str
    description: Optional[str] = None
    category: str = "custom"
    initial_node_id: str
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
