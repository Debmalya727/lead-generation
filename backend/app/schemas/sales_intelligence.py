"""
Pydantic v2 schemas for Phase 8: Advanced Sales Intelligence.
"""
from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class SalesIntelligenceAnalyzeRequest(BaseModel):
    lead_id: str = Field(..., description="ID of the lead to analyze")


class DecisionMakerSchema(BaseModel):
    name: str
    designation: str
    department: str
    linkedin_url: Optional[str] = None
    company_email: Optional[str] = None
    personal_email: Optional[str] = None
    phone: Optional[str] = None
    confidence_score: int
    source: str
    discovery_timestamp: Optional[datetime] = None


class GrowthSignalSchema(BaseModel):
    type: str
    description: str
    confidence: int
    source: str
    date: Optional[datetime] = None


class MilestoneSchema(BaseModel):
    year_or_date: str
    event: str
    category: str


class TimelineSchema(BaseModel):
    founded_year: Optional[str] = None
    expansion_history: List[str] = []
    funding_history: List[str] = []
    milestones: List[MilestoneSchema] = []
    current_stage: str
    future_direction: Optional[str] = None
    recent_events: List[str] = []
    ai_summary: Optional[str] = None


class SalesOpportunityClassificationSchema(BaseModel):
    categories: List[str] = []
    primary_category: str
    rationale: Optional[str] = None


class SalesGraphNodeSchema(BaseModel):
    id: str
    label: str
    type: str


class SalesGraphEdgeSchema(BaseModel):
    source_id: str
    target_id: str
    relation_type: str
    weight: float


class RelationshipGraphSchema(BaseModel):
    nodes: List[SalesGraphNodeSchema] = []
    edges: List[SalesGraphEdgeSchema] = []


class SalesRecommendationSchema(BaseModel):
    best_contact_person: Optional[str] = None
    best_outreach_channel: str
    best_time_to_contact: str
    pain_points: List[str] = []
    recommended_product_pitch: Optional[str] = None
    conversation_starter: Optional[str] = None
    recommended_email_tone: str
    risk_factors: List[str] = []
    opportunity_summary: Optional[str] = None
    competitive_advantage: Optional[str] = None
    objections: List[str] = []
    followup_strategy: Optional[str] = None


class SalesIntelligenceStatusResponse(BaseModel):
    id: str
    lead_id: str
    company_name: str
    status: str
    progress: float
    intent_score: int
    intent_level: str
    error_message: Optional[str] = None

    @classmethod
    def from_orm_doc(cls, doc):
        return cls(
            id=str(doc.id),
            lead_id=str(doc.lead_id),
            company_name=doc.company_name,
            status=doc.status,
            progress=doc.progress,
            intent_score=doc.intent_score,
            intent_level=doc.intent_level,
            error_message=doc.error_message,
        )


class SalesIntelligenceResponse(BaseModel):
    id: str
    lead_id: str
    company_name: str
    website_url: Optional[str] = None
    status: str
    progress: float
    intent_score: int
    intent_level: str
    intent_reason: Optional[str] = None
    decision_makers: List[DecisionMakerSchema] = []
    growth_signals: List[GrowthSignalSchema] = []
    timeline: Optional[TimelineSchema] = None
    classification: Optional[SalesOpportunityClassificationSchema] = None
    graph: Optional[RelationshipGraphSchema] = None
    recommendations: Optional[SalesRecommendationSchema] = None
    analyzed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_orm_doc(cls, doc):
        return cls(
            id=str(doc.id),
            lead_id=str(doc.lead_id),
            company_name=doc.company_name,
            website_url=doc.website_url,
            status=doc.status,
            progress=doc.progress,
            intent_score=doc.intent_score,
            intent_level=doc.intent_level,
            intent_reason=doc.intent_reason,
            decision_makers=[DecisionMakerSchema(**dm.dict()) for dm in doc.decision_makers],
            growth_signals=[GrowthSignalSchema(**gs.dict()) for gs in doc.growth_signals],
            timeline=TimelineSchema(**doc.timeline.dict()) if doc.timeline else None,
            classification=SalesOpportunityClassificationSchema(**doc.classification.dict()) if doc.classification else None,
            graph=RelationshipGraphSchema(**doc.graph.dict()) if doc.graph else None,
            recommendations=SalesRecommendationSchema(**doc.recommendations.dict()) if doc.recommendations else None,
            analyzed_at=doc.analyzed_at,
            created_at=doc.created_at,
            updated_at=doc.updated_at,
        )
