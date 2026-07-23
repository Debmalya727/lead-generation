"""
Celery background worker pipeline for Phase 8: Advanced Sales Intelligence.

Stages:
  10% - Load document & lead context from DB
  30% - Discover decision makers & verify contact details
  50% - Extract growth signals & build milestone timeline
  70% - Calculate intent score & opportunity classification
  85% - Construct relationship graph
  100% - Call LLM for AI sales recommendations & save completed report
"""
import asyncio
import logging
from datetime import datetime, timezone

from app.database.mongodb.connection import DatabaseManager
from app.database.mongodb.repositories.sales_intelligence_repository import SalesIntelligenceRepository
from app.database.mongodb.repositories.lead_repository import LeadRepository
from app.database.mongodb.repositories.intelligence_repository import IntelligenceRepository
from app.database.mongodb.repositories.scoring_repository import ScoringRepository

from app.modules.sales_intelligence.decision_maker_engine import DecisionMakerEngine
from app.modules.sales_intelligence.signal_engine import SignalEngine
from app.modules.sales_intelligence.intent_engine import IntentEngine
from app.modules.sales_intelligence.graph_engine import GraphEngine
from app.modules.sales_intelligence.recommendation_engine import RecommendationEngine

from app.tasks.worker import celery_app

logger = logging.getLogger("backend.tasks.sales_intelligence")


async def async_run_sales_intelligence(doc_id: str) -> None:
    """Async execution pipeline for sales intelligence enrichment."""
    await DatabaseManager.initialize()

    sales_repo = SalesIntelligenceRepository()
    lead_repo = LeadRepository()
    company_intel_repo = IntelligenceRepository()
    scoring_repo = ScoringRepository()

    # Step 1: Load document from DB (10%)
    doc = await sales_repo.get_by_id_no_auth(doc_id)
    if not doc:
        logger.error(f"Sales Intelligence task: doc {doc_id} not found in DB.")
        return

    if doc.status == "failed":
        logger.info(f"Sales Intelligence task: doc {doc_id} already failed, aborting.")
        return

    await sales_repo.update(doc, {"status": "running", "progress": 10.0})
    logger.info(f"Starting sales intelligence enrichment for '{doc.company_name}' (doc_id={doc_id})")

    try:
        # Load related lead, company intelligence, and lead score data
        lead_id_str = str(doc.lead_id)
        owner_id_str = str(doc.owner_id)

        lead = await lead_repo.get_by_id(lead_id_str, owner_id_str)
        company_intel = await company_intel_repo.get_by_lead_id(lead_id_str, owner_id_str)
        lead_score = await scoring_repo.get_by_lead_id(lead_id_str, owner_id_str)

        # Context variables
        lead_name = lead.name if lead else None
        lead_email = lead.email if lead else None
        lead_phone = lead.phone if lead else None
        website_url = doc.website_url or (lead.website if lead else "")

        intel_data = company_intel.intelligence if company_intel else None
        raw_text = company_intel.website_url if company_intel else ""
        tech_stack = company_intel.tech_stack if company_intel else []
        social_links = company_intel.social_links if company_intel else {}

        industry = (intel_data.industry if intel_data else None) or "B2B Services"
        company_size = (intel_data.company_size if intel_data else None) or "10-50 employees"
        revenue_estimate = (intel_data.revenue_estimate if intel_data else None) or "$1M - $10M"
        pain_points = (intel_data.pain_points if intel_data else [])
        intel_confidence = (intel_data.confidence_score if intel_data else 50) or 50
        lead_score_val = lead_score.score if lead_score else 75

        # Step 2: Discover Decision Makers & Verify Contacts (30%)
        dm_engine = DecisionMakerEngine()
        decision_makers = await dm_engine.discover_decision_makers(
            company_name=doc.company_name,
            website_url=website_url,
            raw_text_content=raw_text,
            lead_contact_name=lead_name,
            lead_contact_email=lead_email,
            lead_contact_phone=lead_phone,
        )
        await sales_repo.update(doc, {
            "progress": 30.0,
            "decision_makers": decision_makers,
        })

        # Step 3: Extract Growth Signals & Build Timeline (50%)
        sig_engine = SignalEngine()
        growth_signals = sig_engine.extract_growth_signals(
            text_content=raw_text,
            tech_stack=tech_stack,
            social_links=social_links,
            careers_page=company_intel.careers_page if company_intel else None,
        )
        timeline = sig_engine.build_timeline(
            company_name=doc.company_name,
            text_content=raw_text,
            growth_signals=growth_signals,
        )
        await sales_repo.update(doc, {
            "progress": 50.0,
            "growth_signals": growth_signals,
            "timeline": timeline,
        })

        # Step 4: Intent Detection & Opportunity Classification (70%)
        intent_engine = IntentEngine()
        intent_score, intent_level, intent_reason = intent_engine.compute_intent(
            lead_score_val=lead_score_val,
            intel_confidence=intel_confidence,
            growth_signals=growth_signals,
            has_email=bool(lead_email or any(dm.company_email for dm in decision_makers)),
            has_phone=bool(lead_phone or any(dm.phone for dm in decision_makers)),
            tech_count=len(tech_stack),
        )
        classification = intent_engine.classify_opportunity(
            company_name=doc.company_name,
            intent_score=intent_score,
            lead_score_val=lead_score_val,
            growth_signals=growth_signals,
            tech_stack=tech_stack,
            company_size=company_size,
        )
        await sales_repo.update(doc, {
            "progress": 70.0,
            "intent_score": intent_score,
            "intent_level": intent_level,
            "intent_reason": intent_reason,
            "classification": classification,
        })

        # Step 5: Build Company Relationship Graph (85%)
        graph_engine = GraphEngine()
        graph = graph_engine.build_graph(
            company_id=str(doc.id),
            company_name=doc.company_name,
            decision_makers=decision_makers,
            growth_signals=growth_signals,
            tech_stack=tech_stack,
            industry=industry,
            lead_score_val=lead_score_val,
        )
        await sales_repo.update(doc, {
            "progress": 85.0,
            "graph": graph,
        })

        # Step 6: Generate AI Sales Playbook Recommendations (100%)
        rec_engine = RecommendationEngine()
        recommendations = await rec_engine.generate_recommendations(
            company_name=doc.company_name,
            website_url=website_url,
            industry=industry,
            company_size=company_size,
            revenue_estimate=revenue_estimate,
            intent_score=intent_score,
            intent_level=intent_level,
            categories=classification.categories,
            decision_makers=decision_makers,
            growth_signals=growth_signals,
            pain_points=pain_points,
            tech_stack=tech_stack,
        )

        await sales_repo.update(doc, {
            "status": "completed",
            "progress": 100.0,
            "recommendations": recommendations,
            "analyzed_at": datetime.now(timezone.utc),
        })

        logger.info(f"Sales Intelligence analysis complete for '{doc.company_name}'. Intent: {intent_score}/100 ({intent_level})")

    except Exception as e:
        logger.error(f"Sales Intelligence analysis failed for doc {doc_id}: {str(e)}", exc_info=True)
        doc = await sales_repo.get_by_id_no_auth(doc_id)
        if doc:
            await sales_repo.update(doc, {
                "status": "failed",
                "progress": 100.0,
                "error_message": str(e),
            })

    finally:
        await DatabaseManager.close()


@celery_app.task(name="run_sales_intelligence_analysis")
def run_sales_intelligence_analysis(doc_id: str) -> None:
    """Celery task entrypoint."""
    asyncio.run(async_run_sales_intelligence(doc_id))
