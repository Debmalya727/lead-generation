"""
Scoring Module — Service layer orchestrating the Lead Scoring Engine.

Validates lead ownership, creates/resets the LeadScore document,
and dispatches the Celery background task.
"""
import logging
from bson import ObjectId
from fastapi import HTTPException, status

from app.database.mongodb.repositories.scoring_repository import ScoringRepository
from app.database.mongodb.repositories.lead_repository import LeadRepository
from app.database.mongodb.repositories.intelligence_repository import IntelligenceRepository
from app.schemas.scoring import (
    ScoringAnalyzeRequest,
    ScoringResponse,
    ScoringStatusResponse,
)

logger = logging.getLogger("backend.modules.scoring")


class ScoringModule:
    def __init__(
        self,
        scoring_repo: ScoringRepository,
        lead_repo: LeadRepository,
        intel_repo: IntelligenceRepository,
    ):
        self.scoring_repo = scoring_repo
        self.lead_repo = lead_repo
        self.intel_repo = intel_repo

    async def start_scoring(
        self, payload: ScoringAnalyzeRequest, owner_id: str
    ) -> ScoringStatusResponse:
        """Validate lead, create or reset score document, enqueue Celery task."""
        # Verify lead exists and belongs to this owner
        lead = await self.lead_repo.get_by_id(payload.lead_id, owner_id)
        if not lead:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lead not found or access denied.",
            )

        # Check if a score document already exists — reset for re-scoring if so
        existing = await self.scoring_repo.get_by_lead_id(payload.lead_id, owner_id)
        if existing:
            await self.scoring_repo.update(existing, {
                "status": "pending",
                "progress": 0.0,
                "error_message": None,
                "score": None,
                "priority": None,
                "rule_score": None,
                "llm_score_adjustment": 0,
                "score_breakdown": [],
                "strengths": [],
                "weaknesses": [],
                "risk_factors": [],
                "recommended_outreach": None,
                "score_explanation": None,
                "confidence_score": None,
                "scored_at": None,
                "website_url": getattr(lead, "website", None),
            })
            doc = existing
        else:
            doc_data = {
                "lead_id": ObjectId(payload.lead_id),
                "owner_id": ObjectId(owner_id),
                "company_name": lead.name,
                "website_url": getattr(lead, "website", None),
                "status": "pending",
                "progress": 0.0,
            }
            doc = await self.scoring_repo.create(doc_data)

        logger.info(
            f"Enqueueing lead scoring for '{lead.name}' "
            f"(doc_id={doc.id}, owner={owner_id})"
        )

        # Import here to avoid circular imports at module load time
        from app.tasks.scoring_tasks import run_lead_scoring
        run_lead_scoring.delay(str(doc.id))

        return ScoringStatusResponse.from_orm(doc)

    async def get_by_lead(self, lead_id: str, owner_id: str) -> ScoringResponse:
        """Fetch the full scoring report for a lead."""
        doc = await self.scoring_repo.get_by_lead_id(lead_id, owner_id)
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No scoring report found for this lead. Start scoring first.",
            )
        return ScoringResponse.from_orm(doc)

    async def get_job_status(self, job_id: str, owner_id: str) -> ScoringStatusResponse:
        """Fetch scoring job status by internal document ID (for polling)."""
        doc = await self.scoring_repo.get_by_id(job_id, owner_id)
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Scoring job not found or access denied.",
            )
        return ScoringStatusResponse.from_orm(doc)

    async def delete_score(self, lead_id: str, owner_id: str) -> dict:
        """Delete the scoring report for a lead."""
        doc = await self.scoring_repo.get_by_lead_id(lead_id, owner_id)
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Scoring report not found for this lead.",
            )
        await self.scoring_repo.delete(doc)
        logger.info(f"Deleted scoring report for lead {lead_id} (owner: {owner_id})")
        return {"status": "success", "message": "Scoring report deleted successfully."}
