"""
Sales Intelligence Orchestration Module.

Coordinates job creation, verification, background worker task dispatch, and query access.
"""
import logging
from bson import ObjectId
from fastapi import HTTPException, status
from typing import Optional

from app.database.mongodb.repositories.lead_repository import LeadRepository
from app.database.mongodb.repositories.sales_intelligence_repository import SalesIntelligenceRepository
from app.schemas.sales_intelligence import (
    SalesIntelligenceAnalyzeRequest,
    SalesIntelligenceResponse,
    SalesIntelligenceStatusResponse,
)
from app.tasks.sales_intelligence_tasks import run_sales_intelligence_analysis

logger = logging.getLogger("backend.modules.sales_intelligence")


class SalesIntelligenceModule:
    """Service layer for Phase 8: Advanced Sales Intelligence."""

    def __init__(
        self,
        sales_intel_repo: SalesIntelligenceRepository,
        lead_repo: LeadRepository,
    ):
        self.sales_intel_repo = sales_intel_repo
        self.lead_repo = lead_repo

    async def start_analysis(
        self, payload: SalesIntelligenceAnalyzeRequest, owner_id: str
    ) -> SalesIntelligenceStatusResponse:
        """Validate lead, create/reset sales intelligence document, and enqueue Celery task."""
        lead = await self.lead_repo.get_by_id(payload.lead_id, owner_id)
        if not lead:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lead not found or access denied.",
            )

        # Check existing sales intelligence report
        existing = await self.sales_intel_repo.get_by_lead_id(payload.lead_id, owner_id)
        if existing:
            await self.sales_intel_repo.update(existing, {
                "status": "pending",
                "progress": 0.0,
                "error_message": None,
                "intent_score": 50,
                "intent_level": "Medium",
                "intent_reason": None,
                "decision_makers": [],
                "growth_signals": [],
                "timeline": None,
                "classification": None,
                "graph": None,
                "recommendations": None,
                "analyzed_at": None,
            })
            doc = existing
        else:
            doc_data = {
                "lead_id": ObjectId(payload.lead_id),
                "company_id": str(lead.id),
                "company_name": lead.name,
                "website_url": lead.website,
                "owner_id": ObjectId(owner_id),
                "status": "pending",
                "progress": 0.0,
                "intent_score": 50,
                "intent_level": "Medium",
            }
            doc = await self.sales_intel_repo.create(doc_data)

        logger.info(f"Enqueueing sales intelligence analysis for lead '{lead.name}' (doc_id={doc.id})")
        run_sales_intelligence_analysis.delay(str(doc.id))

        return SalesIntelligenceStatusResponse.from_orm_doc(doc)

    async def get_by_lead(self, lead_id: str, owner_id: str) -> SalesIntelligenceResponse:
        """Fetch full sales intelligence report by lead_id."""
        doc = await self.sales_intel_repo.get_by_lead_id(lead_id, owner_id)
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No sales intelligence report found for this lead. Trigger analysis first.",
            )
        return SalesIntelligenceResponse.from_orm_doc(doc)

    async def get_job_status(self, job_id: str, owner_id: str) -> SalesIntelligenceStatusResponse:
        """Fetch job status for polling."""
        doc = await self.sales_intel_repo.get_by_id(job_id, owner_id)
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sales intelligence job not found or access denied.",
            )
        return SalesIntelligenceStatusResponse.from_orm_doc(doc)

    async def delete_report(self, lead_id: str, owner_id: str) -> dict:
        """Delete sales intelligence report for a lead."""
        doc = await self.sales_intel_repo.get_by_lead_id(lead_id, owner_id)
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sales intelligence report not found for this lead.",
            )
        await self.sales_intel_repo.delete(doc)
        return {"status": "success", "message": "Sales intelligence report deleted successfully."}
