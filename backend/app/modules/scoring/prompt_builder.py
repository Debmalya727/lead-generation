"""
Prompt builder for the LLM Scoring Reasoning Layer.

Constructs a structured prompt that asks the LLM to:
1. Provide a natural language explanation of the score
2. List concrete strengths, weaknesses, and risk factors
3. Recommend a specific outreach strategy
4. Optionally adjust the score by ±10 with justification
"""
import re
import logging
from typing import List

from app.modules.scoring.feature_extractor import FeatureVector
from app.modules.scoring.rule_engine import ScoreBreakdownEntry

logger = logging.getLogger("backend.scoring.prompt_builder")

SCORING_SYSTEM_PROMPT = """You are a senior B2B sales strategist and lead quality analyst.
You analyze lead data and scoring results to provide actionable sales intelligence.

CRITICAL RULES:
1. Return ONLY valid JSON — no markdown code blocks, no explanations outside the JSON.
2. Be specific and actionable — avoid generic phrases.
3. Base your analysis strictly on the provided feature data.
4. The score_adjustment must be between -10 and +10.
5. strengths, weaknesses, and risk_factors must each have 2-4 items.
"""

SCORING_PROMPT_TEMPLATE = """You are scoring a B2B sales lead for the company "{company_name}".

LEAD DATA:
- Website: {website_url}
- Has Email: {has_email}
- Has Phone: {has_phone}
- Industry: {industry}
- Company Size: {company_size}
- Revenue Estimate: {revenue_estimate} ({revenue_confidence} confidence)
- Buying Signals ({buying_signals_count}): {buying_signals}
- Pain Points ({pain_points_count}): {pain_points}
- Tech Stack ({tech_stack_count} technologies): {tech_stack}
- Social Presence ({social_count} platforms): {social_platforms}
- Key Pages: {key_pages}

RULE ENGINE RESULT:
- Rule Score: {rule_score}/100
- Breakdown:
{breakdown_text}

Based on this data, provide a scoring assessment as JSON with EXACTLY these fields:
{{
  "score_explanation": "<2-3 sentence natural language explanation of why this lead received this score>",
  "strengths": ["<specific strength 1>", "<specific strength 2>", "<specific strength 3>"],
  "weaknesses": ["<specific weakness 1>", "<specific weakness 2>"],
  "risk_factors": ["<risk 1>", "<risk 2>"],
  "recommended_outreach": "<specific outreach strategy for a sales rep — channel, timing, angle, talking points>",
  "score_adjustment": <integer between -10 and +10 to adjust the rule score up or down based on qualitative factors>,
  "adjustment_reason": "<one sentence explaining the adjustment>",
  "confidence_score": <integer 0-100 reflecting your confidence in this scoring decision>
}}

Return only the JSON object."""


class ScoringPromptBuilder:
    """Builds LLM prompts for the scoring reasoning layer."""

    def build_prompt(
        self,
        fv: FeatureVector,
        rule_score: int,
        breakdown: List[ScoreBreakdownEntry],
    ) -> str:
        """Construct the scoring reasoning prompt."""
        breakdown_lines = "\n".join(
            f"  - {entry.label}: {entry.score}/{entry.max_score} — {entry.rationale}"
            for entry in breakdown
        )

        tech_names = ", ".join(t["name"] for t in fv.tech_stack) if fv.tech_stack else "None detected"
        social_platforms = ", ".join(fv.social_links.keys()) if fv.social_links else "None"

        key_pages_list = []
        if fv.has_contact_page:
            key_pages_list.append("contact page")
        if fv.has_about_page:
            key_pages_list.append("about page")
        if fv.has_careers_page:
            key_pages_list.append("careers page")
        key_pages = ", ".join(key_pages_list) if key_pages_list else "none detected"

        buying_signals_text = (
            "; ".join(fv.buying_signals[:5]) if fv.buying_signals else "None"
        )
        pain_points_text = (
            "; ".join(fv.pain_points[:5]) if fv.pain_points else "None"
        )

        return SCORING_PROMPT_TEMPLATE.format(
            company_name=fv.company_name,
            website_url=fv.website_url or "Not provided",
            has_email="Yes" if fv.has_email else "No",
            has_phone="Yes" if fv.has_phone else "No",
            industry=fv.industry or "Unknown",
            company_size=fv.company_size_raw or "Unknown",
            revenue_estimate=fv.revenue_estimate_raw or "Unknown",
            revenue_confidence=fv.revenue_confidence_raw or "low",
            buying_signals_count=fv.buying_signals_count,
            buying_signals=buying_signals_text,
            pain_points_count=fv.pain_points_count,
            pain_points=pain_points_text,
            tech_stack_count=fv.tech_stack_count,
            tech_stack=tech_names,
            social_count=fv.social_count,
            social_platforms=social_platforms,
            key_pages=key_pages,
            rule_score=rule_score,
            breakdown_text=breakdown_lines,
        )

    def get_system_prompt(self) -> str:
        """Return the system prompt for the scoring LLM."""
        return SCORING_SYSTEM_PROMPT

    def clean_response(self, response: str) -> str:
        """Strip markdown code fences from LLM response."""
        response = response.strip()
        response = re.sub(r"^```(?:json)?\s*", "", response)
        response = re.sub(r"\s*```$", "", response)
        return response.strip()
