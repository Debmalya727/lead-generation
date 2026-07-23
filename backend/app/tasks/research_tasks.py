"""
Celery Background Worker Tasks for Phase 9: AI Research Agents.
"""
import asyncio
import logging
from datetime import datetime, timezone
from celery import shared_task

logger = logging.getLogger("backend.tasks.research")


async def _async_run_research_pipeline(doc_id_str: str):
    """Internal async task pipeline executing multi-agent research."""
    from app.database.mongodb.connection import DatabaseManager
    from app.database.mongodb.repositories.research_repository import ResearchRepository
    from app.database.mongodb.repositories.lead_repository import LeadRepository
    from app.database.mongodb.repositories.intelligence_repository import IntelligenceRepository
    from app.modules.research.research_orchestrator import ResearchOrchestrator

    # Ensure Beanie MongoDB connection is initialized for worker thread
    if DatabaseManager.client is None:
        await DatabaseManager.initialize()

    research_repo = ResearchRepository()
    lead_repo = LeadRepository()
    company_intel_repo = IntelligenceRepository()
    orchestrator = ResearchOrchestrator()

    report = await research_repo.get_by_id_no_auth(doc_id_str)
    if not report:
        logger.error(f"ResearchReport '{doc_id_str}' not found in MongoDB.")
        return

    lead_id_str = str(report.lead_id)
    owner_id_str = str(report.owner_id)

    try:
        # Update progress to 10%
        await research_repo.update(report, {"status": "running", "progress": 10.0})

        # Fetch lead & existing company intelligence context if available
        lead = await lead_repo.get_by_id(lead_id_str, owner_id_str)
        company_intel = await company_intel_repo.get_by_lead_id(lead_id_str, owner_id_str)

        company_name = report.company_name or (lead.name if lead else "Target Account")
        website_url = report.website_url or (lead.website if lead else "")

        raw_text = company_intel.website_url if company_intel else ""
        tech_stack = company_intel.tech_stack if company_intel else []
        social_links = company_intel.social_links if company_intel else {}
        industry = (company_intel.intelligence.industry if (company_intel and company_intel.intelligence) else "B2B SaaS / Services")

        # Async progress callback helper
        async def progress_cb(prog: float, msg: str):
            logger.info(f"Research Job [{doc_id_str}] {prog:.0f}%: {msg}")
            await research_repo.update(report, {"progress": prog})

        # Run master orchestrator
        results = await orchestrator.execute_pipeline(
            company_name=company_name,
            website_url=website_url or "",
            raw_text_content=raw_text,
            tech_stack=tech_stack,
            social_links=social_links,
            industry=industry or "B2B SaaS / Services",
            progress_callback=progress_cb,
        )

        # Update report with final findings
        update_payload = {
            "status": "completed",
            "progress": 100.0,
            "overall_confidence": results["overall_confidence"],
            "website_findings": results["website_findings"],
            "news_findings": results["news_findings"],
            "hiring_findings": results["hiring_findings"],
            "tech_findings": results["tech_findings"],
            "competitor_findings": results["competitor_findings"],
            "social_findings": results["social_findings"],
            "knowledge_graph": results["knowledge_graph"],
            "verified_facts": results["verified_facts"],
            "ai_summary": results["ai_summary"],
            "analyzed_at": datetime.now(timezone.utc),
            "error_message": None,
        }

        await research_repo.update(report, update_payload)
        logger.info(f"Successfully completed Research Pipeline for doc_id '{doc_id_str}'")

    except Exception as e:
        logger.exception(f"Error executing research pipeline task for doc_id '{doc_id_str}': {str(e)}")
        await research_repo.update(report, {
            "status": "failed",
            "progress": 100.0,
            "error_message": str(e),
        })


@shared_task(name="app.tasks.research_tasks.run_research_pipeline", bind=True, max_retries=2)
def run_research_pipeline(self, doc_id_str: str):
    """Celery task entrypoint executing multi-agent research pipeline."""
    logger.info(f"Celery worker received run_research_pipeline task for doc_id '{doc_id_str}'")
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop.run_until_complete(_async_run_research_pipeline(doc_id_str))
