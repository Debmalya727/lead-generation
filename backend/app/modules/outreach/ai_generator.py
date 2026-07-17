"""
AI Email Prompt Builders & Copy Generator for Outreach Campaigns.

Generates:
- Cold Email Body
- Follow-up Email Body
- High-Converting Subject Lines
- Personalized Icebreakers
- Calls to Action (CTAs)

Utilizes Lead, Company Intelligence, Lead Score, Tech Stack, Pain Points, Buying Signals, Products, Services.
"""
import json
import logging
import re
from typing import Dict, List, Optional

from app.ai.providers.factory import get_llm_provider

logger = logging.getLogger("backend.outreach.ai_generator")

OUTREACH_SYSTEM_PROMPT = """You are a top-performing B2B sales copywriter specializing in personalized, high-converting outreach.
Your emails are concise, human, direct, and focused on building authentic business relationships.

CRITICAL RULES:
1. Avoid generic sales jargon (e.g., 'synergy', 'game-changer', 'cutting-edge').
2. Keep email copy under 150 words.
3. Personalize content using specific pain points, tech stack, and buying signals provided.
4. Always include dynamic variable placeholders like {{first_name}}, {{company}} where appropriate.
5. Return clean JSON outputs as requested.
"""


class AIEmailGenerator:
    """Generates personalized email copy using LLM provider abstraction."""

    async def generate_cold_email(
        self,
        company_name: str,
        website: str = "",
        industry: str = "",
        pain_points: Optional[List[str]] = None,
        buying_signals: Optional[List[str]] = None,
        tech_stack: Optional[List[str]] = None,
        lead_score: Optional[int] = None,
        value_proposition: str = "help grow revenue and streamline operations",
    ) -> Dict[str, str]:
        """Generate a complete cold email subject and body."""
        prompt = f"""Write a high-converting B2B cold email targeting {{first_name}} at {company_name} ({website}).

COMPANY CONTEXT:
- Industry: {industry or 'B2B'}
- Pain Points: {', '.join(pain_points) if pain_points else 'Operational scaling'}
- Buying Signals: {', '.join(buying_signals) if buying_signals else 'Expansion'}
- Tech Stack: {', '.join(tech_stack) if tech_stack else 'Modern web stack'}
- Lead Quality Score: {lead_score or 80}/100
- Our Value Proposition: {value_proposition}

Return a JSON object with:
{{
  "subject": "<Compelling short subject line under 7 words>",
  "icebreaker": "<Customized 1-sentence opening line>",
  "body": "<Complete cold email body, HTML formatted, under 120 words with clear CTA>",
  "cta": "<Clear low-friction CTA line>"
}}
Return only JSON."""

        llm = get_llm_provider()
        raw = await llm.complete(prompt=prompt, system_prompt=OUTREACH_SYSTEM_PROMPT)
        clean = self._clean_json(raw)

        try:
            return json.loads(clean)
        except Exception:
            return {
                "subject": f"Quick question regarding {company_name}",
                "icebreaker": f"Noticed {company_name}'s recent growth in the {industry or 'B2B'} space.",
                "body": f"<p>Hi {{first_name}},</p><p>Noticed {company_name}'s work in {industry or 'your sector'}. We help companies like yours address {pain_points[0] if pain_points else 'growth bottlenecks'}.</p><p>Would you be open to a brief 10-minute chat this week?</p><p>Best regards,<br/>{{sender_name}}</p>",
                "cta": "Would you be open to a brief 10-minute chat this week?",
            }

    async def generate_followup_email(
        self,
        company_name: str,
        previous_subject: str = "",
        step_number: int = 2,
        value_add: str = "relevant case study and ROI insights",
    ) -> Dict[str, str]:
        """Generate a follow-up email sequence step."""
        prompt = f"""Write follow-up email # {step_number} for {company_name}.
Previous subject: {previous_subject or 'Quick question'}
Value-add angle: {value_add}

Return a JSON object with:
{{
  "subject": "Re: {previous_subject or 'Quick question regarding ' + company_name}",
  "body": "<Short polite follow-up under 80 words adding value and a soft CTA>"
}}
Return only JSON."""

        llm = get_llm_provider()
        raw = await llm.complete(prompt=prompt, system_prompt=OUTREACH_SYSTEM_PROMPT)
        clean = self._clean_json(raw)

        try:
            return json.loads(clean)
        except Exception:
            return {
                "subject": f"Re: Quick question regarding {company_name}",
                "body": f"<p>Hi {{first_name}},</p><p>Following up on my last note. I know you're busy at {company_name}. Thought I'd share how similar teams solved key operational challenges.</p><p>Worth a brief 5-minute connect?</p>",
            }

    async def generate_subject_lines(
        self,
        company_name: str,
        industry: str = "",
        topic: str = "",
    ) -> List[str]:
        """Generate 3-5 high-converting subject lines for A/B testing."""
        prompt = f"""Generate 4 high-open-rate B2B cold email subject lines for {company_name} ({industry}).
Topic: {topic or 'partnership'}

Return a JSON object:
{{
  "subjects": ["subject 1", "subject 2", "subject 3", "subject 4"]
}}
Return only JSON."""

        llm = get_llm_provider()
        raw = await llm.complete(prompt=prompt, system_prompt=OUTREACH_SYSTEM_PROMPT)
        clean = self._clean_json(raw)

        try:
            res = json.loads(clean)
            return res.get("subjects", [f"Idea for {company_name}", f"Quick question", f"Growth at {company_name}"])
        except Exception:
            return [f"Idea for {company_name}", f"Quick question for {company_name}", f"Scaling {company_name}"]

    async def generate_icebreaker(
        self,
        company_name: str,
        buying_signals: Optional[List[str]] = None,
        tech_stack: Optional[List[str]] = None,
    ) -> str:
        """Generate a single personalized icebreaker sentence."""
        prompt = f"""Write 1 engaging personalized cold email opening icebreaker sentence for {{first_name}} at {company_name}.
Buying signals: {', '.join(buying_signals) if buying_signals else 'Growth'}
Tech stack: {', '.join(tech_stack) if tech_stack else 'Web'}

Return only the 1-sentence icebreaker text."""

        llm = get_llm_provider()
        raw = await llm.complete(prompt=prompt, system_prompt=OUTREACH_SYSTEM_PROMPT)
        return raw.strip().replace('"', "")

    def _clean_json(self, response: str) -> str:
        response = response.strip()
        response = re.sub(r"^```(?:json)?\s*", "", response)
        response = re.sub(r"\s*```$", "", response)
        return response.strip()
