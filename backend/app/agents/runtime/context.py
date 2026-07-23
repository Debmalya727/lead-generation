"""
Immutable Execution Context passed to Agents during lifecycle execution.
"""
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional


@dataclass(frozen=True)
class ExecutionContext:
    """Immutable data context holding execution scope, parameters, and metadata."""
    job_id: str
    plan_id: str
    owner_id: str
    goal: str
    lead_id: Optional[str] = None
    correlation_id: Optional[str] = None
    task_id: Optional[str] = None
    memory_references: Dict[str, Any] = field(default_factory=dict)
    inputs: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
