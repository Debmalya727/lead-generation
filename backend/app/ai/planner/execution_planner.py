"""
AI Execution Planner — ExecutionPlanner master orchestrator.
"""
from typing import Dict, Any, Optional
import logging

from app.ai.planner.schemas import AIExecutionPlan
from app.ai.planner.task_decomposer import task_decomposer
from app.ai.planner.strategy_selector import strategy_selector
from app.ai.planner.plan_builder import plan_builder

logger = logging.getLogger("backend.ai.planner.orchestrator")


class ExecutionPlanner:
    """Master planner determining required capabilities, execution order, and strategies."""

    async def create_plan(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> AIExecutionPlan:
        """Decompose prompt, select strategy, and return AIExecutionPlan."""
        context = context or {}

        # 1. Decompose prompt into steps
        steps = task_decomposer.decompose(prompt)

        # 2. Select strategy
        strategy = strategy_selector.select_strategy(context)

        # 3. Build plan
        plan = plan_builder.build_plan(prompt, steps, strategy)

        logger.info(
            f"ExecutionPlanner: Created plan '{plan.plan_id}' with {len(steps)} steps "
            f"and strategy '{strategy}'."
        )

        # Store in MongoDB (non-blocking)
        try:
            from app.database.mongodb.collections.ai_orchestrator import AIExecutionPlanDocument
            doc = AIExecutionPlanDocument(
                plan_id=plan.plan_id,
                workflow_id=context.get("workflow_id"),
                prompt=prompt,
                required_capabilities=plan.required_capabilities,
                execution_order=plan.execution_order,
                strategy=strategy,
                node_plans=[s.model_dump() for s in steps],
            )
            await doc.insert()
        except Exception as e:
            logger.debug(f"ExecutionPlanner: Plan persistence skipped: {e}")

        return plan


execution_planner = ExecutionPlanner()
