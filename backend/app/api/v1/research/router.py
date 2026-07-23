"""
REST API Router for Phase 9: AI Research Agents.
"""
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user, get_research_module
from app.database.mongodb.collections.user import User
from app.modules.research.research_module import ResearchModule
from app.schemas.research import (
    ResearchAnalyzeRequest,
    ResearchStatusResponse,
    ResearchReportResponse,
    WebsiteResearchSchema,
    NewsResearchSchema,
    TechnologyResearchSchema,
    HiringResearchSchema,
    CompetitorResearchSchema,
    SocialResearchSchema,
    RelationshipGraphSchema,
)

router = APIRouter()


@router.post(
    "/analyze",
    response_model=ResearchStatusResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Enqueue AI Multi-Agent Research Analysis",
    description="Trigger an asynchronous multi-agent background research pipeline across website, news, hiring, tech stack, competitors, and social footprint.",
)
async def analyze_company_research(
    payload: ResearchAnalyzeRequest,
    current_user: User = Depends(get_current_user),
    service: ResearchModule = Depends(get_research_module),
):
    """Enqueue AI research pipeline."""
    try:
        doc = await service.initiate_research_analysis(
            lead_id=payload.lead_id,
            owner_id=str(current_user.id),
        )
        return ResearchStatusResponse(
            id=str(doc.id),
            lead_id=str(doc.lead_id),
            company_name=doc.company_name,
            status=doc.status,
            progress=doc.progress,
            overall_confidence=doc.overall_confidence,
            error_message=doc.error_message,
        )
    except ValueError as val_err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(val_err))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to trigger research job: {str(e)}")


@router.get(
    "/{job_id}/status",
    response_model=ResearchStatusResponse,
    summary="Poll Research Analysis Job Status",
    description="Check the current execution status (pending, running, completed, failed) and progress (0-100%) of a research job.",
)
async def get_research_job_status(
    job_id: str,
    current_user: User = Depends(get_current_user),
    service: ResearchModule = Depends(get_research_module),
):
    """Poll research job status."""
    doc = await service.get_report_by_id(job_id, str(current_user.id))
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Research job report not found.")
    
    return ResearchStatusResponse(
        id=str(doc.id),
        lead_id=str(doc.lead_id),
        company_name=doc.company_name,
        status=doc.status,
        progress=doc.progress,
        overall_confidence=doc.overall_confidence,
        error_message=doc.error_message,
    )


@router.get(
    "/lead/{lead_id}",
    response_model=ResearchReportResponse,
    summary="Get Consolidated Research Report by Lead ID",
    description="Fetch the complete consolidated AI Research Report including all agent findings, knowledge graph, verified facts, and AI executive summary.",
)
async def get_research_report_by_lead(
    lead_id: str,
    current_user: User = Depends(get_current_user),
    service: ResearchModule = Depends(get_research_module),
):
    """Fetch full consolidated research report."""
    doc = await service.get_report_by_lead(lead_id, str(current_user.id))
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No research report found for this lead.")

    return ResearchReportResponse(
        id=str(doc.id),
        lead_id=str(doc.lead_id),
        company_name=doc.company_name,
        website_url=doc.website_url,
        status=doc.status,
        progress=doc.progress,
        overall_confidence=doc.overall_confidence,
        error_message=doc.error_message,
        website_findings=doc.website_findings.dict() if doc.website_findings else None,
        news_findings=doc.news_findings.dict() if doc.news_findings else None,
        hiring_findings=doc.hiring_findings.dict() if doc.hiring_findings else None,
        tech_findings=doc.tech_findings.dict() if doc.tech_findings else None,
        competitor_findings=doc.competitor_findings.dict() if doc.competitor_findings else None,
        social_findings=doc.social_findings.dict() if doc.social_findings else None,
        knowledge_graph=doc.knowledge_graph.dict() if doc.knowledge_graph else None,
        verified_facts=[f.dict() for f in (doc.verified_facts or [])],
        ai_summary=doc.ai_summary.dict() if doc.ai_summary else None,
        analyzed_at=doc.analyzed_at,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
    )


