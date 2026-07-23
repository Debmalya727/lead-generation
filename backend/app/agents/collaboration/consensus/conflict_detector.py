"""
Conflict Detector for Multi-Agent Collaboration Engine.

Analyzes agent outputs across the workspace to detect conflicting claims or factual contradictions.
"""
import logging
from typing import Dict, List, Any

logger = logging.getLogger("backend.agents.collaboration.consensus.conflict_detector")


class ConflictDetector:
    """Inspector detecting conflicting outputs between agents."""

    def detect_conflicts(self, agent_outputs: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Inspect dict mapping agent_id -> outputs payload for contradictions.
        Returns list of conflict objects.
        """
        conflicts = []

        # Example 1: Funding Stage Conflict (e.g. Research vs Memory)
        research_out = agent_outputs.get("research_agent", {})
        memory_out = agent_outputs.get("memory_agent", {})
        strategy_out = agent_outputs.get("sales_strategy_agent", {})

        # Compare funding stage
        r_funding = research_out.get("funding_stage")
        m_funding = memory_out.get("funding_stage")
        if r_funding and m_funding and r_funding.lower().strip() != m_funding.lower().strip():
            conflicts.append({
                "topic": "funding_stage",
                "severity": "high",
                "agents_involved": ["research_agent", "memory_agent"],
                "competing_claims": {
                    "research_agent": r_funding,
                    "memory_agent": m_funding,
                },
                "reasoning": f"ResearchAgent claims funding stage is '{r_funding}', whereas MemoryAgent claims '{m_funding}'.",
            })

        # Compare company size / employee count
        r_size = research_out.get("company_size")
        m_size = memory_out.get("company_size")
        if r_size and m_size and r_size.lower().strip() != m_size.lower().strip():
            conflicts.append({
                "topic": "company_size",
                "severity": "medium",
                "agents_involved": ["research_agent", "memory_agent"],
                "competing_claims": {
                    "research_agent": r_size,
                    "memory_agent": m_size,
                },
                "reasoning": f"ResearchAgent size '{r_size}' contradicts MemoryAgent size '{m_size}'.",
            })

        # Compare Opportunity Priority (e.g. Strategy priority vs LeadScore)
        s_priority = strategy_out.get("priority")
        if s_priority and strategy_out.get("confidence", 100) < 50:
            conflicts.append({
                "topic": "opportunity_priority",
                "severity": "low",
                "agents_involved": ["sales_strategy_agent"],
                "competing_claims": {"sales_strategy_agent": s_priority},
                "reasoning": f"SalesStrategyAgent prioritized opportunity as '{s_priority}' but confidence is low ({strategy_out.get('confidence')}%).",
            })

        logger.info(f"ConflictDetector found {len(conflicts)} conflicts across {len(agent_outputs)} agent outputs.")
        return conflicts
