"""
Celery Background Worker Tasks for Phase 10: Vector Search & Knowledge Base Indexing.
"""
import asyncio
import logging
from celery import shared_task

logger = logging.getLogger("backend.tasks.vector")


async def _async_index_lead_knowledge(lead_id_str: str, owner_id_str: str):
    """Internal async task for indexing lead knowledge modules."""
    from app.database.mongodb.connection import DatabaseManager
    from app.database.mongodb.repositories.lead_repository import LeadRepository
    from app.database.mongodb.repositories.intelligence_repository import IntelligenceRepository
    from app.database.mongodb.repositories.scoring_repository import ScoringRepository
    from app.database.mongodb.repositories.sales_intelligence_repository import SalesIntelligenceRepository
    from app.database.mongodb.repositories.research_repository import ResearchRepository
    from app.database.mongodb.repositories.outreach_repository import CampaignRepository, EmailTemplateRepository
    from app.vector.services.vector_service import VectorService

    # Ensure Beanie MongoDB connection is initialized for worker thread
    DatabaseManager.client = None
    await DatabaseManager.initialize()

    lead_repo = LeadRepository()
    intel_repo = IntelligenceRepository()
    scoring_repo = ScoringRepository()
    sales_intel_repo = SalesIntelligenceRepository()
    research_repo = ResearchRepository()
    campaign_repo = CampaignRepository()
    template_repo = EmailTemplateRepository()

    service = VectorService(
        lead_repo=lead_repo,
        intel_repo=intel_repo,
        scoring_repo=scoring_repo,
        sales_intel_repo=sales_intel_repo,
        research_repo=research_repo,
        campaign_repo=campaign_repo,
        template_repo=template_repo,
    )

    try:
        res = await service.index_lead_knowledge(lead_id=lead_id_str, owner_id=owner_id_str)
        logger.info(f"Successfully indexed knowledge for lead '{lead_id_str}': {res['total_indexed_chunks']} chunks created.")
    except Exception as e:
        logger.exception(f"Error indexing lead knowledge for lead '{lead_id_str}': {str(e)}")


@shared_task(name="app.tasks.vector_tasks.index_lead_knowledge_task", bind=True, max_retries=2)
def index_lead_knowledge_task(self, lead_id_str: str, owner_id_str: str):
    """Celery task entrypoint for background lead knowledge vector indexing."""
    logger.info(f"Celery worker received index_lead_knowledge_task for lead '{lead_id_str}'")
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop.run_until_complete(_async_index_lead_knowledge(lead_id_str, owner_id_str))


async def _async_reindex_workspace(owner_id_str: str):
    """Internal async task reindexing all workspace leads for an owner."""
    from app.database.mongodb.connection import DatabaseManager
    from app.database.mongodb.repositories.lead_repository import LeadRepository

    if DatabaseManager.client is None:
        await DatabaseManager.initialize()

    lead_repo = LeadRepository()
    leads, _ = await lead_repo.list_leads(owner_id=owner_id_str, limit=500)

    for lead in leads:
        await _async_index_lead_knowledge(str(lead.id), owner_id_str)


@shared_task(name="app.tasks.vector_tasks.reindex_knowledge_base_task", bind=True)
def reindex_knowledge_base_task(self, owner_id_str: str):
    """Celery task entrypoint for reindexing all workspace leads."""
    logger.info(f"Celery worker received reindex_knowledge_base_task for owner '{owner_id_str}'")
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop.run_until_complete(_async_reindex_workspace(owner_id_str))
