"""
Enterprise Lead Discovery Asynchronous Task Pipeline.
9-Stage Background Pipeline:
1. Job Initialization
2. Provider Execution (Google Maps, Justdial, IndiaMART, TradeIndia)
3. Lead Normalization
4. AI Deduplication Engine
5. AI Lead Enrichment
6. Quality Scoring
7. Persistence & Deduplication Merge Log Recording
8. CRM & Knowledge Fabric Integration
9. Event Bus Dispatch & Analytics Recording
"""
import asyncio
import logging
import time
from typing import List, Dict, Any
from app.database.mongodb.connection import DatabaseManager
from app.database.mongodb.repositories.job_repository import JobRepository
from app.database.mongodb.collections.job import ScrapeJob
from app.database.mongodb.collections.discovery import DiscoveredCompanyDocument, DuplicateMergeLogDocument
from app.modules.discovery.providers.provider_registry import provider_registry
from app.modules.discovery.normalization.models import NormalizedLead
from app.modules.discovery.normalization.lead_normalizer import lead_normalizer
from app.modules.discovery.deduplication.deduplication_engine import deduplication_engine
from app.modules.discovery.enrichment.enrichment_engine import enrichment_engine
from app.modules.discovery.scoring.quality_scorer import lead_quality_scorer
from app.modules.discovery.analytics.discovery_analytics import discovery_analytics
from app.events.event_bus.bus import event_bus
from app.events.schemas.events import (
    LeadDiscoveredEvent,
    LeadNormalizedEvent,
    LeadDuplicateDetectedEvent,
    LeadEnrichedEvent,
    LeadScoreUpdatedEvent,
    LeadCRMCreatedEvent,
)
from app.knowledge.gateway.gateway_service import enterprise_knowledge_gateway
from app.tasks.worker import celery_app

logger = logging.getLogger("backend.tasks.discovery")


