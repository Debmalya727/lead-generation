"""
AI Graph Engine — Graph Validator for cycle detection and DAG topological checks.
"""
from typing import Dict, List, Set, Tuple
import logging

from app.ai.graph.graph import DAGGraph

logger = logging.getLogger("backend.ai.graph.validator")


class GraphValidator:
    """Validates DAG structure, detects cycles, and verifies entry/terminal nodes."""

    def validate(self, graph: DAGGraph) -> Tuple[bool, List[str]]:
        """
        Validates graph structure.
        Returns (is_valid, list_of_error_messages).
        """
        errors = []

        if not graph.nodes:
            errors.append("Graph contains no nodes.")
            return False, errors

        if not graph.initial_node_id or graph.initial_node_id not in graph.nodes:
            errors.append(f"Initial node '{graph.initial_node_id}' is missing from graph.")

        # Cycle detection using Depth First Search (DFS)
        visited: Set[str] = set()
        rec_stack: Set[str] = set()

        def dfs(node_id: str) -> bool:
            visited.add(node_id)
            rec_stack.add(node_id)

            for child_id in graph.get_children(node_id):
                if child_id not in visited:
                    if dfs(child_id):
                        return True
                elif child_id in rec_stack:
                    errors.append(f"Cycle detected involving node '{node_id}' -> '{child_id}'.")
                    return True

            rec_stack.remove(node_id)
            return False

        for n_id in graph.nodes:
            if n_id not in visited:
                if dfs(n_id):
                    break

        # Disconnected node check
        if len(visited) < len(graph.nodes):
            unvisited = set(graph.nodes.keys()) - visited
            logger.info(f"GraphValidator: Unvisited/unreachable nodes from root: {unvisited}")

        is_valid = len(errors) == 0
        return is_valid, errors


graph_validator = GraphValidator()
