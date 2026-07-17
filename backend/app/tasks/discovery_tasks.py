import asyncio
import logging
import uuid
from typing import List
from app.database.mongodb.connection import DatabaseManager
from app.database.mongodb.repositories.job_repository import JobRepository
from app.modules.discovery.providers.google_maps import GoogleMapsProvider
from app.modules.discovery.providers.indiamart import IndiaMARTProvider
from app.modules.discovery.providers.justdial import JustDialProvider
from app.modules.discovery.providers.tradeindia import TradeIndiaProvider
from app.tasks.worker import celery_app

logger = logging.getLogger("backend.tasks.discovery")


def get_provider_instance(name: str):
    """Instantiate the matching provider by key name."""
    mapping = {
        "google_maps": GoogleMapsProvider,
        "justdial": JustDialProvider,
        "indiamart": IndiaMARTProvider,
        "tradeindia": TradeIndiaProvider,
    }
    provider_class = mapping.get(name.lower().strip())
    if provider_class:
        return provider_class()
    return None


async def async_run_discovery(job_id: str):
    """Async wrapper executed by Celery processing lead discovery requests."""
    # 1. Initialize MongoDB connection pool inside the background task worker context
    await DatabaseManager.initialize()
    
    job_repo = JobRepository()
    
    # 2. Fetch the job details
    job = await ScrapeJob.get(job_id)
    if not job:
        logger.error(f"Discovery Task failed: Job {job_id} not found in database.")
        return
        
    if job.status == "cancelled":
        logger.info(f"Discovery Task aborted: Job {job_id} was cancelled before starting.")
        return

    # Update state to running
    job = await job_repo.update(job, {"status": "running", "progress": 10.0})
    logger.info(f"Starting Lead Discovery Engine job ID: {job_id} ({job.keyword} in {job.location})")

    # 3. Instantiate selected providers
    provider_instances = []
    for p_name in job.providers:
        prov = get_provider_instance(p_name)
        if prov:
            provider_instances.append(prov)
        else:
            logger.warning(f"Discovery Task: Unknown provider name requested: {p_name}")

    if not provider_instances:
        await job_repo.update(job, {
            "status": "failed",
            "progress": 100.0,
            "error_message": "No valid discovery providers were selected."
        })
        return

    # 4. Execute provider tasks concurrently, allowing them to fail independently
    tasks = []
    for prov in provider_instances:
        tasks.append(run_single_provider(prov, job.keyword, job.location))

    results_by_provider = await asyncio.gather(*tasks, return_exceptions=True)

    # Re-check cancellation before persisting results
    job = await ScrapeJob.get(job_id)
    if job.status == "cancelled":
        logger.info(f"Discovery Task stopped: Job {job_id} was cancelled during extraction.")
        return

    # 5. Process and deduplicate leads
    raw_leads = []
    for idx, prov_res in enumerate(results_by_provider):
        prov_name = provider_instances[idx].provider_name
        if isinstance(prov_res, Exception) or not isinstance(prov_res, list):
            logger.error(f"Provider {prov_name} encountered an error or returned invalid type: {str(prov_res)}")
            continue
        
        raw_leads.extend(prov_res)
        # Update progress based on completed provider chunks
        current_progress = 10.0 + ((idx + 1) / len(provider_instances)) * 80.0
        job = await job_repo.update(job, {"progress": round(current_progress, 1)})

    # Deduplicate results using compound key (name + website/phone)
    deduplicated = {}
    for lead in raw_leads:
        name_key = lead["name"].lower().strip()
        website_key = lead["website"].lower().strip() if lead.get("website") else ""
        phone_key = lead["phone"].strip() if lead.get("phone") else ""
        
        # Deduplication match key
        match_key = f"{name_key}_{website_key or phone_key}"
        
        if match_key in deduplicated:
            # Merge: keep the higher quality score
            existing = deduplicated[match_key]
            if lead["score"] > existing["score"]:
                existing["score"] = lead["score"]
            # append other missing details
            if not existing["email"] and lead["email"]:
                existing["email"] = lead["email"]
            if not existing["phone"] and lead["phone"]:
                existing["phone"] = lead["phone"]
        else:
            deduplicated[match_key] = lead

    # Format leads as sub-documents
    final_discovered_leads = []
    for idx, lead_data in enumerate(deduplicated.values()):
        lead_data["id"] = f"{job_id}_{idx}_{uuid.uuid4().hex[:6]}"
        final_discovered_leads.append(lead_data)

    # 6. Save results and complete
    await job_repo.update(job, {
        "status": "completed",
        "progress": 100.0,
        "total_results": len(final_discovered_leads),
        "results": final_discovered_leads
    })
    
    logger.info(f"Completed Lead Discovery Engine job ID: {job_id}. Discovered {len(final_discovered_leads)} leads.")
    await DatabaseManager.close()


async def run_single_provider(provider, keyword: str, location: str) -> List[dict]:
    """Wraps provider run in a try-catch block to satisfy independent failure rules."""
    try:
        logger.info(f"Running provider discovery: {provider.provider_name}")
        return await provider.discover(keyword, location, limit=15)
    except Exception as e:
        logger.error(f"Error in provider {provider.provider_name}: {str(e)}")
        # Return empty list on failure so other providers proceed
        return []


# Import ScrapeJob inside the task module to prevent circular dependency imports
from app.database.mongodb.collections.job import ScrapeJob


@celery_app.task(name="run_discovery")
def run_discovery(job_id: str):
    """Celery task entrypoint setting up event loops for async execution."""
    asyncio.run(async_run_discovery(job_id))
