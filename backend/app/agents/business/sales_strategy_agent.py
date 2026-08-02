"""
SalesStrategyAgent — Phase 11 Milestone 2 Business Agent.

Analyzes company research and memory context to produce:
- Pain point analysis with severity scoring
- Buying signal detection with urgency scoring
- Budget indicators
- Decision maker strategy
- Value proposition tailored to this company
- Objection handling playbook
- Discovery questions for qualification
- Priority scoring (High/Medium/Low) with reasoning
- Next actions with timelines
"""
import json
import logging
from typing import Dict, Any, List

from app.agents.runtime.base_agent import BaseAgent
from app.agents.runtime.result import AgentResult
from app.agents.runtime.context import ExecutionContext
from app.agents.registry.registry import register_agent
from app.agents.prompts.sales_strategy_prompts import (
    SALES_STRATEGY_AGENT_SYSTEM_PROMPT,
    SALES_STRATEGY_AGENT_USER_PROMPT,
)
from app.ai.providers.factory import get_llm_provider

logger = logging.getLogger("backend.agents.business.sales_strategy")


@register_agent
class SalesStrategyAgent(BaseAgent):
    """Production Sales Strategy Agent producing evidence-based, personalized sales strategies."""

    agent_id: str = "sales_strategy_agent"
    name: str = "Sales Strategy Agent"
    version: str = "1.0.0"
    description: str = "Analyzes company research and memory context to produce a complete sales strategy: pain points, buying signals, value proposition, objection handling, discovery questions, priority scoring, and next actions."
    capabilities: List[str] = [
        "pain_point_analysis",
        "buying_signal_detection",
        "value_proposition_generation",
        "objection_handling",
        "discovery_question_generation",
        "priority_scoring",
        "next_action_planning",
    ]

    def __init__(self):
        super().__init__()
        self.llm_provider = get_llm_provider("lead_scorer")

    async def execute(self, context: ExecutionContext) -> AgentResult:
        """Produce a complete sales strategy from research and memory context."""
        self.log(f"SalesStrategyAgent executing for lead_id='{context.lead_id}' (job: {context.job_id})")

        research_output = context.inputs.get("research_output", {})
        memory_output = context.inputs.get("memory_output", {})
        company_name = research_output.get("company_name", context.inputs.get("company_name", "Target Company"))

        self.log(f"Building sales strategy for '{company_name}' using research + memory context...")

        user_prompt = SALES_STRATEGY_AGENT_USER_PROMPT.format(
            company_name=company_name,
            lead_id=context.lead_id or "N/A",
            goal=context.goal,
            research_context=json.dumps(research_output, indent=2, default=str)[:3000],
            memory_context=json.dumps(memory_output, indent=2, default=str)[:2000],
        )

        raw_response = await self.llm_provider.complete(
            prompt=user_prompt,
            system_prompt=SALES_STRATEGY_AGENT_SYSTEM_PROMPT,
        )

        parsed = self._parse_llm_json(raw_response, company_name=company_name)
        confidence = parsed.get("confidence", 75)
        priority = parsed.get("priority", "medium")

        artifact = {
            "name": f"sales_strategy_{context.lead_id or 'no_lead'}.json",
            "type": "sales_strategy",
            "content": parsed,
        }
        self.artifacts.append(artifact)

        self.log(f"SalesStrategyAgent completed. Priority={priority}, Confidence={confidence}")

        return AgentResult(
            status="completed",
            confidence=confidence,
            messages=[
                f"Sales strategy completed for '{company_name}'.",
                f"Opportunity priority: {priority.upper()}.",
                f"Identified {len(parsed.get('pain_points', []))} pain points and {len(parsed.get('buying_signals', []))} buying signals.",
                f"Generated {len(parsed.get('objection_handling', []))} objection responses and {len(parsed.get('discovery_questions', []))} discovery questions.",
            ],
            logs=self.logs,
            artifacts=self.artifacts,
            outputs=parsed,
            metadata={"agent_type": "sales_strategy", "priority": priority, "company_name": company_name},
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
                "strategic_summary": f"Sales strategy analysis in progress for {company_name}.",
                "pain_points": [],
                "buying_signals": [],
                "budget_indicators": [],
                "decision_maker_strategy": "Research key decision makers via LinkedIn and company website.",
                "value_proposition": f"Our platform helps companies like {company_name} achieve their growth objectives.",
                "unique_differentiators": [],
                "objection_handling": [],
                "discovery_questions": [
                    "What are your biggest challenges in this area today?",
                    "What does success look like for your team in the next 6-12 months?",
                    "What have you tried previously and why did it not work?",
                ],
                "recommended_approach": "cold_outreach",
                "priority": "medium",
                "priority_reasoning": "Insufficient data to fully qualify opportunity.",
                "next_actions": [],
                "confidence": 40,
            }
