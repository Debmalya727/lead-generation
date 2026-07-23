"""
Phase 12.7C REST API Router — AI Orchestration Platform Endpoints.
Endpoints:
- GET /api/v1/ai/workflows
- POST /api/v1/ai/workflows
- POST /api/v1/ai/workflows/run
- GET /api/v1/ai/workflow/{id}
- GET /api/v1/ai/pipelines
- GET /api/v1/ai/executions
- GET /api/v1/ai/provider-health
- GET /api/v1/ai/queues
- POST /api/v1/ai/queues/retry
"""
import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks, status
from pydantic import BaseModel, Field

from app.ai.orchestrator.workflow_orchestrator import ai_workflow_orchestrator
from app.ai.orchestrator.workflow_registry import workflow_registry
from app.ai.orchestrator.schemas import WorkflowRunRequest, WorkflowCreateRequest
from app.ai.resilience.health_tracker import health_tracker
from app.ai.resilience.circuit_breaker import circuit_breaker
from app.ai.queue.queue_manager import queue_manager
from app.database.mongodb.collections.ai_orchestrator import (
    AIWorkflowDocument,
    AIWorkflowRunDocument,
    AIDeadLetterQueueDocument,
)

logger = logging.getLogger("backend.ai.routers.orchestrator")

router = APIRouter(prefix="/ai", tags=["AI Orchestration Platform (12.7C)"])


class RetryDlqRequest(BaseModel):
    dlq_id: str = Field(..., description="Target Dead Letter Queue item ID to retry")


# ─── 1. Workflows ──────────────────────────────────────────────────────────────

@router.get("/workflows")
async def list_workflows():
    """List all registered custom workflows."""
    docs = await workflow_registry.list_workflows()
    return [d.model_dump() for d in docs]


@router.post("/workflows")
async def create_workflow(request: WorkflowCreateRequest):
    """Register a new custom AI workflow definition."""
    try:
        doc = await workflow_registry.register_workflow(
            workflow_id=request.workflow_id,
            name=request.name,
            initial_node_id=request.initial_node_id,
            nodes=request.nodes,
            edges=request.edges,
            description=request.description,
            category=request.category,
        )
        return doc.model_dump()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/workflows/run")
async def run_workflow(request: WorkflowRunRequest):
    """
    Execute an AI workflow or pipeline template synchronously.
    Returns complete run summary with outputs and node execution metrics.
    """
    try:
        await workflow_registry.seed()
        result = await ai_workflow_orchestrator.execute_workflow(
            workflow_id=request.workflow_id,
            template_id=request.template_id,
            inputs=request.inputs,
            priority=request.priority,
            user_id=request.user_id,
            org_id=request.org_id,
            session_id=request.session_id,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workflow/{id}")
async def get_workflow(id: str):
    """Fetch workflow specification by ID or template_id."""
    await workflow_registry.seed()
    spec = await workflow_registry.get_workflow_spec(id)
    if not spec:
        raise HTTPException(status_code=404, detail=f"Workflow or template '{id}' not found.")
    return spec


# ─── 2. Pipelines & Executions ────────────────────────────────────────────────

@router.get("/pipelines")
async def list_pipeline_templates():
    """List 10 built-in pipeline templates."""
    await workflow_registry.seed()
    return workflow_registry.list_templates()


@router.get("/executions")
async def list_workflow_executions(
    workflow_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(30, ge=1, le=100),
):
    """List historical workflow run executions."""
    query = AIWorkflowRunDocument.find_all()
    if workflow_id:
        query = AIWorkflowRunDocument.find(AIWorkflowRunDocument.workflow_id == workflow_id)
    if status:
        query = AIWorkflowRunDocument.find(AIWorkflowRunDocument.status == status)

    docs = await query.sort("-started_at").limit(limit).to_list()
    return [d.model_dump() for d in docs]


# ─── 3. Observability, Health & Queues ────────────────────────────────────────

@router.get("/provider-health")
async def get_provider_health():
    """Get real-time provider health metrics and circuit breaker states."""
    providers = ["gemini", "openai", "claude", "openrouter", "ollama", "deepseek"]
    results = []
    for p in providers:
        h = health_tracker.get_health(p)
        st = circuit_breaker.get_state(p)
        h["state"] = st
        results.append(h)
    return results


@router.get("/queues")
async def get_queue_status():
    """Get status and depth metrics for priority queue and dead-letter queue."""
    stats = await queue_manager.get_queue_stats()
    dlq_items = await AIDeadLetterQueueDocument.find_all().sort("-failed_at").limit(20).to_list()
    stats["dlq_items"] = [item.model_dump() for item in dlq_items]
    return stats


@router.post("/queues/retry")
async def retry_dead_letter_item(request: RetryDlqRequest):
    """Retry a task from the dead-letter queue."""
    res = await queue_manager.retry_dlq_item(request.dlq_id)
    if not res:
        raise HTTPException(status_code=404, detail=f"DLQ item '{request.dlq_id}' not found.")
    return {"message": f"Retried DLQ item '{request.dlq_id}'", "new_queue_id": res.queue_id}
