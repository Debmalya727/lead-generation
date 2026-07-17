import logging
from typing import List
from bson import ObjectId
from fastapi import HTTPException, status
from app.database.mongodb.collections.job import ScrapeJob
from app.database.mongodb.repositories.job_repository import JobRepository
from app.database.mongodb.repositories.lead_repository import LeadRepository
from app.schemas.discovery import DiscoveryStartRequest, DiscoveredLeadResponse, JobStatusResponse, SaveLeadsRequest
from app.tasks.discovery_tasks import run_discovery

logger = logging.getLogger("backend.modules.discovery")


class DiscoveryModule:
    def __init__(self, job_repository: JobRepository, lead_repository: LeadRepository):
        self.job_repo = job_repository
        self.lead_repo = lead_repository

    async def start_discovery(self, payload: DiscoveryStartRequest, owner_id: str) -> JobStatusResponse:
        """Create a discovery job and enqueue it in Celery background workers."""
        valid_providers = {"google_maps", "justdial", "indiamart", "tradeindia"}
        for p in payload.providers:
            if p.lower().strip() not in valid_providers:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid provider: {p}. Choose from google_maps, justdial, indiamart, tradeindia."
                )
                
        job_data = {
            "owner_id": ObjectId(owner_id),
            "keyword": payload.keyword.strip(),
            "location": payload.location.strip(),
            "providers": [p.lower().strip() for p in payload.providers],
            "status": "pending",
            "progress": 0.0,
            "total_results": 0,
            "results": []
        }
        
        job = await self.job_repo.create(job_data)
        logger.info(f"Created ScrapeJob {job.id} for owner {owner_id}. Enqueueing Celery background task...")
        
        # Enqueue background task
        run_discovery.delay(str(job.id))
        
        return JobStatusResponse.from_orm(job)

    async def get_job_status(self, job_id: str, owner_id: str) -> JobStatusResponse:
        """Fetch status progress of a specific discovery job."""
        job = await self.job_repo.get_by_id(job_id, owner_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Discovery job not found or access denied."
            )
        return JobStatusResponse.from_orm(job)

    async def get_job_results(self, job_id: str, owner_id: str) -> List[DiscoveredLeadResponse]:
        """Fetch list of business results extracted by a specific discovery job."""
        job = await self.job_repo.get_by_id(job_id, owner_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Discovery job not found or access denied."
            )
        return [DiscoveredLeadResponse(**res.dict()) for res in job.results]

    async def cancel_job(self, job_id: str, owner_id: str) -> dict:
        """Mark job status as cancelled so Celery tasks terminate dynamically."""
        job = await self.job_repo.get_by_id(job_id, owner_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Discovery job not found or access denied."
            )
            
        if job.status in ("completed", "failed", "cancelled"):
            return {"status": "success", "message": f"Job is already in {job.status} terminal state."}
            
        await self.job_repo.update(job, {"status": "cancelled", "progress": 100.0})
        logger.info(f"Cancelled discovery job: {job_id} under owner: {owner_id}")
        return {"status": "success", "message": "Discovery job cancellation command submitted."}

    async def save_selected_leads(self, job_id: str, payload: SaveLeadsRequest, owner_id: str) -> dict:
        """Persist selected discovered leads into active workspace businesses collection, ignoring duplicates."""
        job = await self.job_repo.get_by_id(job_id, owner_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Discovery job not found or access denied."
            )
            
        target_ids = set(payload.lead_ids)
        leads_to_save = [res for res in job.results if res.id in target_ids]
        
        if not leads_to_save:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No matching discovered leads found for the provided selection IDs."
            )
            
        saved_count = 0
        skipped_count = 0
        
        for d_lead in leads_to_save:
            # Query if duplicates exist in main businesses leads list
            existing, _ = await self.lead_repo.list_leads(
                owner_id=owner_id,
                search=d_lead.name,
                status=None
            )
            
            # Simple duplication check on name and location match
            is_duplicate = False
            for lead in existing:
                if lead.name.lower().strip() == d_lead.name.lower().strip():
                    if (lead.location or "").lower().strip() == (d_lead.location or "").lower().strip():
                        is_duplicate = True
                        break
                        
            if is_duplicate:
                skipped_count += 1
                continue
                
            # Create a Lead model in collection
            lead_payload = {
                "owner_id": ObjectId(owner_id),
                "name": d_lead.name,
                "website": d_lead.website,
                "phone": d_lead.phone,
                "email": d_lead.email,
                "location": d_lead.location,
                "score": d_lead.score,
                "status": "discovered",
                "job_id": ObjectId(job_id)
            }
            await self.lead_repo.create(lead_payload)
            saved_count += 1
            
        logger.info(f"Saved {saved_count} leads from job {job_id} to owner {owner_id} leads database. Skipped {skipped_count} duplicates.")
        return {
            "status": "success",
            "message": f"Successfully saved {saved_count} leads. Skipped {skipped_count} duplicate entries.",
            "saved_count": saved_count,
            "skipped_count": skipped_count
        }
