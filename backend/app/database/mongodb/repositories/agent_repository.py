from datetime import datetime, timezone
from typing import List, Optional, Tuple, Dict, Any
from bson import ObjectId
from app.database.mongodb.collections.agent_runtime import AgentJob, AgentEvent, ExecutionPlan, ExecutionTask


class AgentRepository:
    """Repository for AgentJob & AgentEvent persistence with owner isolation."""

    async def create_job(self, job_data: dict) -> AgentJob:
        """Create a new AgentJob record."""
        job = AgentJob(**job_data)
        await job.insert()
        return job

    async def get_job_by_id(self, job_id: str, owner_id: str) -> Optional[AgentJob]:
        """Fetch AgentJob by job_id for owner."""
        try:
            o_id = ObjectId(owner_id)
        except Exception:
            o_id = owner_id

        return await AgentJob.find_one({"job_id": job_id, "owner_id": o_id})

    async def get_job_by_id_no_auth(self, job_id: str) -> Optional[AgentJob]:
        """Fetch AgentJob by job_id without owner check (used by Celery workers)."""
        return await AgentJob.find_one({"job_id": job_id})

    async def list_jobs(
        self,
        owner_id: str,
        status: Optional[str] = None,
        lead_id: Optional[str] = None,
        limit: int = 50,
        skip: int = 0,
    ) -> Tuple[List[AgentJob], int]:
        """List jobs with pagination and optional status/lead filters."""
        try:
            query = {"owner_id": ObjectId(owner_id)}
        except Exception:
            query = {"owner_id": owner_id}

        if status:
            query["status"] = status
        if lead_id:
            try:
                query["lead_id"] = ObjectId(lead_id)
            except Exception:
                query["lead_id"] = lead_id

        total_count = await AgentJob.find(query).count()
        jobs = await AgentJob.find(query).sort("-created_at").skip(skip).limit(limit).to_list()
        return jobs, total_count

    async def update_job(self, job: AgentJob, update_data: dict) -> AgentJob:
        """Update fields on an AgentJob record."""
        update_data["updated_at"] = datetime.now(timezone.utc)
        await job.update({"$set": update_data})
        return job

    async def create_event(self, event_data: dict) -> AgentEvent:
        """Create and persist an AgentEvent record."""
        event = AgentEvent(**event_data)
        await event.insert()
        return event

    async def list_events_for_job(self, job_id: str, owner_id: str) -> List[AgentEvent]:
        """Fetch all events for a job sorted by timestamp ascending."""
        try:
            o_id = ObjectId(owner_id)
        except Exception:
            o_id = owner_id

        return await AgentEvent.find({"job_id": job_id, "owner_id": o_id}).sort("timestamp").to_list()

    async def list_events_for_job_no_auth(self, job_id: str) -> List[AgentEvent]:
        """Fetch all events for a job without owner check (used by workers)."""
        return await AgentEvent.find({"job_id": job_id}).sort("timestamp").to_list()
