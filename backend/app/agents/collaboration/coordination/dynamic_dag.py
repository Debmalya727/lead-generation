"""
Dynamic DAG Manager for Multi-Agent Collaboration Engine.

Enables runtime dynamic modification of DAG ExecutionPlans:
- Dynamic task insertion (e.g., triggering a Hiring Specialist when hiring surge is detected)
- Task removal
- Task replacement
- Task pause & resume
"""
import logging
from typing import Optional, Dict, Any

from app.database.mongodb.collections.agent_runtime import ExecutionPlan, ExecutionTask
from app.agents.planner.task_graph import DAGGraphManager

logger = logging.getLogger("backend.agents.collaboration.dynamic_dag")


class DynamicDAGManager:
    """Manager handling dynamic runtime modification of DAG task graphs."""

    @classmethod
    def insert_task(
        cls,
        plan: ExecutionPlan,
        new_task: ExecutionTask,
        after_task_id: Optional[str] = None,
        before_task_id: Optional[str] = None,
    ) -> ExecutionPlan:
        """Dynamically insert a new task node into an active ExecutionPlan."""
        logger.info(f"DynamicDAGManager inserting new task node '{new_task.task_id}' into plan '{plan.plan_id}'")

        # Check duplicate
        if any(t.task_id == new_task.task_id for t in plan.tasks):
            logger.warning(f"Task '{new_task.task_id}' already exists in plan.")
            return plan

        if after_task_id:
            new_task.dependencies = [after_task_id]
            # Rewire any tasks that depended on after_task_id to depend on new_task if desired
            for t in plan.tasks:
                if before_task_id and t.task_id == before_task_id:
                    t.dependencies.append(new_task.task_id)

        plan.tasks.append(new_task)
        cls._rebuild_graph_json(plan)
        return plan

    @classmethod
    def remove_task(cls, plan: ExecutionPlan, task_id: str) -> ExecutionPlan:
        """Remove a task node from the ExecutionPlan and rewire dependencies."""
        logger.info(f"DynamicDAGManager removing task node '{task_id}' from plan '{plan.plan_id}'")
        target_task = next((t for t in plan.tasks if t.task_id == task_id), None)
        if not target_task:
            return plan

        target_deps = target_task.dependencies

        # Remove task
        plan.tasks = [t for t in plan.tasks if t.task_id != task_id]

        # Rewire tasks that depended on target_task to inherit target_task's dependencies
        for t in plan.tasks:
            if task_id in t.dependencies:
                t.dependencies.remove(task_id)
                for dep in target_deps:
                    if dep not in t.dependencies:
                        t.dependencies.append(dep)

        cls._rebuild_graph_json(plan)
        return plan

    @classmethod
    def replace_task(cls, plan: ExecutionPlan, target_task_id: str, new_task: ExecutionTask) -> ExecutionPlan:
        """Replace an existing task node with a new task node."""
        logger.info(f"DynamicDAGManager replacing task '{target_task_id}' with '{new_task.task_id}'")
        for idx, t in enumerate(plan.tasks):
            if t.task_id == target_task_id:
                new_task.dependencies = t.dependencies
                plan.tasks[idx] = new_task
                break

        # Update references in other tasks
        for t in plan.tasks:
            if target_task_id in t.dependencies:
                t.dependencies.remove(target_task_id)
                t.dependencies.append(new_task.task_id)

        cls._rebuild_graph_json(plan)
        return plan

    @classmethod
    def pause_task(cls, plan: ExecutionPlan, task_id: str) -> ExecutionPlan:
        """Pause execution of a task node."""
        for t in plan.tasks:
            if t.task_id == task_id:
                t.status = "paused_for_approval"
                t.approval_required = True
                break
        cls._rebuild_graph_json(plan)
        return plan

    @classmethod
    def resume_task(cls, plan: ExecutionPlan, task_id: str) -> ExecutionPlan:
        """Resume execution of a paused task node."""
        for t in plan.tasks:
            if t.task_id == task_id:
                t.status = "pending"
                t.approval_required = False
                break
        cls._rebuild_graph_json(plan)
        return plan

    @classmethod
    def _rebuild_graph_json(cls, plan: ExecutionPlan) -> None:
        """Reconstruct task_graph_json topology dictionary."""
        plan.task_graph_json = {
            "nodes": [
                {
                    "id": t.task_id,
                    "label": t.name,
                    "agent": t.agent_name,
                    "status": t.status,
                    "priority": t.priority,
                }
                for t in plan.tasks
            ],
            "edges": [
                {"source": dep, "target": t.task_id}
                for t in plan.tasks
                for dep in t.dependencies
            ],
            "pipeline_type": plan.task_graph_json.get("pipeline_type", "dynamic"),
        }
