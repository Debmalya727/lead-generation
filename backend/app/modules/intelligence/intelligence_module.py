import logging
from bson import ObjectId
from fastapi import HTTPException, status
from app.database.mongodb.collections.lead import Lead
from app.database.mongodb.repositories.intelligence_repository import IntelligenceRepository
from app.database.mongodb.repositories.lead_repository import LeadRepository
from app.schemas.intelligence import (
    IntelligenceAnalyzeRequest,
    IntelligenceResponse,
    IntelligenceStatusResponse,
)
from app.tasks.intelligence_tasks import run_intelligence_analysis

logger = logging.getLogger("backend.modules.intelligence")


class IntelligenceModule:
    def __init__(
        self,
        intel_repo: IntelligenceRepository,
        lead_repo: LeadRepository,
    ):
        self.intel_repo = intel_repo
        self.lead_repo = lead_repo

    async def start_analysis(
        self, payload: IntelligenceAnalyzeRequest, owner_id: str
    ) -> IntelligenceStatusResponse:
        """Validate lead, create or reset intelligence document, enqueue Celery task."""
        # Verify lead exists and belongs to this owner
        lead = await self.lead_repo.get_by_id(payload.lead_id, owner_id)
        if not lead:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lead not found or access denied.",
            )

        if not lead.website:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Lead has no website URL. Add a website to the lead before running intelligence analysis.",
            )

        # Check if a document already exists — if so, reset it for re-analysis
        existing = await self.intel_repo.get_by_lead_id(payload.lead_id, owner_id)
        if existing:
            # Reset the existing document for re-analysis
            await self.intel_repo.update(existing, {
                "status": "pending",
                "progress": 0.0,
                "error_message": None,
                "intelligence": None,
                "tech_stack": [],
                "social_links": {},
                "contact_page": None,
                "careers_page": None,
                "about_page": None,
                "analyzed_at": None,
                "website_url": lead.website,
            })
            doc = existing
        else:
            # Create new intelligence document
            doc_data = {
                "lead_id": ObjectId(payload.lead_id),
                "owner_id": ObjectId(owner_id),
                "website_url": lead.website,
                "company_name": lead.name,
                "status": "pending",
                "progress": 0.0,
            }
            doc = await self.intel_repo.create(doc_data)

        logger.info(
            f"Enqueueing intelligence analysis for lead '{lead.name}' "
            f"(doc_id={doc.id}, owner={owner_id})"
        )

        # Enqueue Celery background task
        run_intelligence_analysis.delay(str(doc.id))

        return IntelligenceStatusResponse.from_orm(doc)

    async def get_by_lead(self, lead_id: str, owner_id: str) -> IntelligenceResponse:
        """Fetch the full intelligence report for a lead."""
        doc = await self.intel_repo.get_by_lead_id(lead_id, owner_id)
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No intelligence report found for this lead. Start an analysis first.",
            )
        return IntelligenceResponse.from_orm(doc)

    async def get_job_status(self, job_id: str, owner_id: str) -> IntelligenceStatusResponse:
        """Fetch analysis job status by internal document ID (for polling)."""
        doc = await self.intel_repo.get_by_id(job_id, owner_id)
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Intelligence analysis job not found or access denied.",
            )
        return IntelligenceStatusResponse.from_orm(doc)

    async def delete_intelligence(self, lead_id: str, owner_id: str) -> dict:
        """Delete the intelligence report for a lead."""
        doc = await self.intel_repo.get_by_lead_id(lead_id, owner_id)
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Intelligence report not found for this lead.",
            )
        await self.intel_repo.delete(doc)
        logger.info(f"Deleted intelligence report for lead {lead_id} (owner: {owner_id})")
        return {"status": "success", "message": "Intelligence report deleted successfully."}
