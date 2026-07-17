"""
Celery background tasks for Phase 7 AI Outreach & Sales Automation.

Tasks:
- process_campaign_sends: Runs scheduled sends for active campaigns
- generate_ai_email_batch: Generates copy for campaign steps asynchronously
- record_tracking_event: Background logging of opens/clicks/replies
"""
import asyncio
import logging
from app.database.mongodb.connection import DatabaseManager
from app.database.mongodb.repositories.outreach_repository import (
    CampaignRepository,
    CampaignStepRepository,
    CampaignRecipientRepository,
    EmailAccountRepository,
    EmailEventRepository,
    EmailAnalyticsRepository,
)
from app.database.mongodb.repositories.lead_repository import LeadRepository
from app.database.mongodb.repositories.intelligence_repository import IntelligenceRepository
from app.database.mongodb.repositories.scoring_repository import ScoringRepository
from app.modules.outreach.outreach_module import SendingModule
from app.tasks.worker import celery_app

logger = logging.getLogger("backend.tasks.outreach")


async def async_process_campaign_sends(campaign_id: str) -> int:
    """Async wrapper for processing queued campaign email sends."""
    await DatabaseManager.initialize()
    try:
        sending_module = SendingModule(
            campaign_repo=CampaignRepository(),
            step_repo=CampaignStepRepository(),
            recip_repo=CampaignRecipientRepository(),
            account_repo=EmailAccountRepository(),
            lead_repo=LeadRepository(),
            intel_repo=IntelligenceRepository(),
            score_repo=ScoringRepository(),
            event_repo=EmailEventRepository(),
            analytics_repo=EmailAnalyticsRepository(),
        )
        sent_count = await sending_module.send_next_batch(campaign_id=campaign_id, batch_size=25)
        logger.info(f"Background task sent {sent_count} emails for campaign {campaign_id}")
        return sent_count
    finally:
        await DatabaseManager.close()


@celery_app.task(name="process_campaign_sends")
def process_campaign_sends(campaign_id: str) -> int:
    """Celery entrypoint for campaign email batch processing."""
    return asyncio.run(async_process_campaign_sends(campaign_id))


async def async_process_all_active_campaigns() -> None:
    """Async sweep over all active campaigns to queue batch sends."""
    await DatabaseManager.initialize()
    try:
        camp_repo = CampaignRepository()
        active_camps = await camp_repo.list_active_campaigns()
        logger.info(f"Periodic sweep found {len(active_camps)} active campaigns")
        for camp in active_camps:
            process_campaign_sends.delay(str(camp.id))
    finally:
        await DatabaseManager.close()


@celery_app.task(name="process_all_active_campaigns")
def process_all_active_campaigns() -> None:
    """Celery periodic task triggering active campaign sends."""
    asyncio.run(async_process_all_active_campaigns())
