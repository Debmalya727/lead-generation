from typing import Optional
from bson import ObjectId
from app.database.mongodb.collections.job import ScrapeJob


class JobRepository:
    async def list_by_owner(self, owner_id: str, limit: int = 20) -> list[ScrapeJob]:
        """Fetch list of ScrapeJobs owned by user sorted by created_at descending."""
        try:
            return await ScrapeJob.find(ScrapeJob.owner_id == ObjectId(owner_id)).sort("-created_at").limit(limit).to_list()
        except Exception:
            return await ScrapeJob.find_all().sort("-created_at").limit(limit).to_list()

    async def get_by_id(self, job_id: str, owner_id: str) -> Optional[ScrapeJob]:
        """Fetch ScrapeJob document by ID, checking owner constraint."""
        try:
            job = await ScrapeJob.get(ObjectId(job_id))
        except Exception:
            job = await ScrapeJob.get(job_id)
            
        if job and str(job.owner_id) == owner_id:
            return job
        return None

    async def create(self, job_data: dict) -> ScrapeJob:
        """Create and persist a new ScrapeJob document."""
        job = ScrapeJob(**job_data)
        await job.insert()
        return job

    async def update(self, job: ScrapeJob, update_data: dict) -> ScrapeJob:
        """Update fields on a ScrapeJob document."""
        for field, value in update_data.items():
            if hasattr(job, field):
                setattr(job, field, value)
        await job.update_timestamp()
        return job

    async def delete(self, job: ScrapeJob) -> bool:
        """Delete ScrapeJob document."""
        await job.delete()
        return True
