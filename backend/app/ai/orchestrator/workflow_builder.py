"""
AI Workflow Orchestrator — WorkflowBuilder for programmatic fluent creation of workflow specifications.
"""
from typing import Dict, List, Any, Optional


class WorkflowBuilder:
    """Fluent builder for programmatically creating AI workflows."""

    def __init__(self, workflow_id: str, name: str):
        self.workflow_id = workflow_id
        self.name = name
        self._nodes: List[Dict[str, Any]] = []
        self._edges: List[Dict[str, Any]] = []
        self._initial_node_id: Optional[str] = None

    def add_node(
        self,
        node_id: str,
        name: str,
        node_type: str = "GenerationNode",
        config: Optional[Dict[str, Any]] = None,
        timeout_seconds: float = 30.0,
        max_retries: int = 3,
        fallback_node_id: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """Add node to workflow."""
        if not self._initial_node_id:
            self._initial_node_id = node_id

        self._nodes.append({
            "node_id": node_id,
            "name": name,
            "node_type": node_type,
            "config": config or {},
            "timeout_seconds": timeout_seconds,
            "max_retries": max_retries,
            "fallback_node_id": fallback_node_id,
        })
        return self

    def add_edge(
        self,
        from_node_id: str,
        to_node_id: str,
        condition_expression: Optional[str] = None,
    ) -> "WorkflowBuilder":
        """Add directed edge to workflow."""
        self._edges.append({
            "from_node_id": from_node_id,
            "to_node_id": to_node_id,
            "condition_expression": condition_expression,
        })
        return self

    def build(self) -> Dict[str, Any]:
        """Construct workflow specification dictionary."""
        return {
            "workflow_id": self.workflow_id,
            "name": self.name,
            "initial_node_id": self._initial_node_id,
            "nodes": self._nodes,
            "edges": self._edges,
        }

