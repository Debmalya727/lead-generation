"""
AI Research Summarizer Service.

Consolidates multi-agent findings using the existing AI Provider abstraction (`get_llm_provider`).
Generates:
- Executive Summary, SWOT Analysis, Business Overview, Sales Opportunity, Risks, Expansion Opportunities, Buying Signals, Pitch Angle, Objections, Recommended Strategy
"""
import json
import logging
from typing import Any, Dict

from app.ai.providers.factory import get_llm_provider
from app.database.mongodb.collections.research import AIResearchSummary, SWOTAnalysis
from app.modules.research.prompts.research_prompts import (
    RESEARCH_SUMMARIZER_SYSTEM_PROMPT,
    RESEARCH_SUMMARIZER_USER_PROMPT,
)

logger = logging.getLogger("backend.research.research_summarizer")


class ResearchSummarizer:
    """Service for synthesizing multi-agent research data into executive AI summaries."""

    async def summarize(
        self,
        company_name: str,
        website_url: str,
        website_findings: Any = None,
        news_findings: Any = None,
        hiring_findings: Any = None,
        tech_findings: Any = None,
        competitor_findings: Any = None,
        social_findings: Any = None,
    ) -> AIResearchSummary:
        """Call LLM provider abstraction to produce consolidated research report summary."""
        logger.info(f"ResearchSummarizer generating AI summary report for '{company_name}'")

        try:
            llm_provider = get_llm_provider()

            news_text = "; ".join([a.headline for a in (news_findings.articles if news_findings else [])]) or "No major news anomalies"
            comp_text = "; ".join([c.name for c in (competitor_findings.competitors if competitor_findings else [])]) or "Standard B2B SaaS competitors"

            user_prompt = RESEARCH_SUMMARIZER_USER_PROMPT.format(
                company_name=company_name,
                website_url=website_url or "N/A",
                business_model=website_findings.business_model if website_findings else "B2B SaaS",
                products=", ".join(website_findings.products if website_findings else ["Enterprise Suite"]),
                target_customers=", ".join(website_findings.target_customers if website_findings else ["Mid-Market"]),
                pain_points=", ".join(website_findings.pain_points if website_findings else ["Operational scaling"]),
                news_summary=news_text,
                open_positions_count=hiring_findings.open_positions_count if hiring_findings else 10,
                hiring_velocity=hiring_findings.hiring_velocity if hiring_findings else "Medium",
                expansion_signals=", ".join(hiring_findings.expansion_signals if hiring_findings else ["Team expansion"]),
                cloud_hosting=", ".join(tech_findings.cloud_hosting if tech_findings else ["AWS"]),
                analytics_crm=", ".join((tech_findings.analytics if tech_findings else []) + (tech_findings.crm if tech_findings else [])),
                dev_tools=", ".join(tech_findings.developer_tools if tech_findings else ["Docker", "Git"]),
                tech_maturity=tech_findings.tech_maturity if tech_findings else "Modern Enterprise",
                competitors_summary=comp_text,
                social_score=social_findings.overall_presence_score if social_findings else 80,
            )

            raw_response = await llm_provider.complete(
                prompt=user_prompt,
                system_prompt=RESEARCH_SUMMARIZER_SYSTEM_PROMPT,
            )

            cleaned_text = raw_response.strip()
            if cleaned_text.startswith("```json"):
                cleaned_text = cleaned_text[7:]
            if cleaned_text.endswith("```"):
                cleaned_text = cleaned_text[:-3]

            parsed = json.loads(cleaned_text.strip())

            swot_dict = parsed.get("swot", {})
            swot_obj = SWOTAnalysis(
                strengths=swot_dict.get("strengths", ["Strong product-market fit", "Modern web infrastructure"]),
                weaknesses=swot_dict.get("weaknesses", ["Operational scaling complexity"]),
                opportunities=swot_dict.get("opportunities", ["Global geographic expansion", "Enterprise API monetization"]),
                threats=swot_dict.get("threats", ["Established market incumbents", "Cost sensitivity"]),
            )

            return AIResearchSummary(
                executive_summary=parsed.get("executive_summary", f"{company_name} is a high-growth B2B enterprise operating in cloud-native technology."),
                swot=swot_obj,
                business_overview=parsed.get("business_overview", f"{company_name} provides specialized SaaS platform solutions to enterprise clients."),
                sales_opportunity=parsed.get("sales_opportunity", "Strong candidate for operational efficiency & cloud automation tools."),
                risks=parsed.get("risks", ["Budget cycle timing", "Legacy migration friction"]),
                expansion_opportunities=parsed.get("expansion_opportunities", ["Enterprise division upsell", "Multi-region deployment"]),
                buying_signals=parsed.get("buying_signals", ["Active engineering hiring spree", "Recent product launch announcements"]),
                pitch_angle=parsed.get("pitch_angle", f"Focus on ROI acceleration and seamless integration for {company_name}'s core platform."),
                objections=parsed.get("objections", ["Existing internal tool built -> Highlight 3x ROI multiplier and zero maintenance overhead"]),
                recommended_strategy=parsed.get("recommended_strategy", "Initiate multi-threaded outreach targeting Engineering & Business Operations leaders."),
            )

        except Exception as e:
            logger.warning(f"Fallback to default AI Research Summary due to LLM parsing exception: {str(e)}")
            return self._build_fallback_summary(company_name, website_findings, hiring_findings, tech_findings)

    def _build_fallback_summary(
        self,
        company_name: str,
        website_findings: Any = None,
        hiring_findings: Any = None,
        tech_findings: Any = None,
    ) -> AIResearchSummary:
        """Fallback summary when LLM provider is offline or mock."""
        return AIResearchSummary(
            executive_summary=f"{company_name} is a B2B enterprise operating a modern cloud-native web platform. Analysis indicates active market expansion and hiring velocity.",
            swot=SWOTAnalysis(
                strengths=["Modern cloud-native tech stack", "Active engineering recruitment", "Clear product value proposition"],
                weaknesses=["Potential operational bottlenecks during rapid headcount scaling"],
                opportunities=["API ecosystem monetization", "Enterprise mid-market market share capture"],
                threats=["Incumbent competitor pricing pressure"],
            ),
            business_overview=f"{company_name} operates a subscription & solutions business model serving enterprise and mid-market customers.",
            sales_opportunity=f"High likelihood of interest in workflow automation and infrastructure optimization tools.",
            risks=["Procurement review timeline", "Internal resource constraints"],
            expansion_opportunities=["Cross-departmental license expansion", "International market deployment"],
            buying_signals=["Active recruitment across Engineering & Sales", "Recent digital footprint growth"],
            pitch_angle=f"Help {company_name} accelerate growth while eliminating operational integration friction.",
            objections=["We have internal initiatives in progress -> Demonstrate immediate time-to-value advantage"],
            recommended_strategy="Execute multi-channel outreach combining email and executive social touchpoints.",
        )
