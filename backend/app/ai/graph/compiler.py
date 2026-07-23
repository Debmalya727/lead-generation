"""
AI Graph Engine — GraphCompiler compiling workflow dictionary/JSON specs into DAGGraph instances.
"""
from typing import Dict, List, Any
import logging

from app.ai.graph.graph import DAGGraph
from app.ai.graph.edge import GraphEdge
from app.ai.graph.node import (
    GraphNode,
    PromptNode,
    EmbeddingNode,
    SearchNode,
    RetrievalNode,
    ReasoningNode,
    GenerationNode,
    ValidationNode,
    GuardrailNode,
    MemoryNode,
    EvaluationNode,
    ToolNode,
    OutputNode,
    CheckpointNode,
)

logger = logging.getLogger("backend.ai.graph.compiler")

# Factory mapping node_type string → Node class
NODE_FACTORY: Dict[str, type] = {
    "PromptNode": PromptNode,
    "EmbeddingNode": EmbeddingNode,
    "SearchNode": SearchNode,
    "RetrievalNode": RetrievalNode,
    "ReasoningNode": ReasoningNode,
    "GenerationNode": GenerationNode,
    "ValidationNode": ValidationNode,
    "GuardrailNode": GuardrailNode,
    "MemoryNode": MemoryNode,
    "EvaluationNode": EvaluationNode,
    "ToolNode": ToolNode,
    "OutputNode": OutputNode,
    "CheckpointNode": CheckpointNode,
}


class GraphCompiler:
    """Compiles JSON/dict workflow specs into executable DAGGraph instances."""

    def compile(self, spec: Dict[str, Any]) -> DAGGraph:
        """
        Compiles dict specification into DAGGraph.
        Spec format:
          workflow_id: str
          name: str
          initial_node_id: str
          nodes: list of node dicts
          edges: list of edge dicts
        """
        workflow_id = spec.get("workflow_id", "wf_compiled")
        name = spec.get("name", "Compiled Workflow")

        graph = DAGGraph(graph_id=workflow_id, name=name)
        initial_node_id = spec.get("initial_node_id")

        # 1. Instantiate Nodes
        nodes_spec = spec.get("nodes", [])
        for n_dict in nodes_spec:
            node_id = n_dict["node_id"]
            node_type = n_dict.get("node_type", "GenerationNode")
            node_cls = NODE_FACTORY.get(node_type, GenerationNode)

            node_inst = node_cls(
                node_id=node_id,
                name=n_dict.get("name", node_id),
                config=n_dict.get("config", {}),
                timeout_seconds=n_dict.get("timeout_seconds", 30.0),
                max_retries=n_dict.get("max_retries", 3),
                fallback_node_id=n_dict.get("fallback_node_id"),
            )
            graph.add_node(node_inst)

        if initial_node_id and initial_node_id in graph.nodes:
            graph.initial_node_id = initial_node_id

        # 2. Instantiate Edges
        edges_spec = spec.get("edges", [])
        for idx, e_dict in enumerate(edges_spec):
            edge_id = e_dict.get("edge_id", f"edge_{idx}")
            edge_inst = GraphEdge(
                edge_id=edge_id,
                from_node_id=e_dict["from_node_id"],
                to_node_id=e_dict["to_node_id"],
                condition_expression=e_dict.get("condition_expression"),
            )
            graph.add_edge(edge_inst)

        return graph


graph_compiler = GraphCompiler()
