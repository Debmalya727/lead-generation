"""
Enterprise Discovery Module.
Orchestrates lead discovery jobs, provider health monitoring, deduplication merge logs,
CRM lead import, Knowledge Fabric integration, and analytics snapshots.
"""
import logging
from typing import List, Dict, Any, Optional
from bson import ObjectId
from fastapi import HTTPException, status
from app.database.mongodb.collections.job import ScrapeJob
from app.database.mongodb.collections.discovery import (
    DiscoveredCompanyDocument,
    DuplicateMergeLogDocument,
    DiscoveryProviderHealthDocument,
)
from app.database.mongodb.repositories.job_repository import JobRepository
from app.database.mongodb.repositories.lead_repository import LeadRepository
from app.schemas.discovery import DiscoveryStartRequest, JobStatusResponse, SaveLeadsRequest
from app.modules.discovery.providers.provider_registry import provider_registry
from app.modules.discovery.analytics.discovery_analytics import discovery_analytics
from app.tasks.discovery_tasks import run_discovery
from app.events.event_bus.bus import event_bus
from app.events.schemas.events import LeadCRMCreatedEvent

logger = logging.getLogger("backend.modules.discovery")


class DiscoveryModule:
    """Orchestration layer for Enterprise Lead Discovery Platform."""

    def __init__(self, job_repository: JobRepository, lead_repository: LeadRepository):
        self.job_repo = job_repository
        self.lead_repo = lead_repository

    async def start_discovery(self, payload: DiscoveryStartRequest, owner_id: str) -> JobStatusResponse:
        """Register a new lead discovery job and queue 9-stage Celery background pipeline."""
        valid_providers = {"google_maps", "justdial", "indiamart", "tradeindia"}
        requested_providers = [p.lower().strip() for p in payload.providers]

        for p in requested_providers:
            if p not in valid_providers:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid provider: {p}. Valid options: {', '.join(valid_providers)}",
                )

        job_data = {
            "owner_id": ObjectId(owner_id),
            "keyword": payload.keyword.strip(),
            "location": payload.location.strip(),
            "providers": requested_providers,
            "website_filter": payload.website_filter or "all",
            "limit": payload.limit or 20,
            "status": "pending",
            "progress": 0.0,
            "total_results": 0,
            "results": [],
        }

        job = await self.job_repo.create(job_data)
        logger.info(f"[DiscoveryModule] Created ScrapeJob {job.id} for owner {owner_id}. Enqueuing Celery background pipeline...")

        # Enqueue background pipeline task
        run_discovery.delay(str(job.id))

        return JobStatusResponse.from_orm(job)

    async def get_latest_job(self, owner_id: str) -> JobStatusResponse:
        """Fetch status progress of the most recent discovery job for user."""
        jobs = await self.job_repo.list_by_owner(owner_id)
        if not jobs:
            # Fallback to querying all jobs in DB
            jobs = await ScrapeJob.find_all().sort("-created_at").to_list()
        if not jobs:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No discovery jobs found.",
            )
        return JobStatusResponse.model_validate(jobs[0]) if hasattr(JobStatusResponse, "model_validate") else JobStatusResponse.from_orm(jobs[0])

    async def get_all_discovered_companies(self, owner_id: str) -> List[Dict[str, Any]]:
        """Retrieve all canonical discovered company documents across all jobs."""
        docs = await DiscoveredCompanyDocument.find_all().to_list()
        results = []
        for doc in docs:
            d = doc.model_dump() if hasattr(doc, "model_dump") else doc.dict()
            d["id"] = str(doc.id)
            results.append(d)
        return results

    async def get_job_status(self, job_id: str, owner_id: str) -> JobStatusResponse:
        """Fetch status progress of a specific discovery job."""
        job = await self.job_repo.get_by_id(job_id, owner_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Discovery job not found or access denied.",
            )
        return JobStatusResponse.from_orm(job)

    async def get_job_results(self, job_id: str, owner_id: str) -> List[Dict[str, Any]]:
        """Fetch canonical enriched lead documents discovered by a job."""
        job = await self.job_repo.get_by_id(job_id, owner_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Discovery job not found or access denied.",
            )

        # Query DiscoveredCompanyDocument collection
        docs = await DiscoveredCompanyDocument.find(
            DiscoveredCompanyDocument.job_id == job_id
        ).to_list()

        if docs:
            results = []
            for doc in docs:
                d = doc.dict()
                d["id"] = str(doc.id)
                results.append(d)
            return results

        # Fallback to ScrapeJob sub-document results
        return [res.dict() for res in job.results]

    async def get_job_duplicates(self, job_id: str, owner_id: str) -> List[Dict[str, Any]]:
        """Fetch deduplication merge logs for a specific job."""
        logs = await DuplicateMergeLogDocument.find(
            DuplicateMergeLogDocument.job_id == job_id
        ).to_list()
        return [l.dict() for l in logs]

    async def cancel_job(self, job_id: str, owner_id: str) -> dict:
        """Mark job status as cancelled so active tasks terminate dynamically."""
        job = await self.job_repo.get_by_id(job_id, owner_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Discovery job not found or access denied.",
            )

        if job.status in ("completed", "failed", "cancelled"):
            return {"status": "success", "message": f"Job is already in {job.status} terminal state."}

        await self.job_repo.update(job, {"status": "cancelled", "progress": 100.0})
        logger.info(f"[DiscoveryModule] Cancelled discovery job: {job_id} under owner: {owner_id}")
        return {"status": "success", "message": "Discovery job cancellation command submitted."}

    async def get_provider_health(self) -> Dict[str, Any]:
        """Fetch health metrics and circuit breaker status across all registered providers."""
        return provider_registry.get_health_summary()

    async def get_analytics_dashboard(self, owner_id: str) -> Dict[str, Any]:
        """Fetch unified discovery platform analytics dashboard."""
        return await discovery_analytics.get_dashboard_analytics(owner_id)

    async def save_selected_leads(self, job_id: str, payload: SaveLeadsRequest, owner_id: str) -> dict:
        """Save selected discovered leads into active CRM leads database, skipping duplicates."""
        job = await self.job_repo.get_by_id(job_id, owner_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Discovery job not found or access denied.",
            )

        target_ids = set(payload.lead_ids)
        discovered_docs = await DiscoveredCompanyDocument.find(
            DiscoveredCompanyDocument.job_id == job_id
        ).to_list()

        saved_count = 0
        skipped_count = 0

        for idx, doc in enumerate(discovered_docs):
            doc_legacy_id = f"{job_id}_{idx}"
            if str(doc.id) not in target_ids and doc.fingerprint not in target_ids and doc_legacy_id not in target_ids:
                continue

            existing, _ = await self.lead_repo.list_leads(
                owner_id=owner_id,
                search=doc.company_name,
                status=None,
            )

            is_duplicate = False
            for lead in existing:
                if lead.name.lower().strip() == doc.company_name.lower().strip():
                    is_duplicate = True
                    break

            if is_duplicate:
                skipped_count += 1
                continue

            # Create CRM Lead record
            lead_payload = {
                "owner_id": ObjectId(owner_id),
                "name": doc.company_name,
                "website": doc.website,
                "phone": doc.phones[0] if doc.phones else None,
                "email": doc.emails[0] if doc.emails else None,
                "location": f"{doc.city or job.location}, {doc.country}",
                "score": doc.quality_score or 75,
                "status": "discovered",
                "job_id": ObjectId(job_id),
            }
            crm_lead = await self.lead_repo.create(lead_payload)

            doc.crm_id = str(crm_lead.id)
            doc.crm_created = True
            await doc.save()

            await event_bus.publish(LeadCRMCreatedEvent(
                source="DiscoveryModule",
                payload={"crm_lead_id": str(crm_lead.id), "company_name": doc.company_name, "owner_id": owner_id}
            ))

            saved_count += 1

        logger.info(f"[DiscoveryModule] Saved {saved_count} leads to CRM for job {job_id}. Skipped {skipped_count} duplicates.")
        return {
            "status": "success",
            "message": f"Successfully imported {saved_count} leads to CRM. Skipped {skipped_count} duplicate records.",
            "saved_count": saved_count,
            "skipped_count": skipped_count,
        }
