"""
Phase 12.7B REST API Router Extension.
Adds endpoints for: Policies, Capabilities, Sessions, Prompt Registry,
Benchmarks, Guardrails, Evaluation, and Memory Manager.
"""
import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks, status
from pydantic import BaseModel, Field

from app.ai.policies.policy_engine import policy_engine
from app.ai.policies.policy_registry import policy_registry
from app.ai.capabilities.capability_registry import capability_registry_manager
from app.ai.capabilities.capability_router import capability_router
from app.ai.sessions.session_manager import session_manager
from app.ai.prompt_registry.registry import prompt_registry_manager
from app.ai.benchmarks.benchmark_registry import benchmark_registry, benchmark_runner
from app.ai.guardrails.guardrail_engine import guardrail_engine
from app.ai.evaluation.evaluation_engine import evaluation_engine
from app.ai.memory.memory_manager import memory_manager

logger = logging.getLogger("backend.ai.routers.extended")

router = APIRouter(prefix="/ai", tags=["AI Gateway Extended (12.7B)"])


# ─── Request Schemas ───────────────────────────────────────────────────────────

class CapabilityRouteRequest(BaseModel):
    capability: str = Field(..., description="Capability identifier: reasoning | vision | chat | etc.")
    prompt: str = Field(...)
    system_prompt: Optional[str] = Field("")
    user_id: Optional[str] = None
    org_id: Optional[str] = None
    workflow_id: Optional[str] = None
    conversation_id: Optional[str] = None
    agent_id: Optional[str] = None
    bypass_cache: bool = False
    guardrail_config: Optional[Dict[str, Any]] = None


class CreatePolicyRequest(BaseModel):
    policy_id: str
    name: str
    capability: str
    provider: str
    model: str
    priority: int = 100
    conditions: Optional[Dict[str, Any]] = None
    org_id: Optional[str] = None
    description: Optional[str] = None


class CreatePromptRequest(BaseModel):
    name: str
    user_prompt_template: str
    category: str = "conversation"
    system_prompt: Optional[str] = None
    variables: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    description: Optional[str] = None
    created_by: str = "system"


class PromptTransitionRequest(BaseModel):
    registry_id: str
    action: str = Field(..., description="submit_review | approve | reject | promote | deprecate | archive")
    performed_by: str = "system"
    comments: Optional[str] = None


class CreateBenchmarkRequest(BaseModel):
    name: str
    test_prompts: List[str]
    target_providers: List[str]
    target_models: List[str]
    description: Optional[str] = None


class RunBenchmarkRequest(BaseModel):
    benchmark_id: str


class RunEvaluationRequest(BaseModel):
    name: str
    test_prompt: str
    target_models: List[str]
    system_prompt: Optional[str] = None
    initiated_by: str = "system"


class ValidateGuardrailRequest(BaseModel):
    response_text: str
    config: Optional[Dict[str, Any]] = None


class StoreArtifactRequest(BaseModel):
    artifact_type: str
    content: Dict[str, Any]
    workflow_id: Optional[str] = None
    session_id: Optional[str] = None
    conversation_id: Optional[str] = None
    agent_id: Optional[str] = None
    tags: Optional[List[str]] = None


# ─── Capabilities ──────────────────────────────────────────────────────────────

@router.get("/capabilities")
async def list_capabilities():
    """List all registered AI capabilities with default routing."""
    await capability_registry_manager.seed()
    return capability_registry_manager.list_all()


