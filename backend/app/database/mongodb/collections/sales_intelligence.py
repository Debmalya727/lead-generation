"""
Beanie MongoDB Document collections for Phase 8: Advanced Sales Intelligence.

Collections:
- SalesIntelligenceReport (Main Beanie Document)
  Contains embedded schemas for:
  - DecisionMaker
  - GrowthSignal
  - CompanyTimeline
  - SalesOpportunityClassification
  - CompanyRelationshipGraph
  - SalesRecommendation
"""
from datetime import datetime, timezone
from typing import Dict, List, Optional
from beanie import Document, Indexed, PydanticObjectId
from pydantic import BaseModel, Field


class DecisionMaker(BaseModel):
    name: str = Field(..., description="Full name of decision maker")
    designation: str = Field(..., description="Job title / role")
    department: str = Field(..., description="Department (Executive, Tech, Sales, Ops, etc.)")
    linkedin_url: Optional[str] = None
    company_email: Optional[str] = None
    personal_email: Optional[str] = None
    phone: Optional[str] = None
    confidence_score: int = Field(80, ge=0, le=100)
    source: str = Field("website_team_page", description="Discovery source signal")
    discovery_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class GrowthSignal(BaseModel):
    type: str = Field(..., description="hiring | funding | expansion | tech_migration | press | product_launch | social")
    description: str = Field(..., description="Detail of signal detected")
    confidence: int = Field(80, ge=0, le=100)
    source: str = Field("website_scan")
    date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Milestone(BaseModel):
    year_or_date: str
    event: str
    category: str = Field("expansion", description="founding | funding | expansion | milestone | event")


class CompanyTimeline(BaseModel):
    founded_year: Optional[str] = None
    expansion_history: List[str] = Field(default_factory=list)
    funding_history: List[str] = Field(default_factory=list)
    milestones: List[Milestone] = Field(default_factory=list)
    current_stage: str = Field("Growth", description="Startup | Growth | Scale-up | Enterprise")
    future_direction: Optional[str] = None
    recent_events: List[str] = Field(default_factory=list)
    ai_summary: Optional[str] = None


class SalesOpportunityClassification(BaseModel):
    categories: List[str] = Field(default_factory=list, description="Hot Opportunity, Enterprise Target, High Growth, etc.")
    primary_category: str = Field("SMB", description="Primary classification category")
    rationale: Optional[str] = None


class SalesGraphNode(BaseModel):
    id: str
    label: str
    type: str = Field(..., description="company | person | campaign | score | intelligence | tech | industry")


class SalesGraphEdge(BaseModel):
    source_id: str
    target_id: str
    relation_type: str = Field(..., description="employs | scored_by | targets | uses_tech | operates_in | exhibits_signal")
    weight: float = 1.0


class CompanyRelationshipGraph(BaseModel):
    nodes: List[SalesGraphNode] = Field(default_factory=list)
    edges: List[SalesGraphEdge] = Field(default_factory=list)


class SalesRecommendation(BaseModel):
    best_contact_person: Optional[str] = None
    best_outreach_channel: str = Field("Email", description="Email | LinkedIn | Phone | Multi-Channel")
    best_time_to_contact: str = Field("Tuesday - Thursday (09:00 - 11:00 AM)")
    pain_points: List[str] = Field(default_factory=list)
    recommended_product_pitch: Optional[str] = None
    conversation_starter: Optional[str] = None
    recommended_email_tone: str = Field("Professional & Consultative")
    risk_factors: List[str] = Field(default_factory=list)
    opportunity_summary: Optional[str] = None
    competitive_advantage: Optional[str] = None
    objections: List[str] = Field(default_factory=list)
    followup_strategy: Optional[str] = None


class SalesIntelligenceReport(Document):
    lead_id: PydanticObjectId
    company_id: Optional[str] = None
    company_name: str
    website_url: Optional[str] = None
    owner_id: PydanticObjectId

    status: str = Field("pending", description="pending | running | completed | failed")
    progress: float = Field(0.0, ge=0.0, le=100.0)
    error_message: Optional[str] = None

    # Intent Scoring (0-100)
    intent_score: int = Field(50, ge=0, le=100)
    intent_level: str = Field("Medium", description="Very Low | Low | Medium | High | Very High")
    intent_reason: Optional[str] = None

    # Embedded Module Data
    decision_makers: List[DecisionMaker] = Field(default_factory=list)
    growth_signals: List[GrowthSignal] = Field(default_factory=list)
    timeline: Optional[CompanyTimeline] = None
    classification: Optional[SalesOpportunityClassification] = None
    graph: Optional[CompanyRelationshipGraph] = None
    recommendations: Optional[SalesRecommendation] = None

    analyzed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "sales_intelligence_reports"
        indexes = [
            [("owner_id", 1), ("lead_id", 1)],
            [("owner_id", 1), ("status", 1)],
            [("intent_score", -1)],
        ]