async def async_run_discovery(job_id: str):
    """Execute full 9-stage asynchronous lead discovery pipeline."""
    start_time = time.time()
    await DatabaseManager.initialize()
    job_repo = JobRepository()

    # 1. Fetch Discovery Job
    job = await ScrapeJob.get(job_id)
    if not job:
        logger.error(f"[DiscoveryTask] Job {job_id} not found in database.")
        return

    if job.status == "cancelled":
        logger.info(f"[DiscoveryTask] Job {job_id} was cancelled before starting.")
        return

    job = await job_repo.update(job, {"status": "running", "progress": 5.0})
    logger.info(f"[DiscoveryTask] STAGE 1: Started Discovery Pipeline job {job_id} ({job.keyword} in {job.location})")

    # 2. Provider Execution (STAGE 2)
    provider_instances = []
    for p_name in job.providers:
        prov = provider_registry.get_provider(p_name)
        if prov:
            provider_instances.append(prov)
        else:
            logger.warning(f"[DiscoveryTask] Unknown or unregistered provider: '{p_name}'")

    if not provider_instances:
        await job_repo.update(job, {"status": "failed", "progress": 100.0, "error_message": "No valid providers selected."})
        return

    job_limit = getattr(job, "limit", 20) or 20
    job_filter = getattr(job, "website_filter", "all") or "all"

    provider_tasks = [
        prov.discover(job.keyword, job.location, limit=job_limit, website_filter=job_filter)
        for prov in provider_instances
    ]
    raw_results_by_provider = await asyncio.gather(*provider_tasks, return_exceptions=True)

    job = await job_repo.update(job, {"progress": 30.0})
    logger.info(f"[DiscoveryTask] STAGE 2: Completed Provider Search Across {len(provider_instances)} Providers")

    # 3. Lead Normalization (STAGE 3)
    raw_normalized_leads: List[NormalizedLead] = []
    for idx, res in enumerate(raw_results_by_provider):
        prov_name = provider_instances[idx].provider_name
        if isinstance(res, Exception) or not isinstance(res, list):
            logger.error(f"[DiscoveryTask] Provider {prov_name} error: {res}")
            continue

        for item in res:
            if isinstance(item, NormalizedLead):
                raw_normalized_leads.append(item)
            elif isinstance(item, dict):
                norm_lead = lead_normalizer.normalize_raw_lead(item, prov_name)
                raw_normalized_leads.append(norm_lead)

    await event_bus.publish(LeadNormalizedEvent(
        source="DiscoveryPipeline",
        payload={"job_id": job_id, "normalized_count": len(raw_normalized_leads)}
    ))

    job = await job_repo.update(job, {"progress": 45.0})
    logger.info(f"[DiscoveryTask] STAGE 3: Normalized {len(raw_normalized_leads)} Raw Lead Records")

    # 4. AI Deduplication Engine (STAGE 4)
    dedup_result = deduplication_engine.deduplicate(raw_normalized_leads)
    canonical_leads = dedup_result.canonical_leads

    # Persist Deduplication Merge Logs
    for log_dict in dedup_result.merge_logs:
        merge_log = DuplicateMergeLogDocument(
            job_id=job_id,
            owner_id=str(job.owner_id),
            canonical_fingerprint=log_dict["canonical_fingerprint"],
            merged_fingerprints=log_dict["merged_fingerprints"],
            merged_company_names=log_dict["merged_company_names"],
            merged_providers=log_dict["merged_providers"],
            match_reasons=log_dict["match_reasons"],
            confidence=log_dict["confidence"],
        )
        try:
            await merge_log.insert()
        except Exception:
            pass

    if dedup_result.merge_logs:
        await event_bus.publish(LeadDuplicateDetectedEvent(
            source="DeduplicationEngine",
            payload={"job_id": job_id, "merged_count": dedup_result.merged_count}
        ))

    job = await job_repo.update(job, {"progress": 60.0})
    logger.info(f"[DiscoveryTask] STAGE 4: AI Deduplication Unified {len(raw_normalized_leads)} -> {len(canonical_leads)} Canonical Leads")

    # 5. AI Enrichment & 6. Quality Scoring (STAGE 5 & 6)
    enriched_company_docs: List[DiscoveredCompanyDocument] = []
    final_legacy_results = []
    hot_count, warm_count, cold_count = 0, 0, 0

    for idx, c_lead in enumerate(canonical_leads):
        # STAGE 5: Enrich lead
        enriched_dict = await enrichment_engine.enrich_lead(c_lead)

        # STAGE 6: Calculate Quality Score & Tier
        score, tier, breakdown = lead_quality_scorer.calculate_quality_score(enriched_dict)
        enriched_dict["quality_score"] = score
        enriched_dict["quality_tier"] = tier
        enriched_dict["scoring_breakdown"] = breakdown

        if tier == "Hot":
            hot_count += 1
        elif tier == "Warm":
            warm_count += 1
        else:
            cold_count += 1

        # STAGE 8: Ingest into Enterprise Knowledge Fabric
        kobj_id = None
        try:
            kdoc = await enterprise_knowledge_gateway.ingest_asset(
                title=f"Lead: {enriched_dict['company_name']}",
                content_or_uri=f"{enriched_dict.get('ai_summary', '')}\nIndustry: {enriched_dict.get('industry')}\nCity: {enriched_dict.get('city')}",
                asset_type="lead_discovery",
                user_id=str(job.owner_id),
                metadata=enriched_dict,
            )
            kobj_id = kdoc.document_id
        except Exception as e:
            logger.warning(f"[DiscoveryTask] Knowledge Fabric auto-ingest notice for {enriched_dict['company_name']}: {e}")

        # Construct DiscoveredCompanyDocument
        comp_doc = DiscoveredCompanyDocument(
            job_id=job_id,
            owner_id=str(job.owner_id),
            fingerprint=enriched_dict["fingerprint"],
            is_merged=enriched_dict["is_merged"],
            merged_from=enriched_dict["merged_from"],
            company_name=enriched_dict["company_name"],
            trade_name=enriched_dict.get("trade_name"),
            phones=enriched_dict.get("phones", []),
            emails=enriched_dict.get("emails", []),
            website=enriched_dict.get("website"),
            website_domain=enriched_dict.get("website_domain"),
            address=enriched_dict.get("address"),
            city=enriched_dict.get("city"),
            state=enriched_dict.get("state"),
            postal_code=enriched_dict.get("postal_code"),
            country=enriched_dict.get("country", "IN"),
            coordinates=enriched_dict.get("coordinates"),
            gst=enriched_dict.get("gst"),
            categories=enriched_dict.get("categories", []),
            industry=enriched_dict.get("industry"),
            products=enriched_dict.get("products", []),
            business_type=enriched_dict.get("business_type"),
            rating=enriched_dict.get("rating"),
            review_count=enriched_dict.get("review_count"),
            photos=enriched_dict.get("photos", []),
            description=enriched_dict.get("description"),
            ai_summary=enriched_dict.get("ai_summary"),
            business_maturity=enriched_dict.get("business_maturity"),
            buyer_intent=enriched_dict.get("buyer_intent"),
            employees_estimate=enriched_dict.get("employees_estimate"),
            quality_score=score,
            quality_tier=tier,
            scoring_breakdown=breakdown,
            sources=enriched_dict.get("sources", []),
            source_providers=enriched_dict.get("source_providers", []),
            enrichment_status="completed",
            knowledge_object_id=kobj_id,
            knowledge_created=bool(kobj_id),
        )
        try:
            await comp_doc.insert()
        except Exception:
            pass

        enriched_company_docs.append(comp_doc)

        # Legacy dict representation for ScrapeJob sub-document
        final_legacy_results.append({
            "id": f"{job_id}_{idx}",
            "name": enriched_dict["company_name"],
            "website": enriched_dict.get("website") or "",
            "phone": enriched_dict["phones"][0] if enriched_dict.get("phones") else "",
            "email": enriched_dict["emails"][0] if enriched_dict.get("emails") else "",
            "location": f"{enriched_dict.get('city') or job.location}, {enriched_dict.get('country', 'IN')}",
            "score": score,
            "provider": ", ".join(enriched_dict.get("source_providers", ["google_maps"])),
        })

        progress_val = 60.0 + ((idx + 1) / max(1, len(canonical_leads))) * 35.0
        job = await job_repo.update(job, {"progress": round(progress_val, 1)})

    # STAGE 7: Save Results to Job
    await job_repo.update(job, {
        "status": "completed",
        "progress": 100.0,
        "total_results": len(final_legacy_results),
        "results": final_legacy_results,
    })

    total_duration_ms = (time.time() - start_time) * 1000.0
    logger.info(f"[DiscoveryTask] STAGE 7: Saved {len(final_legacy_results)} Enriched Leads to Job {job_id} in {round(total_duration_ms, 1)}ms")

    # STAGE 9: Event Bus Dispatch & Analytics Recording
    await event_bus.publish(LeadDiscoveredEvent(
        source="DiscoveryPipeline",
        payload={
            "job_id": job_id,
            "keyword": job.keyword,
            "location": job.location,
            "total_discovered": len(canonical_leads),
            "merged_duplicates": dedup_result.merged_count,
            "hot_leads": hot_count,
            "warm_leads": warm_count,
            "cold_leads": cold_count,
        }
    ))

    await discovery_analytics.record_job_completed(
        discovered_count=len(canonical_leads),
        merged_count=dedup_result.merged_count,
        hot_count=hot_count,
        warm_count=warm_count,
        cold_count=cold_count,
        duration_ms=total_duration_ms,
        owner_id=str(job.owner_id),
    )


@celery_app.task(name="run_discovery")
def run_discovery(job_id: str):
    """Celery task entrypoint setting up event loop for pipeline execution."""
    asyncio.run(async_run_discovery(job_id))
