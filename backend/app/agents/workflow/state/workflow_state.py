"""
WorkflowState for Phase 11 — Milestone 4: Autonomous Workflow & Tool Orchestration Engine.
"""
from enum import Enum


class WorkflowStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    WAITING = "waiting"
    PAUSED = "paused"
    CANCELLED = "cancelled"
    FAILED = "failed"
    COMPLETED = "completed"
    CHECKPOINTED = "checkpointed"
