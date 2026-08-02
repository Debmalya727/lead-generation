"""
ExecutiveAgent — Phase 11 Milestone 2 Business Agent.

Synthesizes all agent outputs into a final executive-grade sales deliverable:
- Executive summary
- Sales playbook (4 phases)
- Risk assessment
- Recommended actions (prioritized, time-bound)
- Execution checklist (30-day)
- Overall confidence score

Persists the consolidated ExecutiveReport to MongoDB.
"""
import json
import uuid
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from app.agents.runtime.base_agent import BaseAgent
from app.agents.runtime.result import AgentResult
from app.agents.runtime.context import ExecutionContext
from app.agents.registry.registry import register_agent
from app.agents.prompts.executive_prompts import (
    EXECUTIVE_AGENT_SYSTEM_PROMPT,
    EXECUTIVE_AGENT_USER_PROMPT,
)
from app.ai.providers.factory import get_llm_provider

logger = logging.getLogger("backend.agents.business.executive")


@register_agent
class ExecutiveAgent(BaseAgent):
    """Production Executive Agent synthesizing all agent intelligence into a final enterprise sales deliverable."""

    agent_id: str = "executive_agent"
    name: str = "Executive Agent"
    version: str = "1.0.0"
    description: str = "Synthesizes all agent outputs into a final executive sales report: executive summary, sales playbook, risk assessment, recommended actions, and 30-day execution checklist. Persists the report to MongoDB."
    capabilities: List[str] = [
        "executive_summary_generation",
        "sales_playbook_construction",
        "risk_assessment",
        "action_recommendation",
        "execution_checklist_generation",
        "report_persistence",
        "multi_agent_synthesis",
    ]

    def __init__(self):
        super().__init__()
        self.llm_provider = get_llm_provider("manager")

    async def execute(self, context: ExecutionContext) -> AgentResult:
        """Synthesize all agent outputs into a final executive report."""
        self.log(f"ExecutiveAgent synthesizing final report for job_id='{context.job_id}'")

        research_output = context.inputs.get("research_output", {})
        memory_output = context.inputs.get("memory_output", {})
        strategy_output = context.inputs.get("strategy_output", {})
        outreach_output = context.inputs.get("outreach_output", {})
        review_output = context.inputs.get("review_output", {})

        company_name = research_output.get("company_name", context.inputs.get("company_name", "Target Company"))
        self.log(f"Generating executive report for '{company_name}'...")

        user_prompt = EXECUTIVE_AGENT_USER_PROMPT.format(
            company_name=company_name,
            lead_id=context.lead_id or "N/A",
            goal=context.goal,
            research_output=json.dumps(research_output, indent=2, default=str)[:2000],
            memory_output=json.dumps(memory_output, indent=2, default=str)[:1000],
            strategy_output=json.dumps(strategy_output, indent=2, default=str)[:2000],
            outreach_output=json.dumps(outreach_output, indent=2, default=str)[:1500],
            review_output=json.dumps(review_output, indent=2, default=str)[:1000],
        )

        raw_response = await self.llm_provider.complete(
            prompt=user_prompt,
            system_prompt=EXECUTIVE_AGENT_SYSTEM_PROMPT,
        )

        parsed = self._parse_llm_json(raw_response, company_name=company_name)
        overall_confidence = parsed.get("overall_confidence", 78)
        opportunity_score = parsed.get("opportunity_score", 75)

        # Persist to MongoDB
        report_id = await self._persist_executive_report(
            job_id=context.job_id,
            lead_id=context.lead_id,
            owner_id=context.owner_id,
            goal=context.goal,
            company_name=company_name,
            executive_data=parsed,
            research_output=research_output,
            memory_output=memory_output,
            strategy_output=strategy_output,
            outreach_output=outreach_output,
            review_output=review_output,
        )

        artifact = {
            "name": f"executive_report_{context.job_id}.json",
            "type": "executive_report",
            "report_id": report_id,
            "content": parsed,
        }
        self.artifacts.append(artifact)

        self.log(f"ExecutiveAgent completed. Report saved (ID: {report_id}). Opportunity score={opportunity_score}, Confidence={overall_confidence}")

        return AgentResult(
            status="completed",
            confidence=overall_confidence,
            messages=[
                f"Executive report generated for '{company_name}'.",
                f"Opportunity score: {opportunity_score}/100.",
                f"Overall confidence: {overall_confidence}%.",
                f"Report ID: {report_id}.",
                f"Generated {len(parsed.get('recommended_actions', []))} recommended actions and {len(parsed.get('execution_checklist', []))} checklist items.",
            ],
            logs=self.logs,
            artifacts=self.artifacts,
            outputs={**parsed, "report_id": report_id},
            metadata={"agent_type": "executive", "report_id": report_id, "company_name": company_name, "opportunity_score": opportunity_score},
        )

    async def _persist_executive_report(
        self,
        job_id: str,
        lead_id: Optional[str],
        owner_id: str,
        goal: str,
        company_name: str,
        executive_data: Dict[str, Any],
        research_output: Dict[str, Any],
        memory_output: Dict[str, Any],
        strategy_output: Dict[str, Any],
        outreach_output: Dict[str, Any],
        review_output: Dict[str, Any],
    ) -> str:
        """Persist ExecutiveReport document to MongoDB."""
        report_id = f"rpt_{uuid.uuid4().hex[:12]}"
        try:
            from app.database.mongodb.collections.executive_report import ExecutiveReport
            from beanie import PydanticObjectId

            l_id = None
            if lead_id and PydanticObjectId.is_valid(str(lead_id)):
                l_id = PydanticObjectId(str(lead_id))

            if owner_id and PydanticObjectId.is_valid(str(owner_id)):
                o_id = PydanticObjectId(str(owner_id))
            else:
                o_id = PydanticObjectId()

            report = ExecutiveReport(
                report_id=report_id,
                job_id=job_id,
                lead_id=l_id,
                owner_id=o_id,
                goal=goal,
                company_name=company_name,
                executive_summary=executive_data.get("executive_summary", ""),
                opportunity_score=executive_data.get("opportunity_score", 0),
                sales_playbook=executive_data.get("sales_playbook", {}),
                top_pain_points=executive_data.get("top_pain_points", []),
                winning_value_proposition=executive_data.get("winning_value_proposition", ""),
                key_differentiators=executive_data.get("key_differentiators", []),
                risk_assessment=executive_data.get("risk_assessment", []),
                recommended_actions=executive_data.get("recommended_actions", []),
                execution_checklist=executive_data.get("execution_checklist", []),
                best_outreach_channel=executive_data.get("best_outreach_channel", "email"),
                estimated_deal_size=executive_data.get("estimated_deal_size", "Unknown"),
                estimated_close_timeline=executive_data.get("estimated_close_timeline", "Unknown"),
                overall_confidence=executive_data.get("overall_confidence", 0),
                data_quality_notes=executive_data.get("data_quality_notes", ""),
                research_section=research_output,
                memory_section=memory_output,
                strategy_section=strategy_output,
                outreach_section=outreach_output,
                review_section=review_output,
                created_at=datetime.now(timezone.utc),
            )
            await report.insert()
            self.log(f"ExecutiveReport '{report_id}' persisted to MongoDB.")
        except Exception as e:
            self.log(f"ExecutiveReport persistence warning: {str(e)}")

        return report_id

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
                "executive_summary": f"{company_name} represents a B2B sales opportunity. Complete intelligence has been gathered across research, memory, strategy, and outreach dimensions. Review the individual agent outputs for detailed insights.",
                "opportunity_score": 65,
                "sales_playbook": {
                    "phase_1_research": ["Research complete — see research agent outputs."],
                    "phase_2_outreach": ["Use generated outreach templates."],
                    "phase_3_discovery": ["Run discovery call using generated questions."],
                    "phase_4_proposal": ["Tailor proposal to identified pain points."],
                },
                "top_pain_points": [],
                "winning_value_proposition": f"Our platform helps {company_name} achieve measurable growth.",
                "key_differentiators": [],
                "risk_assessment": [{"risk": "Insufficient data confidence", "severity": "medium", "mitigation": "Gather more intelligence before outreach."}],
                "recommended_actions": [{"action": "Review all agent outputs", "priority": "high", "timeline": "Today", "owner": "AE"}],
                "execution_checklist": [{"task": "Review executive report", "due": "Day 1", "status": "pending"}],
                "best_outreach_channel": "email",
                "estimated_deal_size": "Unknown",
                "estimated_close_timeline": "Unknown",
                "overall_confidence": 50,
                "data_quality_notes": "Fallback report generated due to LLM parse error.",
            }