@router.get(
    "/{lead_id}/website",
    response_model=WebsiteResearchSchema,
    summary="Get Website Research Agent Findings",
)
async def get_website_research(
    lead_id: str,
    current_user: User = Depends(get_current_user),
    service: ResearchModule = Depends(get_research_module),
):
    """Fetch website agent findings."""
    doc = await service.get_report_by_lead(lead_id, str(current_user.id))
    if not doc or not doc.website_findings:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Website research findings not available.")
    return doc.website_findings


@router.get(
    "/{lead_id}/news",
    response_model=NewsResearchSchema,
    summary="Get News Research Agent Findings",
)
async def get_news_research(
    lead_id: str,
    current_user: User = Depends(get_current_user),
    service: ResearchModule = Depends(get_research_module),
):
    """Fetch news agent findings."""
    doc = await service.get_report_by_lead(lead_id, str(current_user.id))
    if not doc or not doc.news_findings:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="News research findings not available.")
    return doc.news_findings


@router.get(
    "/{lead_id}/technology",
    response_model=TechnologyResearchSchema,
    summary="Get Technology Research Agent Findings",
)
async def get_technology_research(
    lead_id: str,
    current_user: User = Depends(get_current_user),
    service: ResearchModule = Depends(get_research_module),
):
    """Fetch technology agent findings."""
    doc = await service.get_report_by_lead(lead_id, str(current_user.id))
    if not doc or not doc.tech_findings:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Technology research findings not available.")
    return doc.tech_findings


@router.get(
    "/{lead_id}/hiring",
    response_model=HiringResearchSchema,
    summary="Get Hiring Research Agent Findings",
)
async def get_hiring_research(
    lead_id: str,
    current_user: User = Depends(get_current_user),
    service: ResearchModule = Depends(get_research_module),
):
    """Fetch hiring agent findings."""
    doc = await service.get_report_by_lead(lead_id, str(current_user.id))
    if not doc or not doc.hiring_findings:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hiring research findings not available.")
    return doc.hiring_findings


@router.get(
    "/{lead_id}/competitors",
    response_model=CompetitorResearchSchema,
    summary="Get Competitor Research Agent Findings",
)
async def get_competitor_research(
    lead_id: str,
    current_user: User = Depends(get_current_user),
    service: ResearchModule = Depends(get_research_module),
):
    """Fetch competitor agent findings."""
    doc = await service.get_report_by_lead(lead_id, str(current_user.id))
    if not doc or not doc.competitor_findings:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Competitor research findings not available.")
    return doc.competitor_findings


@router.get(
    "/{lead_id}/social",
    response_model=SocialResearchSchema,
    summary="Get Social Research Agent Findings",
)
async def get_social_research(
    lead_id: str,
    current_user: User = Depends(get_current_user),
    service: ResearchModule = Depends(get_research_module),
):
    """Fetch social agent findings."""
    doc = await service.get_report_by_lead(lead_id, str(current_user.id))
    if not doc or not doc.social_findings:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Social research findings not available.")
    return doc.social_findings


@router.get(
    "/{lead_id}/graph",
    response_model=RelationshipGraphSchema,
    summary="Get Research Knowledge Graph",
)
async def get_research_graph(
    lead_id: str,
    current_user: User = Depends(get_current_user),
    service: ResearchModule = Depends(get_research_module),
):
    """Fetch research knowledge graph."""
    doc = await service.get_report_by_lead(lead_id, str(current_user.id))
    if not doc or not doc.knowledge_graph:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Research knowledge graph not available.")
    return doc.knowledge_graph


@router.delete(
    "/lead/{lead_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete Research Report",
)
async def delete_research_report(
    lead_id: str,
    current_user: User = Depends(get_current_user),
    service: ResearchModule = Depends(get_research_module),
):
    """Delete research report for a lead."""
    deleted = await service.delete_report(lead_id, str(current_user.id))
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Research report not found or delete failed.")
    return {"status": "success", "message": f"Research report for lead {lead_id} deleted."}
