"""
Research Orchestrator.

Master coordinator running multi-agent research pipeline:
1. WebsiteResearchAgent
2. NewsResearchAgent
3. HiringResearchAgent
4. TechnologyResearchAgent
5. CompetitorResearchAgent
6. SocialResearchAgent
7. ConfidenceEngine (Verified Facts & Confidence Scores)
8. GraphBuilder (Multi-relational Knowledge Graph)
9. ResearchSummarizer (AI SWOT & Executive Playbook)
"""
import logging
from typing import Optional, Dict, Any

from app.modules.research.agents.website_agent import WebsiteResearchAgent
from app.modules.research.agents.news_agent import NewsResearchAgent
from app.modules.research.agents.hiring_agent import HiringResearchAgent
from app.modules.research.agents.technology_agent import TechnologyResearchAgent
from app.modules.research.agents.competitor_agent import CompetitorResearchAgent
from app.modules.research.agents.social_agent import SocialResearchAgent
from app.modules.research.services.confidence_engine import ConfidenceEngine
from app.modules.research.services.graph_builder import GraphBuilder
from app.modules.research.services.research_summarizer import ResearchSummarizer

logger = logging.getLogger("backend.research.orchestrator")


class ResearchOrchestrator:
    """Master orchestrator for multi-agent autonomous enterprise research."""

    def __init__(self):
        self.website_agent = WebsiteResearchAgent()
        self.news_agent = NewsResearchAgent()
        self.hiring_agent = HiringResearchAgent()
        self.tech_agent = TechnologyResearchAgent()
        self.competitor_agent = CompetitorResearchAgent()
        self.social_agent = SocialResearchAgent()
        self.confidence_engine = ConfidenceEngine()
        self.graph_builder = GraphBuilder()
        self.summarizer = ResearchSummarizer()

    async def execute_pipeline(
        self,
        company_name: str,
        website_url: str,
        raw_text_content: str = "",
        tech_stack: Optional[list] = None,
        social_links: Optional[dict] = None,
        industry: str = "B2B SaaS / Services",
        progress_callback = None,
    ) -> Dict[str, Any]:
        """Run all research agents independently and consolidate results into a unified payload."""
        logger.info(f"ResearchOrchestrator starting multi-agent pipeline for '{company_name}' ({website_url})")

        # Step 1: Website Research Agent (25%)
        if progress_callback:
            await progress_callback(15.0, "Executing Website Research Agent...")
        website_findings = await self.website_agent.execute(
            company_name=company_name,
            website_url=website_url,
            raw_text_content=raw_text_content,
            tech_stack=tech_stack,
        )

        # Step 2: Tech & Hiring Research Agents (45%)
        if progress_callback:
            await progress_callback(35.0, "Executing Technology & Hiring Research Agents...")
        tech_findings = await self.tech_agent.execute(
            company_name=company_name,
            website_url=website_url,
            detected_stack=tech_stack,
        )
        hiring_findings = await self.hiring_agent.execute(
            company_name=company_name,
            website_url=website_url,
        )

        # Step 3: News & Social Agents (65%)
        if progress_callback:
            await progress_callback(55.0, "Executing News & Social Research Agents...")
        news_findings = await self.news_agent.execute(
            company_name=company_name,
            website_url=website_url,
        )
        social_findings = await self.social_agent.execute(
            company_name=company_name,
            website_url=website_url,
            social_links=social_links,
        )

        # Step 4: Competitor Agent (80%)
        if progress_callback:
            await progress_callback(75.0, "Executing Competitor Research Agent...")
        competitor_findings = await self.competitor_agent.execute(
            company_name=company_name,
            industry=industry,
        )

        # Step 5: Confidence Engine & Knowledge Graph (90%)
        if progress_callback:
            await progress_callback(85.0, "Building Knowledge Graph & Fact Verification...")
        verified_facts = self.confidence_engine.compute_verified_facts(
            company_name=company_name,
            website_url=website_url,
            website_findings=website_findings,
            news_findings=news_findings,
            hiring_findings=hiring_findings,
            tech_findings=tech_findings,
        )
        overall_confidence = self.confidence_engine.calculate_overall_confidence(verified_facts)

        knowledge_graph = self.graph_builder.build_graph(
            company_name=company_name,
            website_findings=website_findings,
            tech_findings=tech_findings,
            competitor_findings=competitor_findings,
            hiring_findings=hiring_findings,
        )

        # Step 6: AI Summarizer (100%)
        if progress_callback:
            await progress_callback(95.0, "Generating AI Executive Research Summary...")
        ai_summary = await self.summarizer.summarize(
            company_name=company_name,
            website_url=website_url,
            website_findings=website_findings,
            news_findings=news_findings,
            hiring_findings=hiring_findings,
            tech_findings=tech_findings,
            competitor_findings=competitor_findings,
            social_findings=social_findings,
        )

        return {
            "website_findings": website_findings,
            "news_findings": news_findings,
            "hiring_findings": hiring_findings,
            "tech_findings": tech_findings,
            "competitor_findings": competitor_findings,
            "social_findings": social_findings,
            "knowledge_graph": knowledge_graph,
            "verified_facts": verified_facts,
            "overall_confidence": overall_confidence,
            "ai_summary": ai_summary,
        }
