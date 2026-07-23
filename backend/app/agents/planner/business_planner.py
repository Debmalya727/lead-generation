"""
BusinessAgentPlannerEngine — Phase 11 Milestone 2.

Extends PlannerEngine to produce the canonical 6-agent business pipeline DAG
when a lead_id is provided or execution_mode == "business_pipeline".

DAG:
  task_01_research  → task_02_memory → task_03_strategy
                                         → task_04_outreach → task_05_review → task_06_executive

Output passthrough:
  Each task's outputs are passed as inputs to dependent tasks via inputs dict.
"""
import uuid
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timezone

from app.agents.planner.planner import PlannerEngine
from app.database.mongodb.collections.agent_runtime import ExecutionPlan, ExecutionTask

logger = logging.getLogger("backend.agents.planner.business_planner")


class BusinessAgentPlannerEngine(PlannerEngine):
    """
    Business-aware planner that constructs the canonical 6-agent pipeline DAG.

    When lead_id is provided OR execution_mode is 'business_pipeline',
    this planner bypasses LLM DAG generation and constructs the pre-wired
    deterministic 6-task sales intelligence pipeline.
    """

    async def create_plan(
        self,
        goal: str,
        lead_id: Optional[str] = None,
        execution_mode: str = "auto",
        company_name: Optional[str] = None,
    ) -> ExecutionPlan:
        """Create business pipeline plan or fall back to generic LLM planner."""

        if execution_mode == "business_pipeline" or lead_id:
            logger.info(f"BusinessAgentPlannerEngine building 6-agent business pipeline DAG for lead_id='{lead_id}'")
            return self._build_business_pipeline(goal=goal, lead_id=lead_id, company_name=company_name)

        # Fall back to generic LLM-driven planner for non-lead goals
        logger.info("Falling back to generic PlannerEngine for non-lead goal.")
        return await super().create_plan(goal=goal, lead_id=lead_id)

    def _build_business_pipeline(
        self,
        goal: str,
        lead_id: Optional[str],
        company_name: Optional[str],
    ) -> ExecutionPlan:
        """Build the canonical deterministic 6-agent sales intelligence pipeline DAG."""
        plan_id = f"biz_plan_{uuid.uuid4().hex[:12]}"
        target = company_name or "Target Company"

        tasks = [
            ExecutionTask(
                task_id="task_01_research",
                name="Company Intelligence Research",
                agent_name="research_agent",
                description=f"Retrieve and synthesize company intelligence for '{target}' from research reports, company intelligence, lead scores, and sales intelligence modules.",
                dependencies=[],
                priority=1,
                parallelizable=False,
                approval_required=False,
                status="pending",
                inputs={"company_name": target, "lead_id": lead_id or ""},
            ),
            ExecutionTask(
                task_id="task_02_memory",
                name="Memory & Relationship Context",
                agent_name="memory_agent",
                description=f"Query vector search and RAG pipeline to retrieve relationship history, campaign data, email history, and knowledge context for '{target}'.",
                dependencies=["task_01_research"],
                priority=2,
                parallelizable=False,
                approval_required=False,
                status="pending",
                inputs={"company_name": target, "lead_id": lead_id or ""},
            ),
            ExecutionTask(
                task_id="task_03_strategy",
                name="Sales Strategy Development",
                agent_name="sales_strategy_agent",
                description=f"Analyze research and memory context to produce pain points, buying signals, value proposition, objection handling, and discovery questions for '{target}'.",
                dependencies=["task_01_research", "task_02_memory"],
                priority=3,
                parallelizable=False,
                approval_required=False,
                status="pending",
                inputs={"company_name": target, "lead_id": lead_id or ""},
            ),
            ExecutionTask(
                task_id="task_04_outreach",
                name="Multi-Channel Outreach Generation",
                agent_name="outreach_agent",
                description=f"Generate personalized cold email, LinkedIn message, call script, meeting request, and follow-up sequence for '{target}'.",
                dependencies=["task_01_research", "task_02_memory", "task_03_strategy"],
                priority=4,
                parallelizable=False,
                approval_required=False,
                status="pending",
                inputs={"company_name": target, "lead_id": lead_id or ""},
            ),
            ExecutionTask(
                task_id="task_05_review",
                name="Quality Audit & Review",
                agent_name="review_agent",
                description="Audit all agent outputs for hallucinations, contradictions, missing sources, low confidence flags, and compliance issues.",
                dependencies=["task_01_research", "task_02_memory", "task_03_strategy", "task_04_outreach"],
                priority=5,
                parallelizable=False,
                approval_required=False,
                status="pending",
                inputs={},
            ),
            ExecutionTask(
                task_id="task_06_executive",
                name="Executive Report Synthesis",
                agent_name="executive_agent",
                description=f"Synthesize all agent outputs into a final executive sales report with opportunity score, sales playbook, risk assessment, recommended actions, and 30-day execution checklist for '{target}'.",
                dependencies=["task_01_research", "task_02_memory", "task_03_strategy", "task_04_outreach", "task_05_review"],
                priority=6,
                parallelizable=False,
                approval_required=False,
                status="pending",
                inputs={"company_name": target, "lead_id": lead_id or ""},
            ),
        ]

        graph_json = {
            "nodes": [
                {"id": t.task_id, "label": t.name, "agent": t.agent_name, "status": t.status, "priority": t.priority}
                for t in tasks
            ],
            "edges": [
                {"source": dep, "target": t.task_id}
                for t in tasks
                for dep in t.dependencies
            ],
            "pipeline_type": "business_pipeline",
        }

        plan = ExecutionPlan(
            plan_id=plan_id,
            goal=goal,
            tasks=tasks,
            task_graph_json=graph_json,
            created_at=datetime.now(timezone.utc),
        )

        logger.info(f"BusinessAgentPlannerEngine built 6-node pipeline DAG '{plan_id}' for goal='{goal[:50]}'")
        return plan
