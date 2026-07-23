"""
OutreachTool — Tool wrapper for Outreach & Cold Campaign service.
"""
from typing import Dict, Any
from app.agents.tools.base import BaseTool
from app.agents.tools.tool_registry.registry import register_tool


@register_tool
class OutreachTool(BaseTool):
    tool_id = "outreach_tool"
    name = "Cold Outreach Generator Tool"
    description = "Generates personalized cold emails, LinkedIn connection scripts, and multi-touch sequences."
    category = "outreach"
    version = "1.0.0"
    timeout = 45
    cost_estimate = 0.04
    input_schema = {
        "type": "object",
        "properties": {
            "company_name": {"type": "string"},
            "value_proposition": {"type": "string"},
        },
        "required": ["company_name"],
    }

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        company_name = inputs.get("company_name", "")
        value_prop = inputs.get("value_proposition", f"Transform lead discovery for {company_name}")

        return {
            "company_name": company_name,
            "cold_email": {
                "subject": f"Unlocking AI sales pipeline efficiency for {company_name}",
                "body": f"Hi Team,\n\nNotice {company_name} is scaling rapidly. LeadForgeAI can automate lead intelligence and multi-channel outreach for your sales team.\n\nBest,\nLeadForgeAI Sales Team",
            },
            "linkedin_message": f"Hi, loved {company_name}'s recent growth milestone. Would love to connect and share how we accelerate B2B pipeline growth.",
            "best_channel": "Email",
            "confidence": 90,
        }
