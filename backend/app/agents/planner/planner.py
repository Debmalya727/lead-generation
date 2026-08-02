"""
Planner Engine for Enterprise Agent Runtime.

Decomposes natural language goals into structured DAG ExecutionPlans.
Does NOT execute tasks. Planner only constructs execution plans.
"""
import uuid
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from app.ai.providers.factory import get_llm_provider
from app.agents.registry.registry import AgentRegistry
from app.agents.planner.task_graph import DAGGraphManager
from app.agents.prompts.planner_prompts import PLANNER_SYSTEM_PROMPT, PLANNER_USER_PROMPT
from app.database.mongodb.collections.agent_runtime import ExecutionPlan, ExecutionTask

logger = logging.getLogger("backend.agents.planner")


class PlannerEngine:
    """Planner constructing DAG ExecutionPlans from natural language goals."""

    def __init__(self):
        self.llm_provider = get_llm_provider("planner")

    async def create_plan(self, goal: str, lead_id: Optional[str] = None) -> ExecutionPlan:
        """Construct DAG ExecutionPlan for natural language goal."""
        logger.info(f"PlannerEngine constructing DAG ExecutionPlan for goal='{goal[:50]}...'")

        plan_id = f"plan_{uuid.uuid4().hex[:12]}"
        registered_agents = AgentRegistry.list_agents()

        cap_lines = [f"- Agent '{a['name']}' (ID: '{a['agent_id']}'): {', '.join(a['capabilities'])}" for a in registered_agents]
        cap_text = "\n".join(cap_lines) if cap_lines else "- Agent 'runtime_diagnostic_agent': General execution capabilities"

        user_prompt = PLANNER_USER_PROMPT.format(
            goal=goal,
            capabilities_text=cap_text,
        )

        try:
            raw_response = await self.llm_provider.complete(
                prompt=user_prompt,
                system_prompt=PLANNER_SYSTEM_PROMPT,
            )

            cleaned_text = raw_response.strip()
            if cleaned_text.startswith("```json"):
                cleaned_text = cleaned_text[7:]
            if cleaned_text.endswith("```"):
                cleaned_text = cleaned_text[:-3]

            parsed = json.loads(cleaned_text.strip())
            task_list_data = parsed.get("tasks", [])

            tasks: List[ExecutionTask] = []
            for item in task_list_data:
                # Ensure valid target agent name
                agent_name = item.get("agent_name", "runtime_diagnostic_agent")
                if not AgentRegistry.validate(agent_name):
                    agent_name = "runtime_diagnostic_agent"

                tasks.append(ExecutionTask(
                    task_id=item.get("task_id", f"task_{len(tasks)+1:02d}"),
                    name=item.get("name", f"Execution Node {len(tasks)+1}"),
                    agent_name=agent_name,
                    description=item.get("description", "Execute task node"),
                    dependencies=item.get("dependencies", []),
                    priority=item.get("priority", 1),
                    parallelizable=item.get("parallelizable", True),
                    approval_required=item.get("approval_required", False),
                    status="pending",
                ))

            # Detect circular dependencies
            if DAGGraphManager.detect_cycles(tasks):
                logger.warning("Circular dependency detected in LLM generated DAG plan. Resetting dependencies to linear sequence.")
                for idx, t in enumerate(tasks):
                    t.dependencies = [tasks[idx-1].task_id] if idx > 0 else []

            # If no tasks parsed, create fallback DAG task graph
            if not tasks:
                tasks = self._build_fallback_tasks(goal)

        except Exception as e:
            logger.warning(f"Fallback plan generation triggered due to LLM parsing exception: {str(e)}")
            tasks = self._build_fallback_tasks(goal)

        # Construct adjacency graph JSON
        graph_json = {
            "nodes": [{"id": t.task_id, "label": t.name, "agent": t.agent_name, "status": t.status} for t in tasks],
            "edges": [{"source": dep, "target": t.task_id} for t in tasks for dep in t.dependencies],
        }

        plan = ExecutionPlan(
            plan_id=plan_id,
            goal=goal,
            tasks=tasks,
            task_graph_json=graph_json,
            created_at=datetime.now(timezone.utc),
        )

        logger.info(f"Successfully constructed DAG ExecutionPlan '{plan_id}' with {len(tasks)} task nodes.")
        return plan

    def _build_fallback_tasks(self, goal: str) -> List[ExecutionTask]:
        """Construct fallback DAG task graph."""
        return [
            ExecutionTask(
                task_id="task_01_init",
                name="Initialize Operations & Context",
                agent_name="runtime_diagnostic_agent",
                description=f"Initialize workspace resources for goal: {goal}",
                dependencies=[],
                priority=1,
                parallelizable=True,
                approval_required=False,
                status="pending",
            ),
            ExecutionTask(
                task_id="task_02_execute",
                name="Execute Core Goal Tasks",
                agent_name="runtime_diagnostic_agent",
                description=f"Execute core actions to achieve goal: {goal}",
                dependencies=["task_01_init"],
                priority=2,
                parallelizable=True,
                approval_required=False,
                status="pending",
            ),
            ExecutionTask(
                task_id="task_03_consolidate",
                name="Consolidate Results & Artifacts",
                agent_name="runtime_diagnostic_agent",
                description="Synthesize outputs and finalize execution job",
                dependencies=["task_02_execute"],
                priority=3,
                parallelizable=True,
                approval_required=False,
                status="pending",
            ),
        ]
