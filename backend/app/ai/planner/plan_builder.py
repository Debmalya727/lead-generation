"""
AI Execution Planner — PlanBuilder constructing AIExecutionPlan objects.
"""
import uuid
import time
from typing import List, Dict, Any

from app.ai.planner.schemas import AIExecutionPlan, TaskStepSpec


class PlanBuilder:
    """Constructs AIExecutionPlan objects from decomposed steps and strategy."""

    def build_plan(
        self,
        prompt: str,
        steps: List[TaskStepSpec],
        strategy: str = "sequential",
    ) -> AIExecutionPlan:
        plan_id = f"plan_{uuid.uuid4().hex[:12]}"
        required_capabilities = list(set(s.capability for s in steps if s.capability))
        execution_order = [s.step_id for s in steps]

        return AIExecutionPlan(
            plan_id=plan_id,
            prompt=prompt,
            strategy=strategy,
            required_capabilities=required_capabilities,
            steps=steps,
            execution_order=execution_order,
            created_at_ts=time.time(),
        )


plan_builder = PlanBuilder()
