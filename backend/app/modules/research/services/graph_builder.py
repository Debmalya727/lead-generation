"""
Knowledge Graph Builder.

Establishes multi-relational graph nodes & edges linking:
- Company, Products, Services, Decision Makers, Competitors, Technologies, Industries, Markets, Growth Signals, News, Hiring
Future-proofed for Phase 10 Vector Search, Phase 11 Autonomous Agents, and Phase 12 Conversational CRM.
"""
import logging
from typing import List, Any, Dict

from app.database.mongodb.collections.research import (
    ResearchKnowledgeGraph,
    GraphNode,
    GraphEdge,
)

logger = logging.getLogger("backend.research.graph_builder")


class GraphBuilder:
    """Builder for constructing graph topology across research findings."""

    def build_graph(
        self,
        company_name: str,
        website_findings: Any = None,
        tech_findings: Any = None,
        competitor_findings: Any = None,
        hiring_findings: Any = None,
    ) -> ResearchKnowledgeGraph:
        """Construct graph nodes and weighted edges."""
        logger.info(f"GraphBuilder constructing relationship graph for '{company_name}'")

        company_id = f"company_{company_name.lower().replace(' ', '_')}"
        nodes: List[GraphNode] = [
            GraphNode(id=company_id, label=company_name, type="company")
        ]
        edges: List[GraphEdge] = []

        # Add Products & Services Nodes
        if website_findings:
            for idx, prod in enumerate(website_findings.products):
                prod_id = f"product_{idx}"
                nodes.append(GraphNode(id=prod_id, label=prod, type="product"))
                edges.append(GraphEdge(source_id=company_id, target_id=prod_id, relation_type="OFFERS_PRODUCT", weight=1.0))

            for idx, srv in enumerate(website_findings.services):
                srv_id = f"service_{idx}"
                nodes.append(GraphNode(id=srv_id, label=srv, type="service"))
                edges.append(GraphEdge(source_id=company_id, target_id=srv_id, relation_type="PROVIDES_SERVICE", weight=0.9))

        # Add Tech Stack Nodes
        if tech_findings:
            for idx, tech in enumerate((tech_findings.cloud_hosting or []) + (tech_findings.database or [])):
                t_id = f"tech_{idx}"
                nodes.append(GraphNode(id=t_id, label=tech, type="tech"))
                edges.append(GraphEdge(source_id=company_id, target_id=t_id, relation_type="USES_TECHNOLOGY", weight=0.85))

        # Add Competitor Nodes
        if competitor_findings:
            for idx, comp in enumerate(competitor_findings.competitors):
                c_id = f"competitor_{idx}"
                nodes.append(GraphNode(id=c_id, label=comp.name, type="competitor"))
                edges.append(GraphEdge(source_id=company_id, target_id=c_id, relation_type="COMPETES_WITH", weight=0.95))

        # Add Hiring Department Nodes
        if hiring_findings:
            for idx, dept in enumerate(hiring_findings.departments):
                h_id = f"hiring_{idx}"
                nodes.append(GraphNode(id=h_id, label=f"{dept.department} ({dept.open_count} openings)", type="hiring"))
                edges.append(GraphEdge(source_id=company_id, target_id=h_id, relation_type="HIRING_FOR", weight=0.8))

        return ResearchKnowledgeGraph(nodes=nodes, edges=edges)
