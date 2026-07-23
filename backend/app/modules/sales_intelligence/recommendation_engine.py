"""
AI Sales Recommendation Engine.

Calls LLM provider abstraction to construct a high-converting B2B Sales Strategy Playbook:
- Best contact person
- Best outreach channel
- Best time to contact
- Tailored product pitch
- Conversation starter
- Recommended email tone
- Objections & counter-responses
- Follow-up cadence
"""
import json
import logging
import re
from typing import List, Dict, Any, Optional

from app.ai.providers.factory import get_llm_provider
from app.database.mongodb.collections.sales_intelligence import SalesRecommendation, DecisionMaker, GrowthSignal
from app.modules.sales_intelligence.prompts.intelligence_prompts import (
    SALES_INTELLIGENCE_SYSTEM_PROMPT,
    SALES_RECOMMENDATIONS_PROMPT_TEMPLATE,
)

logger = logging.getLogger("backend.sales_intelligence.recommendation_engine")


class RecommendationEngine:
    """Generates AI Sales Playbooks and Recommendations using LLM provider abstraction."""

    async def generate_recommendations(
        self,
        company_name: str,
        website_url: str,
        industry: str,
        company_size: str,
        revenue_estimate: str,
        intent_score: int,
        intent_level: str,
        categories: List[str],
        decision_makers: List[DecisionMaker],
        growth_signals: List[GrowthSignal],
        pain_points: List[str],
        tech_stack: List[Dict[str, str]],
    ) -> SalesRecommendation:
        """Call LLM provider abstraction to generate Sales Recommendations."""
        # Format decision makers summary
        dm_lines = []
        for dm in decision_makers[:3]:
            dm_lines.append(f"- {dm.name} ({dm.designation}, {dm.department}) — Email: {dm.company_email or 'N/A'}")
        dm_summary = "\n".join(dm_lines) if dm_lines else "- Primary Company Contact"

        # Format growth signals summary
        sig_summary = "; ".join(s.description for s in growth_signals[:4]) if growth_signals else "Steady operations"

        # Format pain points & tech stack
        pp_summary = "; ".join(pain_points[:3]) if pain_points else "Process optimization and operational scaling"
        ts_summary = ", ".join(t.get("name", "") for t in tech_stack[:5]) if tech_stack else "Standard web stack"

        prompt = SALES_RECOMMENDATIONS_PROMPT_TEMPLATE.format(
            company_name=company_name,
            website_url=website_url or "N/A",
            industry=industry or "B2B",
            company_size=company_size or "SMB",
            revenue_estimate=revenue_estimate or "N/A",
            intent_score=intent_score,
            intent_level=intent_level,
            categories=", ".join(categories) if categories else "SMB",
            decision_makers_summary=dm_summary,
            signals_summary=sig_summary,
            pain_points_summary=pp_summary,
            tech_stack_summary=ts_summary,
        )

        llm = get_llm_provider()
        logger.info(f"Calling LLM provider ({type(llm).__name__}) for sales recommendations: {company_name}")
        raw_response = await llm.complete(prompt=prompt, system_prompt=SALES_INTELLIGENCE_SYSTEM_PROMPT)
        clean_json_str = self._clean_json(raw_response)

        try:
            parsed = json.loads(clean_json_str)
            return SalesRecommendation(
                best_contact_person=parsed.get("best_contact_person") or (decision_makers[0].name if decision_makers else "Managing Director"),
                best_outreach_channel=parsed.get("best_outreach_channel") or "Email",
                best_time_to_contact=parsed.get("best_time_to_contact") or "Tuesday - Thursday (09:00 - 11:00 AM)",
                pain_points=parsed.get("pain_points") or pain_points,
                recommended_product_pitch=parsed.get("recommended_product_pitch") or f"Help {company_name} streamline operations and accelerate customer acquisition.",
                conversation_starter=parsed.get("conversation_starter") or f"Noticed {company_name}'s recent work in the {industry} sector.",
                recommended_email_tone=parsed.get("recommended_email_tone") or "Professional & Consultative",
                risk_factors=parsed.get("risk_factors") or ["Budget review cycles", "Existing vendor contracts"],
                opportunity_summary=parsed.get("opportunity_summary") or f"High-value target in {industry} exhibiting active intent signals.",
                competitive_advantage=parsed.get("competitive_advantage") or "Faster implementation timeline and higher ROI metrics.",
                objections=parsed.get("objections") or ["We already have a solution -> Demonstrate 3x ROI multiplier"],
                followup_strategy=parsed.get("followup_strategy") or "Day 1 Initial Pitch, Day 3 Case Study Share, Day 7 Final Follow-up",
            )
        except Exception as e:
            logger.warning(f"Failed to parse LLM sales recommendation JSON for {company_name}: {str(e)}. Using fallback.")
            best_dm = decision_makers[0].name if decision_makers else "Managing Director"
            return SalesRecommendation(
                best_contact_person=best_dm,
                best_outreach_channel="Email",
                best_time_to_contact="Tuesday - Thursday (09:00 - 11:00 AM)",
                pain_points=pain_points or ["Operational efficiency", "Customer acquisition cost optimization"],
                recommended_product_pitch=f"Help {company_name} accelerate revenue growth and optimize operations.",
                conversation_starter=f"Noticed {company_name}'s growth momentum in {industry}.",
                recommended_email_tone="Professional & Consultative",
                risk_factors=["Longer procurement cycle", "Internal bandwidth constraints"],
                opportunity_summary=f"Strong fit account in {industry} vertical.",
                competitive_advantage="Tailored solution with lower implementation overhead.",
                objections=["No immediate budget -> Offer flexible pilot trial"],
                followup_strategy="Day 1 Email, Day 3 LinkedIn, Day 7 Followup",
            )

    def _clean_json(self, text: str) -> str:
        text = text.strip()
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        return text.strip()
