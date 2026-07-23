"""
AI Graph Engine — GraphScheduler for topological ordering and identifying parallelizable node clusters.
"""
from typing import Dict, List, Set
from collections import deque
import logging

from app.ai.graph.graph import DAGGraph

logger = logging.getLogger("backend.ai.graph.scheduler")


class GraphScheduler:
    """Determines topological execution order and identifies parallel execution clusters."""

    def get_topological_order(self, graph: DAGGraph) -> List[str]:
        """Kahn's algorithm for topological ordering."""
        in_degree = {n_id: len(graph.get_incoming_edges(n_id)) for n_id in graph.nodes}
        queue = deque([n_id for n_id, deg in in_degree.items() if deg == 0])

        order = []
        while queue:
            node_id = queue.popleft()
            order.append(node_id)
            for child_id in graph.get_children(node_id):
                in_degree[child_id] -= 1
                if in_degree[child_id] == 0:
                    queue.append(child_id)

        return order

    def get_execution_stages(self, graph: DAGGraph) -> List[List[str]]:
        """
        Groups nodes into parallel execution stages (levelized order).
        Nodes in the same stage can be executed concurrently.
        """
        in_degree = {n_id: len(graph.get_incoming_edges(n_id)) for n_id in graph.nodes}
        current_stage = [n_id for n_id, deg in in_degree.items() if deg == 0]

        stages = []
        while current_stage:
            stages.append(current_stage)
            next_stage = []
            for node_id in current_stage:
                for child_id in graph.get_children(node_id):
                    in_degree[child_id] -= 1
                    if in_degree[child_id] == 0:
                        next_stage.append(child_id)
            current_stage = next_stage

        return stages


graph_scheduler = GraphScheduler()
