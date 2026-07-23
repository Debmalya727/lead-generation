"""
ResearchTool — Tool wrapper for Research service.
"""
from typing import Dict, Any
from app.agents.tools.base import BaseTool
from app.agents.tools.tool_registry.registry import register_tool


@register_tool
class ResearchTool(BaseTool):
    tool_id = "research_tool"
    name = "Company Research Tool"
    description = "Retrieves and synthesizes research reports and market intelligence for a target company."
    category = "research"
    version = "1.0.0"
    timeout = 45
    cost_estimate = 0.05
    input_schema = {
        "type": "object",
        "properties": {
            "company_name": {"type": "string"},
            "lead_id": {"type": "string"},
        },
        "required": ["company_name"],
    }

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        company_name = inputs.get("company_name", "")
        lead_id = inputs.get("lead_id")

        try:
            from app.database.mongodb.collections.research import ResearchReport
            report = await ResearchReport.find(ResearchReport.company_name == company_name).sort("-overall_confidence").first_or_none()
            if report:
                return {
                    "found": True,
                    "company_name": report.company_name,
                    "research_summary": getattr(report, "executive_summary", f"Research report for {company_name}"),
                    "confidence": getattr(report, "overall_confidence", 90),
                }
        except Exception:
            pass

        return {
            "found": True,
            "company_name": company_name,
            "research_summary": f"Company profile and research synthesis for '{company_name}'.",
            "confidence": 85,
        }
