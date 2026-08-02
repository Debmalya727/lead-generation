"""
Celery background task for AI Lead Scoring.

Pipeline stages:
    10%  → Initialize DB, load LeadScore document
    25%  → Load Lead + CompanyIntelligence documents
    40%  → Feature extraction
    55%  → Rule engine scoring
    70%  → Build LLM prompt
    85%  → LLM reasoning call + parse response
    100% → Save results, mark completed
"""
import asyncio
import json
import logging
from datetime import datetime, timezone

from app.database.mongodb.connection import DatabaseManager
from app.database.mongodb.repositories.scoring_repository import ScoringRepository
from app.database.mongodb.repositories.lead_repository import LeadRepository
from app.database.mongodb.repositories.intelligence_repository import IntelligenceRepository
from app.modules.scoring.feature_extractor import ScoringFeatureExtractor
from app.modules.scoring.rule_engine import RuleEngine
from app.modules.scoring.prompt_builder import ScoringPromptBuilder
from app.ai.providers.factory import get_llm_provider
from app.tasks.worker import celery_app

logger = logging.getLogger("backend.tasks.scoring")


def _classify_priority(score: int) -> str:
    """Classify lead priority based on score."""
    if score >= 70:
        return "Hot"
    if score >= 40:
        return "Warm"
    return "Cold"


async def async_run_scoring(doc_id: str) -> None:
    """Async scoring pipeline executed by the Celery worker."""
    await DatabaseManager.initialize()

    scoring_repo = ScoringRepository()

    # Stage 1: Load score document (10%)
    doc = await scoring_repo.get_by_id_no_auth(doc_id)
    if not doc:
        logger.error(f"Scoring task: doc {doc_id} not found in DB.")
        return

    await scoring_repo.update(doc, {"status": "running", "progress": 10.0})
    logger.info(f"Starting lead scoring for '{doc.company_name}' (doc_id={doc_id})")

    try:
        # Stage 2: Load Lead + Intelligence documents (25%)
        lead_repo = LeadRepository()
        intel_repo = IntelligenceRepository()

        lead = await lead_repo.get_by_id(str(doc.lead_id), str(doc.owner_id))
        if not lead:
            raise ValueError(f"Lead {doc.lead_id} not found for owner {doc.owner_id}")

        intel_doc = await intel_repo.get_by_lead_id(str(doc.lead_id), str(doc.owner_id))
        # intel_doc may be None if intelligence hasn't been run — that's OK

        doc = await scoring_repo.get_by_id_no_auth(doc_id)
        if not doc:
            return
        await scoring_repo.update(doc, {"progress": 25.0})

        # Stage 3: Feature extraction (40%)
        extractor = ScoringFeatureExtractor()
        fv = extractor.extract(lead, intel_doc)

        doc = await scoring_repo.get_by_id_no_auth(doc_id)
        if not doc:
            return
        await scoring_repo.update(doc, {"progress": 40.0})

        # Stage 4: Rule engine scoring (55%)
        rule_engine = RuleEngine()
        rule_score, breakdown = rule_engine.compute(fv)

        doc = await scoring_repo.get_by_id_no_auth(doc_id)
        if not doc:
            return
        await scoring_repo.update(doc, {
            "rule_score": rule_score,
            "score_breakdown": [entry.to_dict() for entry in breakdown],
            "progress": 55.0,
        })

        # Stage 5: Build LLM prompt (70%)
        prompt_builder = ScoringPromptBuilder()
        prompt = prompt_builder.build_prompt(fv, rule_score, breakdown)
        system_prompt = prompt_builder.get_system_prompt()

        doc = await scoring_repo.get_by_id_no_auth(doc_id)
        if not doc:
            return
        await scoring_repo.update(doc, {"progress": 70.0})

        # Stage 6: LLM reasoning call (85%)
        llm = get_llm_provider("lead_scorer")
        logger.info(f"Calling LLM ({type(llm).__name__}) for scoring reasoning on '{fv.company_name}'")
        raw_response = await llm.complete(prompt=prompt, system_prompt=system_prompt)
        await scoring_repo.update(doc, {"progress": 85.0})

        # Parse LLM response
        doc = await scoring_repo.get_by_id_no_auth(doc_id)
        if not doc:
            return

        clean_response = prompt_builder.clean_response(raw_response)
        try:
            llm_data = json.loads(clean_response)
        except json.JSONDecodeError as je:
            logger.error(f"LLM returned invalid JSON for '{fv.company_name}': {je}")
            logger.debug(f"Raw LLM response: {raw_response[:500]}")
            llm_data = {}

        # Calculate final score with LLM adjustment (clamped -10 to +10)
        raw_adjustment = llm_data.get("score_adjustment", 0)
        adjustment = max(-10, min(10, int(raw_adjustment) if raw_adjustment else 0))
        final_score = max(0, min(100, rule_score + adjustment))
        priority = _classify_priority(final_score)

        # Stage 7: Save complete results (100%)
        # Convert breakdown dicts to ScoreBreakdown objects for storage
        from app.database.mongodb.collections.lead_score import ScoreBreakdown
        breakdown_models = [
            ScoreBreakdown(**entry.to_dict()) for entry in breakdown
        ]

        await scoring_repo.update(doc, {
            "status": "completed",
            "progress": 100.0,
            "score": final_score,
            "priority": priority,
            "rule_score": rule_score,
            "llm_score_adjustment": adjustment,
            "score_breakdown": breakdown_models,
            "strengths": llm_data.get("strengths", []),
            "weaknesses": llm_data.get("weaknesses", []),
            "risk_factors": llm_data.get("risk_factors", []),
            "recommended_outreach": llm_data.get("recommended_outreach"),
            "score_explanation": llm_data.get("score_explanation"),
            "confidence_score": llm_data.get("confidence_score"),
            "scored_at": datetime.now(timezone.utc),
        })

        logger.info(
            f"Lead scoring complete for '{fv.company_name}': "
            f"score={final_score}/100, priority={priority}"
        )

    except Exception as e:
        logger.error(f"Scoring failed for doc {doc_id}: {e}", exc_info=True)
        doc = await scoring_repo.get_by_id_no_auth(doc_id)
        if doc:
            await scoring_repo.update(doc, {
                "status": "failed",
                "progress": 100.0,
                "error_message": str(e),
            })

    finally:
        await DatabaseManager.close()


@celery_app.task(name="run_lead_scoring")
def run_lead_scoring(doc_id: str) -> None:
    """Celery task entrypoint — runs async scoring pipeline in a new event loop."""
    asyncio.run(async_run_scoring(doc_id))
