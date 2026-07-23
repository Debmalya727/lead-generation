"""
Service Layer for Enterprise Agent Runtime Operations.
"""
import uuid
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone
from bson import ObjectId

from app.agents.planner.planner import PlannerEngine
from app.agents.planner.business_planner import BusinessAgentPlannerEngine
from app.agents.execution.execution_engine import ExecutionEngine
from app.agents.events.event_bus import EventBus
from app.database.mongodb.repositories.agent_repository import AgentRepository
from app.database.mongodb.collections.agent_runtime import AgentJob, AgentEvent, ExecutionPlan, ExecutionTask
from app.agents.tasks.agent_tasks import run_agent_job_task

logger = logging.getLogger("backend.agents.service")


class AgentService:
    """Service layer managing AgentJobs, DAG execution, events, and approvals."""

    def __init__(self, agent_repo: Optional[AgentRepository] = None):
        self.agent_repo = agent_repo or AgentRepository()
        self.planner_engine = PlannerEngine()
        self.business_planner_engine = BusinessAgentPlannerEngine()
        self.execution_engine = ExecutionEngine(self.agent_repo)
        self.event_bus = EventBus(self.agent_repo)

    async def submit_job(
        self,
        goal: str,
        owner_id: str,
        lead_id: Optional[str] = None,
        execution_mode: str = "auto",
        company_name: Optional[str] = None,
    ) -> AgentJob:
        """Construct DAG plan, create AgentJob document, and enqueue Celery worker execution task."""
        logger.info(f"AgentService submitting new AgentJob for goal='{goal[:40]}...' (owner: {owner_id}, mode: {execution_mode})")

        job_id = f"job_{uuid.uuid4().hex[:12]}"
        
        # 1. Build DAG Execution Plan — use BusinessAgentPlannerEngine for lead goals or business_pipeline mode
        use_business_pipeline = execution_mode == "business_pipeline" or bool(lead_id)
        if use_business_pipeline:
            plan: ExecutionPlan = await self.business_planner_engine.create_plan(
                goal=goal,
                lead_id=lead_id,
                execution_mode=execution_mode,
                company_name=company_name,
            )
        else:
            plan: ExecutionPlan = await self.planner_engine.create_plan(goal=goal, lead_id=lead_id)

        try:
            o_id = ObjectId(owner_id)
        except Exception:
            o_id = owner_id

        try:
            l_id = ObjectId(lead_id) if lead_id else None
        except Exception:
            l_id = lead_id

        # 2. Persist AgentJob document
        job_data = {
            "job_id": job_id,
            "goal": goal,
            "lead_id": l_id,
            "owner_id": o_id,
            "status": "pending",
            "progress": 0.0,
            "plan": plan,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }

        job = await self.agent_repo.create_job(job_data)

        # 3. Emit PlanCreated Event
        await self.event_bus.emit(
            job_id=job_id,
            owner_id=str(o_id),
            event_type="plan_created",
            payload={"plan_id": plan.plan_id, "task_count": len(plan.tasks)},
        )

        # 4. Enqueue Celery worker background task
        run_agent_job_task.delay(job_id, str(o_id))

        return job

    async def get_job(self, job_id: str, owner_id: str) -> Optional[AgentJob]:
        """Fetch job details."""
        return await self.agent_repo.get_job_by_id(job_id, owner_id)

    async def list_jobs(
        self,
        owner_id: str,
        status: Optional[str] = None,
        lead_id: Optional[str] = None,
        limit: int = 50,
        skip: int = 0,
    ) -> Tuple[List[AgentJob], int]:
        """List jobs for owner with filters."""
        return await self.agent_repo.list_jobs(owner_id=owner_id, status=status, lead_id=lead_id, limit=limit, skip=skip)

    async def get_job_events(self, job_id: str, owner_id: str) -> List[AgentEvent]:
        """Fetch all state transition events for a job."""
        return await self.agent_repo.list_events_for_job(job_id, owner_id)

    async def cancel_job(self, job_id: str, owner_id: str) -> AgentJob:
        """Cancel an active or pending job."""
        job = await self.agent_repo.get_job_by_id(job_id, owner_id)
        if not job:
            raise ValueError(f"Job '{job_id}' not found.")

        updated = await self.agent_repo.update_job(job, {"status": "cancelled", "completed_at": datetime.now(timezone.utc)})
        await self.event_bus.emit(
            job_id=job_id,
            owner_id=owner_id,
            event_type="execution_finished",
            payload={"status": "cancelled"},
        )
        return updated

    async def retry_job(self, job_id: str, owner_id: str) -> AgentJob:
        """Retry a failed or cancelled job."""
        job = await self.agent_repo.get_job_by_id(job_id, owner_id)
        if not job or not job.plan:
            raise ValueError(f"Job '{job_id}' not found.")

        # Reset failed/cancelled task statuses back to pending
        for t in job.plan.tasks:
            if t.status in ("failed", "cancelled"):
                t.status = "pending"
                t.error_message = None

        updated = await self.agent_repo.update_job(job, {
            "status": "pending",
            "plan": job.plan,
            "error_message": None,
        })

        run_agent_job_task.delay(job_id, owner_id)
        return updated

    async def approve_task_node(self, job_id: str, task_id: str, owner_id: str) -> AgentJob:
        """Approve a task node paused for human approval and resume job execution."""
        job = await self.agent_repo.get_job_by_id(job_id, owner_id)
        if not job or not job.plan:
            raise ValueError(f"Job '{job_id}' not found.")

        found = False
        for t in job.plan.tasks:
            if t.task_id == task_id and t.status == "paused_for_approval":
                t.status = "pending"
                t.approval_required = False  # Mark approved
                found = True
                break

        if not found:
            raise ValueError(f"Task node '{task_id}' not found or not in paused_for_approval state.")

        updated = await self.agent_repo.update_job(job, {
            "status": "running",
            "plan": job.plan,
        })

        # Resume execution via Celery task
        run_agent_job_task.delay(job_id, owner_id)
        return updated

    async def get_executive_report(self, job_id: str, owner_id: str):
        """Fetch the ExecutiveReport generated by ExecutiveAgent for a completed job."""
        try:
            from app.database.mongodb.collections.executive_report import ExecutiveReport
            from bson import ObjectId
            try:
                o_id = ObjectId(owner_id)
            except Exception:
                o_id = owner_id

            report = await ExecutiveReport.find_one(
                ExecutiveReport.job_id == job_id,
                ExecutiveReport.owner_id == o_id,
            )
            return report
        except Exception as e:
            logger.warning(f"get_executive_report failed: {str(e)}")
            return None

    def list_registered_agents(self) -> List[Dict[str, Any]]:
        """Return list of all registered agents and their capabilities."""
        from app.agents.registry.registry import AgentRegistry
        AgentRegistry.discover()
        return AgentRegistry.list_agents()
