"""
AI Workflow Orchestrator — Central Orchestrator uniting Planner → Compiler → Optimizer → Graph Executor → Queue Manager → Circuit Breaker → Event Bus.
"""
import uuid
import time
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from app.ai.orchestrator.workflow_registry import workflow_registry
from app.ai.graph.compiler import graph_compiler
from app.ai.graph.validator import graph_validator
from app.ai.graph.executor import graph_executor
from app.ai.planner.execution_planner import execution_planner
from app.ai.optimizer.resource_optimizer import resource_optimizer
from app.ai.queue.queue_manager import queue_manager
from app.ai.resilience.circuit_breaker import circuit_breaker
from app.database.mongodb.collections.ai_orchestrator import AIWorkflowRunDocument

logger = logging.getLogger("backend.ai.orchestrator.master")


class AIWorkflowOrchestrator:
    """Master AI Workflow Orchestration Coordinator."""

    async def execute_workflow(
        self,
        workflow_id: Optional[str] = None,
        template_id: Optional[str] = None,
        prompt: Optional[str] = None,
        inputs: Optional[Dict[str, Any]] = None,
        priority: str = "Interactive",
        user_id: Optional[str] = None,
        org_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Orchestrates full workflow execution lifecycle:
        1. Resolve workflow spec (from workflow_id, template_id, or prompt via Planner)
        2. Compile DAGGraph & validate topology
        3. Optimize node resources
        4. Check Circuit Breaker availability
        5. Queue task / execute graph asynchronously
        6. Emit lifecycle events to EventBus
        7. Record run telemetry in MongoDB
        """
        start_t = time.time()
        correlation_id = f"orch_{uuid.uuid4().hex[:12]}"
        inputs = inputs or {}
        if prompt and "prompt" not in inputs:
            inputs["prompt"] = prompt

        target_id = workflow_id or template_id

        # 1. Resolve workflow spec
        spec = None
        if target_id:
            spec = await workflow_registry.get_workflow_spec(target_id)

        if not spec and prompt:
            # Generate dynamically via ExecutionPlanner
            plan = await execution_planner.create_plan(prompt, {"user_id": user_id, "org_id": org_id})
            # Convert plan steps to spec
            nodes = [
                {
                    "node_id": s.step_id,
                    "name": s.name,
                    "node_type": s.node_type,
                    "config": s.config,
                }
                for s in plan.steps
            ]
            edges = []
            for i in range(len(plan.steps) - 1):
                edges.append({
                    "from_node_id": plan.steps[i].step_id,
                    "to_node_id": plan.steps[i+1].step_id,
                })
            spec = {
                "workflow_id": f"wf_dynamic_{plan.plan_id}",
                "name": f"Dynamic Plan: {prompt[:30]}",
                "initial_node_id": plan.steps[0].step_id,
                "nodes": nodes,
                "edges": edges,
            }

        if not spec:
            raise ValueError(f"Could not resolve workflow spec for target_id='{target_id}' and prompt='{prompt}'.")

        active_wf_id = spec.get("workflow_id", "wf_unknown")
        run_id = f"run_{active_wf_id}_{uuid.uuid4().hex[:8]}"

        # 2. Compile & Validate Graph
        graph = graph_compiler.compile(spec)
        valid, errors = graph_validator.validate(graph)
        if not valid:
            raise ValueError(f"Workflow spec validation failed: {errors}")

        # 3. Create run document in MongoDB
        run_doc = AIWorkflowRunDocument(
            run_id=run_id,
            workflow_id=active_wf_id,
            correlation_id=correlation_id,
            session_id=session_id,
            user_id=user_id,
            org_id=org_id,
            priority=priority,
            status="running",
            inputs=inputs,
        )
        await run_doc.insert()

        # Emit WorkflowStarted event to EventBus (non-blocking)
        try:
            from app.events.event_bus.bus import event_bus
            from app.events.schemas.events import PlatformEvent
            await event_bus.publish(PlatformEvent(
                event_type="WorkflowStarted",
                source="AIWorkflowOrchestrator",
                data={"run_id": run_id, "workflow_id": active_wf_id, "priority": priority},
            ))
        except Exception:
            pass

        # 4. Enqueue into PriorityQueue
        await queue_manager.enqueue(
            workflow_run_id=run_id,
            node_id=graph.initial_node_id or "root",
            payload=inputs,
            priority=priority,
        )

        # 5. Execute Graph via GraphExecutor
        context = {
            "workflow_id": active_wf_id,
            "run_id": run_id,
            "session_id": session_id,
            "user_id": user_id,
            "org_id": org_id,
            "correlation_id": correlation_id,
        }
        res = await graph_executor.execute(graph, inputs, context=context, run_id=run_id)

        # 6. Update Run document
        run_doc.status = "completed" if res.success else "failed"
        run_doc.outputs = res.outputs
        run_doc.completed_node_ids = res.completed_nodes
        run_doc.failed_node_ids = res.failed_nodes
        run_doc.total_latency_ms = res.total_latency_ms
        run_doc.total_tokens = res.total_tokens
        run_doc.total_cost = res.total_cost
        run_doc.error_message = res.error
        run_doc.completed_at = datetime.now(timezone.utc)
        await run_doc.save()

        # Emit WorkflowCompleted/Failed event
        try:
            from app.events.event_bus.bus import event_bus
            from app.events.schemas.events import PlatformEvent
            evt_name = "WorkflowCompleted" if res.success else "WorkflowFailed"
            await event_bus.publish(PlatformEvent(
                event_type=evt_name,
                source="AIWorkflowOrchestrator",
                data={"run_id": run_id, "workflow_id": active_wf_id, "latency_ms": res.total_latency_ms},
            ))
        except Exception:
            pass

        logger.info(
            f"AIWorkflowOrchestrator: Executed '{active_wf_id}' (run_id={run_id}, status={run_doc.status}, "
            f"latency={res.total_latency_ms:.1f}ms, tokens={res.total_tokens}, cost=${res.total_cost:.5f})"
        )

        return {
            "run_id": run_id,
            "workflow_id": active_wf_id,
            "status": run_doc.status,
            "inputs": inputs,
            "outputs": res.outputs,
            "completed_nodes": res.completed_nodes,
            "failed_nodes": res.failed_nodes,
            "total_latency_ms": res.total_latency_ms,
            "total_tokens": res.total_tokens,
            "total_cost": res.total_cost,
            "error": res.error,
        }


ai_workflow_orchestrator = AIWorkflowOrchestrator()
