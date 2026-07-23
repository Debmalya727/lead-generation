"""
Research Module Service Layer.

High-level orchestration service for initiating analysis jobs, fetching research reports,
and retrieving granular sub-resource agent findings.
"""
import logging
from typing import Optional, List, Tuple

from app.database.mongodb.repositories.research_repository import ResearchRepository
from app.database.mongodb.repositories.lead_repository import LeadRepository
from app.database.mongodb.repositories.intelligence_repository import IntelligenceRepository
from app.database.mongodb.collections.research import ResearchReport
from app.tasks.research_tasks import run_research_pipeline

logger = logging.getLogger("backend.research.module")


class ResearchModule:
    """Service layer managing research job lifecycle and reporting."""

    def __init__(
        self,
        research_repo: ResearchRepository,
        lead_repo: LeadRepository,
        company_intel_repo: IntelligenceRepository,
    ):
        self.research_repo = research_repo
        self.lead_repo = lead_repo
        self.company_intel_repo = company_intel_repo

    async def initiate_research_analysis(
        self,
        lead_id: str,
        owner_id: str,
    ) -> ResearchReport:
        """Enqueue an asynchronous research analysis job via Celery."""
        logger.info(f"Initiating research analysis for lead_id '{lead_id}' (owner: {owner_id})")

        # 1. Verify lead exists & belongs to owner
        lead = await self.lead_repo.get_by_id(lead_id, owner_id)
        if not lead:
            raise ValueError("Lead not found or access denied")

        # 2. Fetch existing report or create pending document
        existing = await self.research_repo.get_by_lead_id(lead_id, owner_id)
        if existing:
            report = await self.research_repo.update(existing, {
                "status": "running",
                "progress": 5.0,
                "error_message": None,
            })
        else:
            report_data = {
                "lead_id": lead.id,
                "company_name": lead.name,
                "website_url": lead.website or "",
                "owner_id": lead.owner_id,
                "status": "running",
                "progress": 5.0,
            }
            report = await self.research_repo.create(report_data)

        # 3. Enqueue Celery background task
        run_research_pipeline.delay(str(report.id))

        return report

    async def get_report_by_lead(self, lead_id: str, owner_id: str) -> Optional[ResearchReport]:
        """Fetch complete research report for a target lead."""
        return await self.research_repo.get_by_lead_id(lead_id, owner_id)

    async def get_report_by_id(self, doc_id: str, owner_id: str) -> Optional[ResearchReport]:
        """Fetch research report by document ID."""
        return await self.research_repo.get_by_id(doc_id, owner_id)

    async def delete_report(self, lead_id: str, owner_id: str) -> bool:
        """Delete research report for a lead."""
        report = await self.research_repo.get_by_lead_id(lead_id, owner_id)
        if report:
            return await self.research_repo.delete(report)
        return False
