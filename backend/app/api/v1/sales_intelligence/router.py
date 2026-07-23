"""
REST API Router for Phase 8: Advanced Sales Intelligence.

Endpoints:
- POST   /api/v1/sales-intelligence/analyze
- GET    /api/v1/sales-intelligence/lead/{lead_id}
- GET    /api/v1/sales-intelligence/{job_id}/status
- GET    /api/v1/sales-intelligence/{lead_id}/signals
- GET    /api/v1/sales-intelligence/{lead_id}/decision-makers
- GET    /api/v1/sales-intelligence/{lead_id}/timeline
- GET    /api/v1/sales-intelligence/{lead_id}/intent
- GET    /api/v1/sales-intelligence/{lead_id}/recommendations
- DELETE /api/v1/sales-intelligence/lead/{lead_id}
"""
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, status

from app.api.deps import get_current_user, get_sales_intelligence_module
from app.database.mongodb.collections.user import User
from app.modules.sales_intelligence.sales_intelligence_module import SalesIntelligenceModule
from app.schemas.sales_intelligence import (
    SalesIntelligenceAnalyzeRequest,
    SalesIntelligenceResponse,
    SalesIntelligenceStatusResponse,
    DecisionMakerSchema,
    GrowthSignalSchema,
    TimelineSchema,
    SalesRecommendationSchema,
)

router = APIRouter()


@router.post(
    "/analyze",
    response_model=SalesIntelligenceStatusResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Enqueue Sales Intelligence Enrichment Job",
    description="Validates lead and enqueues Celery background job for Decision Maker Discovery, Growth Signals, Intent Scoring, Graph Generation, and AI Sales Recommendations.",
)
async def analyze_sales_intelligence(
    payload: SalesIntelligenceAnalyzeRequest,
    current_user: User = Depends(get_current_user),
    module: SalesIntelligenceModule = Depends(get_sales_intelligence_module),
):
    return await module.start_analysis(payload, str(current_user.id))


@router.get(
    "/lead/{lead_id}",
    response_model=SalesIntelligenceResponse,
    summary="Fetch Full Sales Intelligence Report by Lead ID",
)
async def get_sales_intelligence_report(
    lead_id: str,
    current_user: User = Depends(get_current_user),
    module: SalesIntelligenceModule = Depends(get_sales_intelligence_module),
):
    return await module.get_by_lead(lead_id, str(current_user.id))


@router.get(
    "/{job_id}/status",
    response_model=SalesIntelligenceStatusResponse,
    summary="Poll Sales Intelligence Enrichment Job Status",
)
async def get_job_status(
    job_id: str,
    current_user: User = Depends(get_current_user),
    module: SalesIntelligenceModule = Depends(get_sales_intelligence_module),
):
    return await module.get_job_status(job_id, str(current_user.id))


@router.get(
    "/{lead_id}/signals",
    response_model=List[GrowthSignalSchema],
    summary="Fetch Company Growth Signals",
)
async def get_growth_signals(
    lead_id: str,
    current_user: User = Depends(get_current_user),
    module: SalesIntelligenceModule = Depends(get_sales_intelligence_module),
):
    report = await module.get_by_lead(lead_id, str(current_user.id))
    return report.growth_signals


@router.get(
    "/{lead_id}/decision-makers",
    response_model=List[DecisionMakerSchema],
    summary="Fetch Discovered Decision Makers",
)
async def get_decision_makers(
    lead_id: str,
    current_user: User = Depends(get_current_user),
    module: SalesIntelligenceModule = Depends(get_sales_intelligence_module),
):
    report = await module.get_by_lead(lead_id, str(current_user.id))
    return report.decision_makers


@router.get(
    "/{lead_id}/timeline",
    response_model=TimelineSchema,
    summary="Fetch Company Timeline",
)
async def get_company_timeline(
    lead_id: str,
    current_user: User = Depends(get_current_user),
    module: SalesIntelligenceModule = Depends(get_sales_intelligence_module),
):
    report = await module.get_by_lead(lead_id, str(current_user.id))
    return report.timeline


@router.get(
    "/{lead_id}/intent",
    summary="Fetch Intent Score & Opportunity Classification",
)
async def get_intent_and_classification(
    lead_id: str,
    current_user: User = Depends(get_current_user),
    module: SalesIntelligenceModule = Depends(get_sales_intelligence_module),
):
    report = await module.get_by_lead(lead_id, str(current_user.id))
    return {
        "intent_score": report.intent_score,
        "intent_level": report.intent_level,
        "intent_reason": report.intent_reason,
        "classification": report.classification,
    }


@router.get(
    "/{lead_id}/recommendations",
    response_model=SalesRecommendationSchema,
    summary="Fetch AI Sales Strategy Playbook Recommendations",
)
async def get_sales_recommendations(
    lead_id: str,
    current_user: User = Depends(get_current_user),
    module: SalesIntelligenceModule = Depends(get_sales_intelligence_module),
):
    report = await module.get_by_lead(lead_id, str(current_user.id))
    return report.recommendations


@router.delete(
    "/lead/{lead_id}",
    summary="Delete Sales Intelligence Report",
)
async def delete_sales_intelligence_report(
    lead_id: str,
    current_user: User = Depends(get_current_user),
    module: SalesIntelligenceModule = Depends(get_sales_intelligence_module),
):
    return await module.delete_report(lead_id, str(current_user.id))
