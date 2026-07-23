"""
SchedulerService for Section 13: Background Scheduler Architecture.

Manages recurring cron workflows, delayed executions, and periodic maintenance jobs.
Integrates directly with WorkflowEngine.run_workflow().
"""
import uuid
import time
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple

from app.database.mongodb.collections.platform_extended import (
    ScheduledJobDocument,
    JobHistoryDocument,
)
from app.events.event_bus.bus import event_bus
from app.events.schemas.events import PlatformEvent

logger = logging.getLogger("backend.scheduler")


class SchedulerService:
    """Service orchestrating background cron jobs and scheduled workflow triggers."""

    PREBUILT_JOBS = [
        {
            "job_id": "job_nightly_refresh",
            "name": "Nightly Target Lead Refresh",
            "description": "Scrapes and enriches new industry target leads every night at 2 AM",
            "workflow_template_id": "sales_discovery",
            "cron_expression": "0 2 * * *",
            "priority": "high",
        },
        {
            "job_id": "job_weekly_research",
            "name": "Weekly Deep Company Intelligence",
            "description": "Performs deep company research and growth signal analysis every Monday",
            "workflow_template_id": "company_research",
            "cron_expression": "0 6 * * 1",
            "priority": "medium",
        },
        {
            "job_id": "job_monthly_reports",
            "name": "Monthly Executive Sales Reports",
            "description": "Generates C-level executive summary reports on the 1st of each month",
            "workflow_template_id": "executive_report_gen",
            "cron_expression": "0 8 1 * *",
            "priority": "medium",
        },
        {
            "job_id": "job_auto_rescoring",
            "name": "Automatic Predictive Lead Rescoring",
            "description": "Re-evaluates intent scores and ICP fit for stale leads every 6 hours",
            "workflow_template_id": "sales_discovery",
            "cron_expression": "0 */6 * * *",
            "priority": "low",
        },
    ]

    async def initialize_prebuilt_jobs(self, owner_id: str = "system") -> None:
        """Seed prebuilt scheduler jobs if missing."""
        for p in self.PREBUILT_JOBS:
            existing = await ScheduledJobDocument.find_one(ScheduledJobDocument.job_id == p["job_id"])
            if not existing:
                doc = ScheduledJobDocument(
                    job_id=p["job_id"],
                    name=p["name"],
                    description=p["description"],
                    workflow_template_id=p["workflow_template_id"],
                    cron_expression=p["cron_expression"],
                    priority=p["priority"],
                    owner_id=owner_id,
                    is_active=True,
                )
                await doc.insert()

    async def create_job(
        self,
        name: str,
        workflow_template_id: str,
        owner_id: str,
        cron_expression: Optional[str] = None,
        interval_seconds: Optional[int] = None,
        inputs: Optional[Dict[str, Any]] = None,
        priority: str = "medium",
        description: str = "Custom scheduled workflow job",
    ) -> ScheduledJobDocument:
        """Create a new scheduled background workflow job."""
        job_id = f"job_{uuid.uuid4().hex[:12]}"
        doc = ScheduledJobDocument(
            job_id=job_id,
            name=name,
            description=description,
            workflow_template_id=workflow_template_id,
            cron_expression=cron_expression,
            interval_seconds=interval_seconds,
            inputs=inputs or {},
            priority=priority,
            owner_id=owner_id,
            is_active=True,
            created_at=datetime.now(timezone.utc),
        )
        await doc.insert()
        logger.info(f"SchedulerService: Created job '{job_id}' ('{name}')")
        return doc

    async def run_job_now(self, job_id: str, owner_id: str) -> Tuple[JobHistoryDocument, str]:
        """Manually trigger immediate execution of a scheduled job via WorkflowEngine."""
        start_t = time.time()
        job = await ScheduledJobDocument.find_one(ScheduledJobDocument.job_id == job_id)
        if not job:
            raise ValueError(f"Job with ID '{job_id}' not found.")

        # Invoke WorkflowEngine
        from app.agents.workflow.workflow_engine.engine import WorkflowEngine
        wf_engine = WorkflowEngine()

        exec_doc = await wf_engine.run_workflow(
            workflow_id=job.workflow_template_id,
            owner_id=owner_id,
            custom_inputs=job.inputs or {"company_name": "ScheduledTarget"},
        )

        duration_ms = round((time.time() - start_t) * 1000, 2)
        history_id = f"hist_{uuid.uuid4().hex[:12]}"

        hist = JobHistoryDocument(
            history_id=history_id,
            job_id=job_id,
            workflow_execution_id=exec_doc.execution_id,
            status=exec_doc.status,
            duration_ms=duration_ms,
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
        )
        await hist.insert()

        job.last_run_at = datetime.now(timezone.utc)
        job.run_count += 1
        await job.save()

        # Publish EventBus event
        await event_bus.publish(PlatformEvent(
            event_type="WorkflowCompleted" if exec_doc.status == "completed" else "WorkflowFailed",
            topic="workflows",
            user_id=owner_id,
            payload={"job_id": job_id, "execution_id": exec_doc.execution_id, "workflow_id": job.workflow_template_id},
        ))

        return hist, exec_doc.execution_id

    async def list_jobs(self, owner_id: Optional[str] = None) -> List[ScheduledJobDocument]:
        """List scheduled jobs."""
        if owner_id:
            return await ScheduledJobDocument.find(ScheduledJobDocument.owner_id == owner_id).to_list()
        return await ScheduledJobDocument.find_all().to_list()

    async def get_history(self, job_id: str, limit: int = 50) -> List[JobHistoryDocument]:
        """Fetch execution history for a job."""
        return await JobHistoryDocument.find(JobHistoryDocument.job_id == job_id).sort("-started_at").limit(limit).to_list()
