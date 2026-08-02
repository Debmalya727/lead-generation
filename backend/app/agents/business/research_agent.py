"""
ResearchAgent — Phase 11 Milestone 2 Business Agent.

Retrieves and synthesizes structured company intelligence from:
- ResearchReport (Phase 9)
- CompanyIntelligence (Phase 5)
- LeadScore (Phase 6)
- SalesIntelligenceReport (Phase 8)
- Knowledge Graph

Produces: company_context, key_facts, technology_stack, decision_makers,
          growth_signals, buying_signals, pain_points, confidence.
"""
import json
import logging
from typing import Dict, Any, List, Optional

from app.agents.runtime.base_agent import BaseAgent
from app.agents.runtime.result import AgentResult
from app.agents.runtime.context import ExecutionContext
from app.agents.registry.registry import register_agent
from app.agents.prompts.research_prompts import (
    RESEARCH_AGENT_SYSTEM_PROMPT,
    RESEARCH_AGENT_USER_PROMPT,
)
from app.ai.providers.factory import get_llm_provider

logger = logging.getLogger("backend.agents.business.research")


@register_agent
class ResearchAgent(BaseAgent):
    """Production Research Agent synthesizing company intelligence from all platform modules."""

    agent_id: str = "research_agent"
    name: str = "Research Agent"
    version: str = "1.0.0"
    description: str = "Retrieves and synthesizes company intelligence from research reports, company intelligence, lead scores, and sales intelligence into structured company context."
    capabilities: List[str] = [
        "company_intelligence_retrieval",
        "research_report_synthesis",
        "technology_stack_analysis",
        "decision_maker_identification",
        "growth_signal_detection",
        "buying_signal_detection",
        "pain_point_extraction",
    ]

    def __init__(self):
        super().__init__()
        self.llm_provider = get_llm_provider("research")

    async def execute(self, context: ExecutionContext) -> AgentResult:
        """Retrieve and synthesize company intelligence."""
        self.log(f"ResearchAgent executing for lead_id='{context.lead_id}' (job: {context.job_id})")

        lead_id = context.lead_id
        owner_id = context.owner_id

        # Gather available data from platform modules
        company_intel_data = await self._fetch_company_intelligence(lead_id, owner_id)
        research_report_data = await self._fetch_research_report(lead_id, owner_id)
        lead_score_data = await self._fetch_lead_score(lead_id, owner_id)
        sales_intel_data = await self._fetch_sales_intelligence(lead_id, owner_id)

        company_name = (
            company_intel_data.get("company_name")
            or research_report_data.get("company_name")
            or context.inputs.get("company_name", "Target Company")
        )

        self.log(f"Fetched intelligence for '{company_name}'. Calling LLM to synthesize research context...")

        user_prompt = RESEARCH_AGENT_USER_PROMPT.format(
            company_name=company_name,
            lead_id=lead_id or "N/A",
            company_intelligence=json.dumps(company_intel_data, indent=2, default=str)[:3000],
            research_report=json.dumps(research_report_data, indent=2, default=str)[:3000],
            lead_score=json.dumps(lead_score_data, indent=2, default=str)[:1000],
            sales_intelligence=json.dumps(sales_intel_data, indent=2, default=str)[:2000],
        )

        raw_response = await self.llm_provider.complete(
            prompt=user_prompt,
            system_prompt=RESEARCH_AGENT_SYSTEM_PROMPT,
        )

        parsed = self._parse_llm_json(raw_response, fallback_company=company_name)
        confidence = parsed.get("confidence", 75)

        artifact = {
            "name": f"research_context_{lead_id or 'no_lead'}.json",
            "type": "research_context",
            "content": parsed,
        }
        self.artifacts.append(artifact)

        self.log(f"ResearchAgent completed synthesis. Confidence={confidence}")

        return AgentResult(
            status="completed",
            confidence=confidence,
            messages=[
                f"Research synthesis completed for '{company_name}'.",
                f"Identified {len(parsed.get('growth_signals', []))} growth signals and {len(parsed.get('pain_points', []))} pain points.",
                f"Data confidence: {confidence}%",
            ],
            logs=self.logs,
            artifacts=self.artifacts,
            outputs=parsed,
            metadata={"agent_type": "research", "company_name": company_name, "lead_id": lead_id},
        )

    async def _fetch_company_intelligence(self, lead_id: Optional[str], owner_id: str) -> Dict[str, Any]:
        """Fetch CompanyIntelligence document for this lead."""
        if not lead_id:
            return {}
        try:
            from app.database.mongodb.repositories.intelligence_repository import IntelligenceRepository
            from bson import ObjectId
            repo = IntelligenceRepository()
            intel = await repo.find_by_lead_id(lead_id)
            if intel:
                return intel.model_dump(exclude_none=True)
        except Exception as e:
            self.log(f"CompanyIntelligence fetch warning: {str(e)}")
        return {}

    async def _fetch_research_report(self, lead_id: Optional[str], owner_id: str) -> Dict[str, Any]:
        """Fetch ResearchReport document for this lead."""
        if not lead_id:
            return {}
        try:
            from app.database.mongodb.repositories.research_repository import ResearchRepository
            repo = ResearchRepository()
            report = await repo.get_by_lead_id(lead_id, owner_id)
            if report:
                return report.model_dump(exclude_none=True)
        except Exception as e:
            self.log(f"ResearchReport fetch warning: {str(e)}")
        return {}

    async def _fetch_lead_score(self, lead_id: Optional[str], owner_id: str) -> Dict[str, Any]:
        """Fetch LeadScore document for this lead."""
        if not lead_id:
            return {}
        try:
            from app.database.mongodb.repositories.scoring_repository import ScoringRepository
            repo = ScoringRepository()
            score = await repo.get_by_lead_id(lead_id)
            if score:
                return score.model_dump(exclude_none=True)
        except Exception as e:
            self.log(f"LeadScore fetch warning: {str(e)}")
        return {}

    async def _fetch_sales_intelligence(self, lead_id: Optional[str], owner_id: str) -> Dict[str, Any]:
        """Fetch SalesIntelligenceReport for this lead."""
        if not lead_id:
            return {}
        try:
            from app.database.mongodb.repositories.sales_intelligence_repository import SalesIntelligenceRepository
            repo = SalesIntelligenceRepository()
            report = await repo.get_by_lead_id(lead_id, owner_id)
            if report:
                return report.model_dump(exclude_none=True)
        except Exception as e:
            self.log(f"SalesIntelligence fetch warning: {str(e)}")
        return {}

    def _parse_llm_json(self, raw: str, fallback_company: str = "Target Company") -> Dict[str, Any]:
        """Parse LLM JSON response with fallback."""
        try:
            cleaned = raw.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            return json.loads(cleaned.strip())
        except Exception as e:
            self.log(f"JSON parse warning, using fallback: {str(e)}")
            return {
                "company_name": fallback_company,
                "executive_summary": f"Research synthesis in progress for {fallback_company}.",
                "key_facts": [],
                "technology_stack": [],
                "decision_makers": [],
                "growth_signals": [],
                "buying_signals": [],
                "pain_points": [],
                "competitors": [],
                "recent_news": [],
                "hiring_signals": [],
                "confidence": 40,
                "sources": ["fallback_mode"],
            }
