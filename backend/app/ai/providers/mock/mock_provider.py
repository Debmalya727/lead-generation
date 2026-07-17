"""
Mock LLM provider that returns deterministic structured JSON output.
Used when no LLM_API_KEY is configured — allows full testing of the
intelligence pipeline without API credentials.
"""
import json
import logging
from app.ai.providers.base_llm import BaseLLMProvider

logger = logging.getLogger("backend.ai.mock_provider")


MOCK_INTELLIGENCE_OUTPUT = {
    "executive_summary": "A well-established company offering specialized products and services in its industry vertical, with a strong online presence and clear customer focus.",
    "company_description": "This company operates within its target market providing valuable solutions. Based on the website content, it appears to have an established track record and dedicated team serving clients across multiple segments.",
    "products": [
        "Core Product Suite",
        "Premium Tier Offering",
        "Custom Enterprise Solutions"
    ],
    "services": [
        "Professional Consulting",
        "Implementation & Onboarding",
        "Ongoing Support & Maintenance"
    ],
    "industry": "Professional Services",
    "company_size": "10-50 employees",
    "revenue_estimate": "$1M - $10M annually",
    "revenue_confidence": "low",
    "pain_points": [
        "Scaling operations while maintaining quality",
        "Customer acquisition cost optimization",
        "Competitive differentiation in a crowded market"
    ],
    "buying_signals": [
        "Active website with regular content updates",
        "Multiple service tiers indicating growth focus",
        "Presence of careers/jobs page suggesting expansion"
    ],
    "ideal_sales_angle": "Lead with ROI metrics and case studies. This company appears growth-oriented — emphasize how your offering accelerates their expansion without proportionally increasing operational overhead.",
    "confidence_score": 45
}

MOCK_SCORING_OUTPUT = {
    "score_explanation": "This company has complete contact information and a functional website, but displays minimal active buying signals and undocumented operational pain points, resulting in a moderate overall quality rating.",
    "strengths": [
        "Complete contact details including verified phone and email",
        "Active and responsive website presence",
        "Clearly identified industry vertical"
    ],
    "weaknesses": [
        "No explicit software stack or marketing tools detected",
        "Low estimate of current headcount limits immediate B2B sales potential"
    ],
    "risk_factors": [
        "Small estimated company size may indicate budget limitations",
        "Lack of recent hiring activity suggests flat growth trajectory"
    ],
    "recommended_outreach": "Initiate soft outreach via email. Avoid direct high-pressure sales pitches; instead, offer a free operational audit or resource guide tailored to mid-market professional services.",
    "score_adjustment": 5,
    "adjustment_reason": "Slight positive adjustment due to complete contact data reducing initial prospecting friction.",
    "confidence_score": 85
}


class MockLLMProvider(BaseLLMProvider):
    """
    Deterministic mock provider returning structured intelligence or scoring output.
    Used as a fallback when LLM_API_KEY is not configured.
    """

    async def complete(self, prompt: str, system_prompt: str = "") -> str:
        logger.warning(
            "MockLLMProvider is active — no LLM_API_KEY configured. "
            "Returning deterministic mock output. "
            "Set LLM_API_KEY in your environment for real AI extraction."
        )
        if "scoring assessment" in prompt.lower() or "score_adjustment" in prompt.lower() or "sales strategist" in system_prompt.lower():
            return json.dumps(MOCK_SCORING_OUTPUT)
        return json.dumps(MOCK_INTELLIGENCE_OUTPUT)

