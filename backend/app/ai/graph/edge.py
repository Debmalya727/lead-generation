"""
AI Graph Engine — GraphEdge representing directed connections between nodes.
Supports conditional expression evaluation.
"""
from typing import Any, Dict, Optional
import logging

logger = logging.getLogger("backend.ai.graph.edge")


class GraphEdge:
    """Directed edge connecting a source node to a target node in a DAG."""

    def __init__(
        self,
        edge_id: str,
        from_node_id: str,
        to_node_id: str,
        condition_expression: Optional[str] = None,
    ):
        self.edge_id = edge_id
        self.from_node_id = from_node_id
        self.to_node_id = to_node_id
        self.condition_expression = condition_expression

    def evaluate_condition(self, source_output: Dict[str, Any]) -> bool:
        """
        Evaluates condition_expression against source node output data.
        Returns True if condition passes or no condition expression is defined.
        """
        if not self.condition_expression:
            return True

        expr = self.condition_expression.strip()
        try:
            # Simple expression evaluation (e.g., "success == True", "guardrail_passed == True")
            # Safe evaluation environment with source_output keys in scope
            scope = dict(source_output)
            # Add common convenience aliases
            scope["success"] = source_output.get("success", True)
            return bool(eval(expr, {"__builtins__": None}, scope))
        except Exception as e:
            logger.warning(f"GraphEdge [{self.edge_id}] condition evaluation failed: {e}. Defaulting to False.")
            return False
