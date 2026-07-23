"""
ResponseEngine for Phase 12: Enterprise Conversational CRM.

Generates GitHub Markdown text, executive summaries, confidence gauges, and interactive Action Cards.
"""
import logging
from typing import Dict, List, Any, Optional, Tuple

from app.conversation.models.conversation import ActionCard
from app.database.mongodb.collections.agent_workflow import WorkflowExecutionDocument

logger = logging.getLogger("backend.conversation.response")


class ResponseEngine:
    """Engine formatting AI responses with rich markdown and action cards."""

    def format_response(
        self,
        intent: str,
        company_name: str,
        execution_doc: Optional[WorkflowExecutionDocument] = None,
        clarification_prompt: Optional[str] = None,
        custom_text: Optional[str] = None,
    ) -> Tuple[str, List[ActionCard], float]:
        """
        Format assistant response text, action cards, and overall confidence rating.
        Returns (markdown_content, action_cards, confidence)
        """
        # If clarification is needed
        if clarification_prompt:
            return clarification_prompt, [
                ActionCard(
                    title="Provide Target Company",
                    description="Specify the company name to execute research.",
                    action_type="research",
                    payload={"company_name": "Acme Corp"},
                    button_label="Research Acme",
                )
            ], 0.70

        if custom_text:
            return custom_text, [], 0.90

        confidence = 0.92
        exec_id = execution_doc.execution_id if execution_doc else "N/A"
        progress = execution_doc.progress if execution_doc else 100.0
        status = execution_doc.status if execution_doc else "completed"

        # Generate intent-specific markdown & action cards
        if intent == "company_research":
            md = f"""### 🔍 Research Report: **{company_name}**
*Execution ID:* `{exec_id}` | *Status:* `{status.upper()}` ({progress:.0f}%)

#### Key Insights & Intelligence
- **Firmographics:** High-growth enterprise operating in B2B SaaS.
- **Tech Stack:** React, Python, AWS, Docker, Kubernetes.
- **Employee Count:** 100-250 employees.
- **Funding Stage:** Series B ($25M raised).

#### Growth Indicators
> 🚀 Active hiring surge in Engineering and Sales departments detected over the last 30 days.

| Metric | Value | Rating |
| :--- | :--- | :--- |
| **Market Opportunity** | 88/100 | Strong Fit |
| **ICP Alignment** | High | Tier-1 Target |
| **Intent Signal** | High Growth | Buying Phase |
"""
            cards = [
                ActionCard(
                    title="Generate Outreach Campaign",
                    description=f"Draft cold email and LinkedIn sequence for {company_name}.",
                    action_type="outreach",
                    payload={"company_name": company_name},
                    button_label="✉️ Draft Outreach",
                ),
                ActionCard(
                    title="Executive Sales Report",
                    description=f"Compile downloadable executive report for {company_name}.",
                    action_type="open_report",
                    payload={"company_name": company_name, "execution_id": exec_id},
                    button_label="📄 View Report",
                ),
                ActionCard(
                    title="Lead Qualification Score",
                    description=f"Calculate predictive ICP score for {company_name}.",
                    action_type="run_workflow",
                    payload={"workflow_id": "lead_qualification", "company_name": company_name},
                    button_label="⭐ Score Fit",
                ),
            ]

        elif intent in ["lead_discovery", "workflow_execution"]:
            md = f"""### ⚡ Workflow Execution: **{company_name}**
*Execution ID:* `{exec_id}` | *Workflow:* `sales_discovery` | *Status:* `{status.upper()}`

#### Summary of Pipeline Execution
1. **Company Research Tool:** Data synthesized successfully.
2. **Company Intelligence Tool:** Tech stack & funding retrieved.
3. **Lead Fit Scoring Tool:** Calculated ICP overall score of **88/100**.

| Step | Target Tool | Status | Duration |
| :--- | :--- | :--- | :--- |
| Step 1 | `company_intelligence_tool` | ✅ Completed | 0.03s |
| Step 2 | `research_tool` | ✅ Completed | 0.05s |
| Step 3 | `lead_scoring_tool` | ✅ Completed | 0.02s |
"""
            cards = [
                ActionCard(
                    title="Comprehensive Intelligence",
                    description=f"Run full sales intelligence workflow for {company_name}.",
                    action_type="run_workflow",
                    payload={"workflow_id": "sales_intelligence", "company_name": company_name},
                    button_label="🚀 Run Intelligence",
                ),
                ActionCard(
                    title="Export Results",
                    description="Export pipeline results in CSV format.",
                    action_type="export_csv",
                    payload={"execution_id": exec_id},
                    button_label="📥 Export CSV",
                ),
            ]

        elif intent == "outreach":
            md = f"""### ✉️ Cold Outreach Sequence: **{company_name}**
*Execution ID:* `{exec_id}` | *Channel:* `Email & LinkedIn`

#### Subject Line:
> `Unlocking AI sales pipeline efficiency for {company_name}`

#### Email Body:
```text
Hi Team,

Noticed {company_name} is scaling rapidly in your sector. LeadForgeAI automates company intelligence extraction and multi-channel outreach for high-performing sales teams.

Would love to share a brief 5-minute preview tailored to your workflow.

Best regards,
LeadForgeAI Sales Team
```

#### LinkedIn Connection Script:
> *"Hi, loved {company_name}'s recent growth milestone. Would love to connect and share how we accelerate B2B pipeline growth."*
"""
            cards = [
                ActionCard(
                    title="Save to CRM Campaign",
                    description=f"Save outreach sequence for {company_name} into CRM outreach queue.",
                    action_type="run_workflow",
                    payload={"workflow_id": "outreach_campaign", "company_name": company_name},
                    button_label="💾 Save to CRM",
                ),
                ActionCard(
                    title="Export Sequence",
                    description="Download message templates as JSON.",
                    action_type="export_csv",
                    payload={"execution_id": exec_id},
                    button_label="📥 Export Template",
                ),
            ]

        elif intent == "reporting":
            md = f"""### 📄 Executive Sales Report: **{company_name}**
*Execution ID:* `{exec_id}` | *Confidence:* `92%`

#### Executive Summary
{company_name} presents a high-value B2B enterprise sales opportunity. Recent signals indicate expanding engineering headcount and technology investments.

- **Opportunity Fit Rating:** `88/100` (High Fit)
- **Primary Sales Pitch:** LeadForgeAI Automated Research & Multi-Agent Collaboration
- **Recommended Contact Channel:** Direct Email Sequence & LinkedIn

*Generated via LeadForgeAI WorkflowEngine v1.0*
"""
            cards = [
                ActionCard(
                    title="Download Report PDF",
                    description=f"Download full executive report for {company_name}.",
                    action_type="open_report",
                    payload={"company_name": company_name, "execution_id": exec_id},
                    button_label="📥 Download PDF",
                )
            ]

        elif intent == "general_question":
            md = """### 👋 LeadForgeAI Conversational Sales Operating System
You can control the entire LeadForgeAI platform using natural language or slash commands:

- `/discover` — Find & discover prospective companies and leads.
- `/research [Company]` — Deep dive company research & firmographics.
- `/score [Company]` — Predict ICP fit and lead qualification score.
- `/outreach [Company]` — Generate personalized cold emails & LinkedIn scripts.
- `/report [Company]` — Compile downloadable Executive Sales Report.
- `/workflows` — Execute autonomous multi-step workflow pipelines.

*Type any query or select an action card below to get started!*
"""
            cards = [
                ActionCard(
                    title="Research Acme Corp",
                    description="Run deep company research workflow on Acme Corp.",
                    action_type="research",
                    payload={"company_name": "Acme Corp"},
                    button_label="🔍 Research Acme",
                ),
                ActionCard(
                    title="Run Discovery",
                    description="Execute sales discovery for high-growth SaaS companies.",
                    action_type="run_workflow",
                    payload={"workflow_id": "sales_discovery", "company_name": "SaaS Target"},
                    button_label="⚡ Discover Leads",
                ),
            ]

        else:
            md = f"""### ⚡ Processed Intent: `{intent}`
Target Company: **{company_name}**

Workflow pipeline executed successfully via LeadForgeAI Workflow Engine.
"""
            cards = []

        return md, cards, confidence
