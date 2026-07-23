"""
Directed Acyclic Graph (DAG) Task Graph Structure for Agent Execution Plans.
"""
import logging
from typing import Dict, List, Any, Optional, Set
from pydantic import BaseModel, Field

from app.database.mongodb.collections.agent_runtime import ExecutionTask, ExecutionPlan

logger = logging.getLogger("backend.agents.task_graph")


class TaskGraph:
    """DAG Task Graph representation supporting topological sorting, dependency checks, and ready-node discovery."""

    def __init__(self, tasks: List[ExecutionTask]):
        self.tasks_dict: Dict[str, ExecutionTask] = {t.task_id: t for t in tasks}

    def get_task(self, task_id: str) -> Optional[ExecutionTask]:
        """Fetch task node by ID."""
        return self.tasks_dict.get(task_id)

    def get_ready_tasks(self) -> List[ExecutionTask]:
        """Discover task nodes whose dependencies are all completed and are ready to execute."""
        return DAGGraphManager.get_ready_tasks(list(self.tasks_dict.values()))

    def is_completed(self) -> bool:
        """Check if all task nodes in DAG graph are completed."""
        return all(t.status == "completed" for t in self.tasks_dict.values())

    def is_failed(self) -> bool:
        """Check if any non-optional task node has failed."""
        return any(t.status == "failed" for t in self.tasks_dict.values())

    def is_paused_for_approval(self) -> bool:
        """Check if execution is currently waiting on human approval."""
        return any(t.status == "paused_for_approval" for t in self.tasks_dict.values())


class DAGGraphManager:
    """Manager providing DAG operations for task lists."""

    @staticmethod
    def get_ready_tasks(tasks: List[ExecutionTask]) -> List[ExecutionTask]:
        """Return tasks whose status is 'pending' and all dependencies are 'completed'."""
        completed_ids = {t.task_id for t in tasks if t.status == "completed"}
        ready = []

        for t in tasks:
            if t.status == "pending":
                # Check if all dependencies are in completed_ids
                if all(dep_id in completed_ids for dep_id in t.dependencies):
                    ready.append(t)

        return ready

    @staticmethod
    def detect_cycles(tasks: List[ExecutionTask]) -> bool:
        """Check if task graph contains circular dependency cycles using Kahn's algorithm."""
        in_degree = {t.task_id: len(t.dependencies) for t in tasks}
        adj = {t.task_id: [] for t in tasks}

        for t in tasks:
            for dep in t.dependencies:
                if dep in adj:
                    adj[dep].append(t.task_id)

        queue = [t_id for t_id, deg in in_degree.items() if deg == 0]
        visited_count = 0

        while queue:
            node = queue.pop(0)
            visited_count += 1
            for neighbor in adj.get(node, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        return visited_count < len(tasks)
