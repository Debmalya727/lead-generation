"""
OutreachAgent — Phase 11 Milestone 2 Business Agent.

Generates highly personalized multi-channel outreach content:
- Cold email (subject + body + CTA)
- LinkedIn message
- Call script (opener, value hook, discovery, close)
- Meeting request
- Follow-up sequence (3 steps, varied angles)

Uses: research context + memory context + sales strategy as inputs.
"""
import json
import logging
from typing import Dict, Any, List

from app.agents.runtime.base_agent import BaseAgent
from app.agents.runtime.result import AgentResult
from app.agents.runtime.context import ExecutionContext
from app.agents.registry.registry import register_agent
from app.agents.prompts.outreach_prompts import (
    OUTREACH_AGENT_SYSTEM_PROMPT,
    OUTREACH_AGENT_USER_PROMPT,
)
from app.ai.providers.factory import get_llm_provider

logger = logging.getLogger("backend.agents.business.outreach")


@register_agent
class OutreachAgent(BaseAgent):
    """Production Outreach Agent generating personalized multi-channel sales outreach packages."""

    agent_id: str = "outreach_agent"
    name: str = "Outreach Agent"
    version: str = "1.0.0"
    description: str = "Generates highly personalized cold email, LinkedIn message, call script, meeting request, and follow-up sequence using research, memory, and sales strategy context."
    capabilities: List[str] = [
        "cold_email_generation",
        "linkedin_message_generation",
        "call_script_generation",
        "meeting_request_generation",
        "follow_up_sequence_generation",
        "personalization_optimization",
        "multi_channel_outreach",
    ]

    def __init__(self):
        super().__init__()
        self.llm_provider = get_llm_provider()

    async def execute(self, context: ExecutionContext) -> AgentResult:
        """Generate personalized multi-channel outreach package."""
        self.log(f"OutreachAgent executing for lead_id='{context.lead_id}' (job: {context.job_id})")

        research_output = context.inputs.get("research_output", {})
        memory_output = context.inputs.get("memory_output", {})
        strategy_output = context.inputs.get("strategy_output", {})
        company_name = research_output.get("company_name", context.inputs.get("company_name", "Target Company"))

        self.log(f"Generating outreach package for '{company_name}' using research + memory + strategy...")

        user_prompt = OUTREACH_AGENT_USER_PROMPT.format(
            company_name=company_name,
            lead_id=context.lead_id or "N/A",
            goal=context.goal,
            research_context=json.dumps(research_output, indent=2, default=str)[:2000],
            memory_context=json.dumps(memory_output, indent=2, default=str)[:1500],
            strategy_context=json.dumps(strategy_output, indent=2, default=str)[:2000],
        )

        raw_response = await self.llm_provider.complete(
            prompt=user_prompt,
            system_prompt=OUTREACH_AGENT_SYSTEM_PROMPT,
        )

        parsed = self._parse_llm_json(raw_response, company_name=company_name)
        confidence = parsed.get("confidence", 78)
        personalization_score = parsed.get("personalization_score", 70)

        artifact = {
            "name": f"outreach_package_{context.lead_id or 'no_lead'}.json",
            "type": "outreach_package",
            "content": parsed,
        }
        self.artifacts.append(artifact)

        self.log(f"OutreachAgent completed. Personalization score={personalization_score}, Confidence={confidence}")

        return AgentResult(
            status="completed",
            confidence=confidence,
            messages=[
                f"Outreach package generated for '{company_name}'.",
                f"Personalization score: {personalization_score}/100.",
                f"Generated {len(parsed.get('follow_up_sequence', []))} follow-up steps.",
            ],
            logs=self.logs,
            artifacts=self.artifacts,
            outputs=parsed,
            metadata={"agent_type": "outreach", "personalization_score": personalization_score, "company_name": company_name},
        )

    def _parse_llm_json(self, raw: str, company_name: str = "Target Company") -> Dict[str, Any]:
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
            self.log(f"JSON parse warning: {str(e)}")
            return {
                "cold_email": {
                    "subject": f"Quick question for {company_name}",
                    "preview_text": "Relevant insight for your team",
                    "body": f"Hi [First Name],\n\nI noticed {company_name} is [growth signal]. We help companies like yours [value proposition].\n\nWould a 15-minute call make sense this week?\n\nBest,\n[Your Name]",
                    "cta": "Book a 15-minute call",
                    "personalization_tokens": {"company": company_name, "pain_point": "growth challenges", "hook": "growth signal"},
                },
                "linkedin_message": f"Hi [Name], noticed {company_name} is growing fast. Worth a quick chat about how we could help? [Your Name]",
                "call_script": {
                    "opener": f"Hi, this is [Name] from [Company]. I'm reaching out because I noticed {company_name}...",
                    "value_hook": "We help B2B companies like yours achieve [specific outcome] in [timeframe].",
                    "discovery_question": "What's your biggest challenge with [pain area] right now?",
                    "objection_handler": "I understand. Many of our clients felt the same way before seeing [specific result].",
                    "close": "Would it make sense to schedule a 20-minute demo to show you exactly how this works?",
                },
                "meeting_request": f"Hi [Name], I'd love to show you how we could help {company_name} [specific outcome]. Do you have 20 minutes this week?",
                "follow_up_sequence": [
                    {"day": 3, "channel": "email", "subject": "Following up", "body": "Hi [Name], wanted to follow up on my email...", "angle": "value"},
                    {"day": 7, "channel": "linkedin", "body": "Hi [Name], saw your recent post on [topic]...", "angle": "social_proof"},
                    {"day": 14, "channel": "email", "subject": "Last reach out", "body": "Hi [Name], I don't want to be a nuisance...", "angle": "breakup"},
                ],
                "personalization_score": 45,
                "confidence": 40,
            }
