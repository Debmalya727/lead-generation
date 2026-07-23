"""
Company Relationship Graph Engine.

Constructs a scalable graph of nodes & edges linking:
- Company Node
- Decision Maker Persona Nodes
- Tech Stack Nodes
- Growth Signal Nodes
- Industry Node
- Lead Score Node
- Campaign Outreach Node
"""
import logging
from typing import List, Dict, Any

from app.database.mongodb.collections.sales_intelligence import (
    CompanyRelationshipGraph,
    SalesGraphNode,
    SalesGraphEdge,
    DecisionMaker,
    GrowthSignal,
)

logger = logging.getLogger("backend.sales_intelligence.graph_engine")


class GraphEngine:
    """Builds graph nodes and weighted edges for company relationships."""

    def build_graph(
        self,
        company_id: str,
        company_name: str,
        decision_makers: List[DecisionMaker],
        growth_signals: List[GrowthSignal],
        tech_stack: List[Dict[str, str]],
        industry: str = "B2B Services",
        lead_score_val: int = 80,
    ) -> CompanyRelationshipGraph:
        """Construct graph nodes and relationships."""
        nodes: List[SalesGraphNode] = []
        edges: List[SalesGraphEdge] = []

        # Central Company Node
        c_node_id = f"company_{company_id}"
        nodes.append(SalesGraphNode(id=c_node_id, label=company_name, type="company"))

        # Industry Node
        ind_node_id = f"industry_{industry.lower().replace(' ', '_')}"
        nodes.append(SalesGraphNode(id=ind_node_id, label=industry, type="industry"))
        edges.append(SalesGraphEdge(source_id=c_node_id, target_id=ind_node_id, relation_type="operates_in", weight=1.0))

        # Lead Score Node
        score_node_id = f"score_{lead_score_val}"
        nodes.append(SalesGraphNode(id=score_node_id, label=f"Quality Score: {lead_score_val}/100", type="score"))
        edges.append(SalesGraphEdge(source_id=c_node_id, target_id=score_node_id, relation_type="scored_by", weight=0.9))

        # Decision Maker Nodes
        for idx, dm in enumerate(decision_makers):
            dm_id = f"person_{company_id}_{idx}"
            nodes.append(SalesGraphNode(id=dm_id, label=f"{dm.name} ({dm.designation})", type="person"))
            edges.append(SalesGraphEdge(source_id=c_node_id, target_id=dm_id, relation_type="employs", weight=1.0))

        # Tech Stack Nodes
        for idx, t in enumerate(tech_stack[:6]):
            t_name = t.get("name", f"Tech_{idx}")
            t_id = f"tech_{t_name.lower().replace(' ', '_')}"
            nodes.append(SalesGraphNode(id=t_id, label=t_name, type="tech"))
            edges.append(SalesGraphEdge(source_id=c_node_id, target_id=t_id, relation_type="uses_tech", weight=0.8))

        # Growth Signal Nodes
        for idx, sig in enumerate(growth_signals[:4]):
            sig_id = f"signal_{company_id}_{idx}"
            nodes.append(SalesGraphNode(id=sig_id, label=f"Signal: {sig.type.title()}", type="signal"))
            edges.append(SalesGraphEdge(source_id=c_node_id, target_id=sig_id, relation_type="exhibits_signal", weight=0.9))

        logger.info(f"Built relationship graph for '{company_name}' with {len(nodes)} nodes and {len(edges)} edges")
        return CompanyRelationshipGraph(nodes=nodes, edges=edges)