@router.post("/capabilities/route")
async def route_by_capability(request: CapabilityRouteRequest):
    """
    Route a prompt through capability-based policy resolution.
    Returns response with policy metadata and guardrail results.
    """
    try:
        result = await capability_router.route(
            capability=request.capability,
            prompt=request.prompt,
            system_prompt=request.system_prompt or "",
            user_id=request.user_id,
            org_id=request.org_id,
            workflow_id=request.workflow_id,
            conversation_id=request.conversation_id,
            agent_id=request.agent_id,
            bypass_cache=request.bypass_cache,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── Policy Engine ─────────────────────────────────────────────────────────────

@router.get("/policies")
async def list_policies():
    """List all AI routing policies."""
    await policy_engine.initialize()
    docs = await policy_registry.list_all()
    return [d.model_dump() for d in docs]


@router.post("/policies")
async def create_policy(request: CreatePolicyRequest):
    """Create a new AI routing policy."""
    try:
        doc = await policy_registry.create(
            policy_id=request.policy_id,
            name=request.name,
            capability=request.capability,
            provider=request.provider,
            model=request.model,
            priority=request.priority,
            conditions=request.conditions,
            org_id=request.org_id,
            description=request.description,
        )
        return doc.model_dump()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/policies/resolve")
async def resolve_capability(
    capability: str = Query(...),
    org_id: Optional[str] = Query(None),
    user_tier: Optional[str] = Query(None),
):
    """Resolve which provider/model would be selected for a given capability."""
    await policy_engine.initialize()
    context = {}
    if org_id:
        context["org_id"] = org_id
    if user_tier:
        context["user_tier"] = user_tier
    resolution = await policy_engine.resolve(capability, context)
    return resolution.model_dump()


# ─── Sessions ─────────────────────────────────────────────────────────────────

@router.get("/sessions")
async def list_sessions(
    user_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
):
    """List recent AI sessions with optional filters."""
    from app.database.mongodb.collections.ai_gateway_extended import AISessionDocument
    query = AISessionDocument.find_all()
    docs = await query.sort("-started_at").limit(limit).to_list()
    if user_id:
        docs = [d for d in docs if d.user_id == user_id]
    if status:
        docs = [d for d in docs if d.status == status]
    return [d.model_dump() for d in docs]


@router.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """Get a specific session by ID."""
    doc = await session_manager.get_session(session_id)
    if not doc:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")
    return doc.model_dump()


# ─── Prompt Registry ──────────────────────────────────────────────────────────

@router.get("/prompts/registry")
async def list_prompt_registry(
    status: Optional[str] = Query(None, description="draft | review | approved | production | deprecated | archived"),
    category: Optional[str] = Query(None),
):
    """List prompt registry entries with lifecycle status."""
    docs = await prompt_registry_manager.list_all(status=status, category=category)
    return [d.model_dump() for d in docs]


@router.post("/prompts/registry")
async def create_prompt_registry_entry(request: CreatePromptRequest):
    """Create a new prompt registry entry (starts in Draft status)."""
    try:
        doc = await prompt_registry_manager.create(
            name=request.name,
            user_prompt_template=request.user_prompt_template,
            category=request.category,
            system_prompt=request.system_prompt,
            variables=request.variables,
            tags=request.tags,
            description=request.description,
            created_by=request.created_by,
        )
        return doc.model_dump()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/prompts/registry/transition")
async def transition_prompt(request: PromptTransitionRequest):
    """Transition a prompt through its lifecycle (submit → approve → promote → deprecate → archive)."""
    try:
        doc = await prompt_registry_manager.transition(
            registry_id=request.registry_id,
            action=request.action,
            performed_by=request.performed_by,
            comments=request.comments,
        )
        return doc.model_dump()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/prompts/registry/{registry_id}/history")
async def get_prompt_history(registry_id: str):
    """Get approval/lifecycle event history for a prompt."""
    history = await prompt_registry_manager.get_history(registry_id)
    return [h.model_dump() for h in history]


# ─── Benchmarks ───────────────────────────────────────────────────────────────

@router.get("/benchmarks")
async def list_benchmarks():
    """List all benchmark suite definitions."""
    docs = await benchmark_registry.list_all()
    return [d.model_dump() for d in docs]


@router.post("/benchmarks")
async def create_benchmark(request: CreateBenchmarkRequest):
    """Create a new benchmark suite."""
    try:
        doc = await benchmark_registry.create(
            name=request.name,
            test_prompts=request.test_prompts,
            target_providers=request.target_providers,
            target_models=request.target_models,
            description=request.description,
        )
        return doc.model_dump()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/benchmarks/run")
async def run_benchmark(request: RunBenchmarkRequest, background_tasks: BackgroundTasks):
    """Trigger a benchmark run (async background execution)."""
    benchmark = await benchmark_registry.get(request.benchmark_id)
    if not benchmark:
        raise HTTPException(status_code=404, detail=f"Benchmark '{request.benchmark_id}' not found.")

    background_tasks.add_task(
        benchmark_runner.run,
        benchmark_id=benchmark.benchmark_id,
        test_prompts=benchmark.test_prompts,
        target_models=benchmark.target_models,
    )
    return {"message": f"Benchmark run triggered for '{benchmark.name}'.", "benchmark_id": benchmark.benchmark_id}


@router.get("/benchmarks/{benchmark_id}/leaderboard")
async def get_benchmark_leaderboard(benchmark_id: str):
    """Get ranked model leaderboard for a benchmark suite."""
    leaderboard = await benchmark_registry.get_leaderboard(benchmark_id)
    return {"benchmark_id": benchmark_id, "leaderboard": leaderboard}


@router.get("/benchmarks/{benchmark_id}/history")
async def get_benchmark_history(benchmark_id: str, limit: int = Query(50)):
    """Get historical run results for a benchmark."""
    history = await benchmark_registry.get_history(benchmark_id=benchmark_id, limit=limit)
    return [h.model_dump() for h in history]


# ─── Guardrails ───────────────────────────────────────────────────────────────

@router.post("/guardrails/validate")
async def validate_response(request: ValidateGuardrailRequest):
    """Run guardrail validation against a response text (synchronous)."""
    result = guardrail_engine.validate(request.response_text, request.config or {})
    return result.model_dump()


@router.get("/guardrails/logs")
async def list_guardrail_logs(
    passed: Optional[bool] = Query(None),
    limit: int = Query(50, ge=1, le=200),
):
    """List guardrail validation logs."""
    from app.database.mongodb.collections.ai_gateway_extended import GuardrailLogDocument
    docs = await GuardrailLogDocument.find_all().sort("-validated_at").limit(limit).to_list()
    if passed is not None:
        docs = [d for d in docs if d.passed == passed]
    return [d.model_dump() for d in docs]


# ─── Evaluation ───────────────────────────────────────────────────────────────

@router.get("/evaluations")
async def list_evaluations(limit: int = Query(20)):
    """List recent evaluation runs."""
    runs = await evaluation_engine.get_runs(limit=limit)
    return [r.model_dump() for r in runs]


@router.post("/evaluations/run")
async def run_evaluation(request: RunEvaluationRequest, background_tasks: BackgroundTasks):
    """Trigger an AI evaluation comparing multiple models on a single prompt (async)."""
    run_id = f"eval_pending_{request.name[:20].replace(' ', '_')}"
    background_tasks.add_task(
        evaluation_engine.run_evaluation,
        name=request.name,
        test_prompt=request.test_prompt,
        target_models=request.target_models,
        system_prompt=request.system_prompt,
        initiated_by=request.initiated_by,
    )
    return {
        "message": f"Evaluation '{request.name}' triggered across {len(request.target_models)} models.",
        "target_models": request.target_models,
    }


@router.get("/evaluations/{run_id}/scores")
async def get_evaluation_scores(run_id: str):
    """Get ranked scores for a specific evaluation run."""
    scores = await evaluation_engine.get_run_scores(run_id)
    return [s.model_dump() for s in scores]


# ─── Memory ───────────────────────────────────────────────────────────────────

@router.get("/memory")
async def list_memory(
    user_id: Optional[str] = Query(None),
    workflow_id: Optional[str] = Query(None),
    session_id: Optional[str] = Query(None),
    limit: int = Query(20),
):
    """Search AI memory records by context identifiers."""
    docs = await memory_manager.search_by_context(
        user_id=user_id,
        workflow_id=workflow_id,
        session_id=session_id,
        limit=limit,
    )
    return [d.model_dump() for d in docs]


@router.get("/memory/artifacts")
async def list_artifacts(
    workflow_id: Optional[str] = Query(None),
    artifact_type: Optional[str] = Query(None),
    limit: int = Query(50),
):
    """List workflow artifacts stored in AI memory."""
    docs = await memory_manager.list_artifacts(
        workflow_id=workflow_id,
        artifact_type=artifact_type,
        limit=limit,
    )
    return [d.model_dump() for d in docs]


@router.post("/memory/artifacts")
async def store_artifact(request: StoreArtifactRequest):
    """Store a new workflow artifact in AI memory."""
    try:
        doc = await memory_manager.store_artifact(
            artifact_type=request.artifact_type,
            content=request.content,
            workflow_id=request.workflow_id,
            session_id=request.session_id,
            conversation_id=request.conversation_id,
            agent_id=request.agent_id,
            tags=request.tags,
        )
        return doc.model_dump()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/memory/artifacts/{artifact_id}")
async def get_artifact(artifact_id: str):
    """Retrieve a specific workflow artifact by ID."""
    doc = await memory_manager.get_artifact(artifact_id)
    if not doc:
        raise HTTPException(status_code=404, detail=f"Artifact '{artifact_id}' not found.")
    return doc.model_dump()
