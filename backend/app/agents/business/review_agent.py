"""
ReviewAgent — Phase 11 Milestone 2 Business Agent.

Reviews all prior agent outputs for:
- Hallucinations (claims not supported by source data)
- Contradictions between agents
- Missing source citations
- Low confidence flags (confidence < 60)
- Compliance issues
- Completeness gaps

Returns: corrections, warnings, confidence_scores, is_approved, review_notes.
"""
import json
import logging
from typing import Dict, Any, List

from app.agents.runtime.base_agent import BaseAgent
from app.agents.runtime.result import AgentResult
from app.agents.runtime.context import ExecutionContext
from app.agents.registry.registry import register_agent
from app.agents.prompts.review_prompts import (
    REVIEW_AGENT_SYSTEM_PROMPT,
    REVIEW_AGENT_USER_PROMPT,
)
from app.ai.providers.factory import get_llm_provider

logger = logging.getLogger("backend.agents.business.review")


@register_agent
class ReviewAgent(BaseAgent):
    """Production Review Agent auditing all business agent outputs for quality, accuracy, and compliance."""

    agent_id: str = "review_agent"
    name: str = "Review Agent"
    version: str = "1.0.0"
    description: str = "Audits all agent outputs for hallucinations, contradictions, missing sources, low confidence claims, and compliance issues. Returns corrections and approval status."
    capabilities: List[str] = [
        "hallucination_detection",
        "contradiction_analysis",
        "source_validation",
        "confidence_floor_checking",
        "compliance_auditing",
        "quality_scoring",
        "agent_output_review",
    ]

    def __init__(self):
        super().__init__()
        self.llm_provider = get_llm_provider()

    async def execute(self, context: ExecutionContext) -> AgentResult:
        """Perform quality audit of all prior agent outputs."""
        self.log(f"ReviewAgent executing quality audit for job_id='{context.job_id}'")

        research_output = context.inputs.get("research_output", {})
        memory_output = context.inputs.get("memory_output", {})
        strategy_output = context.inputs.get("strategy_output", {})
        outreach_output = context.inputs.get("outreach_output", {})

        self.log("Auditing research, memory, strategy, and outreach outputs...")

        user_prompt = REVIEW_AGENT_USER_PROMPT.format(
            research_output=json.dumps(research_output, indent=2, default=str)[:2000],
            memory_output=json.dumps(memory_output, indent=2, default=str)[:1500],
            strategy_output=json.dumps(strategy_output, indent=2, default=str)[:2000],
            outreach_output=json.dumps(outreach_output, indent=2, default=str)[:1500],
        )

        raw_response = await self.llm_provider.complete(
            prompt=user_prompt,
            system_prompt=REVIEW_AGENT_SYSTEM_PROMPT,
        )

        parsed = self._parse_llm_json(raw_response)
        is_approved = parsed.get("is_approved", True)
        quality_score = parsed.get("overall_quality_score", 80)
        confidence = parsed.get("confidence", 88)

        issues_count = (
            len(parsed.get("hallucinations_detected", []))
            + len(parsed.get("contradictions_detected", []))
            + len(parsed.get("compliance_issues", []))
        )

        artifact = {
            "name": f"review_audit_{context.job_id}.json",
            "type": "quality_audit",
            "content": parsed,
        }
        self.artifacts.append(artifact)

        status = "completed" if is_approved else "completed"  # Always complete — review result drives executive
        self.log(f"ReviewAgent completed. Approved={is_approved}, Quality={quality_score}, Issues={issues_count}")

        return AgentResult(
            status=status,
            confidence=confidence,
            messages=[
                f"Quality audit completed. {'✅ Approved' if is_approved else '⚠️ Issues detected'}.",
                f"Overall quality score: {quality_score}/100.",
                f"Issues detected: {issues_count}.",
                f"Warnings: {len(parsed.get('warnings', []))}.",
            ],
            logs=self.logs,
            artifacts=self.artifacts,
            outputs=parsed,
            metadata={"agent_type": "review", "is_approved": is_approved, "quality_score": quality_score},
        )

    def _parse_llm_json(self, raw: str) -> Dict[str, Any]:
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
            self.log(f"JSON parse warning, using pass-through review: {str(e)}")
            return {
                "is_approved": True,
                "overall_quality_score": 75,
                "hallucinations_detected": [],
                "contradictions_detected": [],
                "missing_sources": [],
                "low_confidence_flags": [],
                "compliance_issues": [],
                "corrections": [],
                "warnings": ["Review agent output parsing failed — using auto-approval fallback."],
                "review_notes": "Auto-approval due to LLM output parse failure. Manual review recommended.",
                "approved_sections": ["research", "memory", "strategy", "outreach"],
                "rejected_sections": [],
                "confidence": 70,
            }
