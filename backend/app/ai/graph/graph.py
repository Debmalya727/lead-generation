"""
AI Graph Engine — DAGGraph structure representing nodes, edges, and graph topological properties.
"""
from typing import Dict, List, Set, Optional, Any
import logging

from app.ai.graph.node import GraphNode
from app.ai.graph.edge import GraphEdge

logger = logging.getLogger("backend.ai.graph.dag")


class DAGGraph:
    """Directed Acyclic Graph containing GraphNodes and GraphEdges."""

    def __init__(self, graph_id: str, name: str = "DAG"):
        self.graph_id = graph_id
        self.name = name
        self.nodes: Dict[str, GraphNode] = {}
        self.edges: List[GraphEdge] = []
        self.initial_node_id: Optional[str] = None

    def add_node(self, node: GraphNode) -> None:
        """Add a node to the graph."""
        self.nodes[node.node_id] = node
        if not self.initial_node_id:
            self.initial_node_id = node.node_id

    def add_edge(self, edge: GraphEdge) -> None:
        """Add a directed edge between nodes."""
        if edge.from_node_id not in self.nodes:
            raise ValueError(f"Source node '{edge.from_node_id}' does not exist in graph.")
        if edge.to_node_id not in self.nodes:
            raise ValueError(f"Target node '{edge.to_node_id}' does not exist in graph.")
        self.edges.append(edge)

    def get_outgoing_edges(self, node_id: str) -> List[GraphEdge]:
        """Return all edges originating from node_id."""
        return [e for e in self.edges if e.from_node_id == node_id]

    def get_incoming_edges(self, node_id: str) -> List[GraphEdge]:
        """Return all edges pointing into node_id."""
        return [e for e in self.edges if e.to_node_id == node_id]

    def get_children(self, node_id: str) -> List[str]:
        """Return node IDs of immediate children."""
        return [e.to_node_id for e in self.get_outgoing_edges(node_id)]

    def get_parents(self, node_id: str) -> List[str]:
        """Return node IDs of immediate parents."""
        return [e.from_node_id for e in self.get_incoming_edges(node_id)]

    def is_root(self, node_id: str) -> bool:
        """Check if node has no incoming edges."""
        return len(self.get_incoming_edges(node_id)) == 0

    def is_terminal(self, node_id: str) -> bool:
        """Check if node has no outgoing edges."""
        return len(self.get_outgoing_edges(node_id)) == 0
