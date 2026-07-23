"""
ConversationPlanner for Phase 12: Enterprise Conversational CRM.

Translates classified natural language intent & entities into formal Workflow Engine plans.
Conversation NEVER bypasses the Workflow Engine.
"""
import logging
from typing import Dict, Any, Tuple, Optional

from app.agents.workflow.workflow_engine.engine import WorkflowEngine
from app.database.mongodb.collections.agent_workflow import WorkflowExecutionDocument

logger = logging.getLogger("backend.conversation.planner")


class ConversationPlanner:
    """Planner mapping natural language intent into executable Workflow Engine plans."""

    INTENT_TO_TEMPLATE = {
        "lead_discovery": "sales_discovery",
        "company_research": "company_research",
        "lead_scoring": "lead_qualification",
        "sales_intelligence": "sales_intelligence",
        "outreach": "outreach_campaign",
        "reporting": "executive_report_gen",
        "workflow_execution": "sales_discovery",
    }

    SLASH_TO_TEMPLATE = {
        "discover": "sales_discovery",
        "research": "company_research",
        "outreach": "outreach_campaign",
        "report": "executive_report_gen",
        "score": "lead_qualification",
        "workflows": "sales_intelligence",
    }

    def __init__(self):
        self.workflow_engine = WorkflowEngine()

    async def plan_and_execute(
        self,
        intent: str,
        entities: Dict[str, Any],
        owner_id: str,
        slash_command: Optional[str] = None,
    ) -> Tuple[str, WorkflowExecutionDocument, Dict[str, Any]]:
        """
        Create workflow execution plan and invoke Workflow Engine.
        Returns (template_id, execution_doc, plan_summary)
        """
        # 1. Resolve workflow template ID
        template_id = "sales_discovery"
        if slash_command and slash_command in self.SLASH_TO_TEMPLATE:
            template_id = self.SLASH_TO_TEMPLATE[slash_command]
        elif entities.get("workflow_name"):
            template_id = entities["workflow_name"]
        elif intent in self.INTENT_TO_TEMPLATE:
            template_id = self.INTENT_TO_TEMPLATE[intent]

        company_name = entities.get("company_name", "Target Account")
        lead_id = entities.get("lead_id")

        plan_summary = {
            "intent": intent,
            "selected_template": template_id,
            "company_name": company_name,
            "entities_used": entities,
            "orchestration_layer": "WorkflowEngine v1.0",
        }

        logger.info(f"ConversationPlanner: Executing template '{template_id}' via WorkflowEngine for '{company_name}'")

        # 2. Invoke Workflow Engine (Strict Workflow Engine Routing)
        execution_doc = await self.workflow_engine.run_workflow(
            workflow_id=template_id,
            owner_id=owner_id,
            company_name=company_name,
            lead_id=lead_id,
            custom_inputs=entities,
        )

        return template_id, execution_doc, plan_summary
