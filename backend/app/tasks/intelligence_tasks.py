"""
Celery background task for AI Company Intelligence analysis.

Pipeline stages:
    10% - Initialize DB, load document
    25% - Crawl website with Playwright
    50% - Content processing and prompt assembly
    75% - LLM completion call
    90% - Parse and validate LLM response
    100% - Save results, mark completed
"""
import asyncio
import json
import logging
from datetime import datetime, timezone

from app.database.mongodb.connection import DatabaseManager
from app.database.mongodb.repositories.intelligence_repository import IntelligenceRepository
from app.modules.intelligence.crawler import WebsiteCrawler
from app.modules.intelligence.content_processor import ContentProcessor
from app.ai.providers.factory import get_llm_provider
from app.tasks.worker import celery_app

logger = logging.getLogger("backend.tasks.intelligence")


async def async_run_intelligence(doc_id: str) -> None:
    """Async intelligence analysis pipeline executed by the Celery worker."""
    await DatabaseManager.initialize()

    intel_repo = IntelligenceRepository()

    # Step 1: Load document from DB (10%)
    doc = await intel_repo.get_by_id_no_auth(doc_id)
    if not doc:
        logger.error(f"Intelligence task: doc {doc_id} not found in DB.")
        return

    if doc.status == "failed":
        logger.info(f"Intelligence task: doc {doc_id} already in failed state, aborting.")
        return

    await intel_repo.update(doc, {"status": "running", "progress": 10.0})
    logger.info(f"Starting intelligence analysis for {doc.company_name} ({doc.website_url})")

    try:
        # Step 2: Crawl website (25%)
        crawler = WebsiteCrawler(timeout_ms=25000)
        crawl_result = await crawler.crawl(doc.website_url)

        # Refresh doc after update
        doc = await intel_repo.get_by_id_no_auth(doc_id)
        if doc is None:
            logger.error(f"Doc {doc_id} vanished after crawl update.")
            return

        if not crawl_result.success or not crawl_result.text_content:
            error_msg = crawl_result.error or "Crawler returned empty content."
            logger.warning(f"Crawl partial failure for {doc.website_url}: {error_msg}")
            text_content = (
                f"Company: {doc.company_name}\nWebsite: {doc.website_url}\n"
                "(Website content could not be retrieved. Perform analysis based on company name only.)"
            )
        else:
            text_content = crawl_result.text_content

        # Save crawler-detected fields immediately (independent of LLM)
        await intel_repo.update(doc, {
            "progress": 25.0,
            "tech_stack": crawl_result.tech_stack,
            "social_links": crawl_result.social_links,
            "contact_page": crawl_result.contact_page,
            "careers_page": crawl_result.careers_page,
            "about_page": crawl_result.about_page,
        })

        doc = await intel_repo.get_by_id_no_auth(doc_id)
        if doc is None:
            return

        # Step 3: Content processing — build LLM prompt (50%)
        processor = ContentProcessor()
        prompt = processor.build_analysis_prompt(
            text_content=text_content,
            company_name=doc.company_name,
            website_url=doc.website_url,
        )
        system_prompt = processor.get_system_prompt()
        await intel_repo.update(doc, {"progress": 50.0})

        doc = await intel_repo.get_by_id_no_auth(doc_id)
        if doc is None:
            return

        # Step 4: LLM extraction call (75%)
        llm = get_llm_provider()
        logger.info(f"Calling LLM provider ({type(llm).__name__}) for {doc.company_name}")
        raw_response = await llm.complete(prompt=prompt, system_prompt=system_prompt)
        await intel_repo.update(doc, {"progress": 75.0})

        doc = await intel_repo.get_by_id_no_auth(doc_id)
        if doc is None:
            return

        # Step 5: Parse and validate LLM JSON response (90%)
        clean_response = processor.clean_llm_response(raw_response)
        try:
            extracted_data = json.loads(clean_response)
        except json.JSONDecodeError as je:
            logger.error(f"LLM returned invalid JSON for {doc.company_name}: {str(je)}")
            logger.debug(f"Raw LLM response: {raw_response[:500]}")
            extracted_data = {}

        # Build IntelligencePayload from extracted data
        from app.database.mongodb.collections.intelligence import IntelligencePayload
        intelligence_payload = IntelligencePayload(
            executive_summary=extracted_data.get("executive_summary"),
            company_description=extracted_data.get("company_description"),
            products=extracted_data.get("products", []),
            services=extracted_data.get("services", []),
            industry=extracted_data.get("industry"),
            company_size=extracted_data.get("company_size"),
            revenue_estimate=extracted_data.get("revenue_estimate"),
            revenue_confidence=extracted_data.get("revenue_confidence"),
            pain_points=extracted_data.get("pain_points", []),
            buying_signals=extracted_data.get("buying_signals", []),
            ideal_sales_angle=extracted_data.get("ideal_sales_angle"),
            confidence_score=extracted_data.get("confidence_score"),
        )

        await intel_repo.update(doc, {"progress": 90.0})

        doc = await intel_repo.get_by_id_no_auth(doc_id)
        if doc is None:
            return

        # Step 6: Save completed results (100%)
        await intel_repo.update(doc, {
            "status": "completed",
            "progress": 100.0,
            "intelligence": intelligence_payload,
            "analyzed_at": datetime.now(timezone.utc),
        })
        logger.info(
            f"Intelligence analysis complete for {doc.company_name}. "
            f"Confidence: {intelligence_payload.confidence_score}/100"
        )

    except Exception as e:
        logger.error(f"Intelligence analysis failed for doc {doc_id}: {str(e)}", exc_info=True)
        doc = await intel_repo.get_by_id_no_auth(doc_id)
        if doc:
            await intel_repo.update(doc, {
                "status": "failed",
                "progress": 100.0,
                "error_message": str(e),
            })

    finally:
        await DatabaseManager.close()


@celery_app.task(name="run_intelligence_analysis")
def run_intelligence_analysis(doc_id: str) -> None:
    """Celery task entrypoint — runs async pipeline in a new event loop."""
    asyncio.run(async_run_intelligence(doc_id))
