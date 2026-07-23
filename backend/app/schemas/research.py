"""
Pydantic v2 Validation Schemas for Phase 9: AI Research Agents API.
"""
from typing import List, Dict, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field


class ResearchAnalyzeRequest(BaseModel):
    lead_id: str = Field(..., description="ID of the target lead/company to research")


class ResearchStatusResponse(BaseModel):
    id: str
    lead_id: str
    company_name: str
    status: str = Field(..., description="pending | running | completed | failed")
    progress: float = Field(..., ge=0.0, le=100.0)
    overall_confidence: int = Field(85, ge=0, le=100)
    error_message: Optional[str] = None


class VerifiedFactSchema(BaseModel):
    fact: str
    confidence: int
    source: str
    agent: str
    timestamp: datetime
    verification_method: str


class WebsiteResearchSchema(BaseModel):
    executive_summary: Optional[str] = None
    products: List[str] = Field(default_factory=list)
    services: List[str] = Field(default_factory=list)
    business_model: Optional[str] = None
    target_customers: List[str] = Field(default_factory=list)
    markets: List[str] = Field(default_factory=list)
    technology: List[str] = Field(default_factory=list)
    pain_points: List[str] = Field(default_factory=list)
    crawled_pages: List[str] = Field(default_factory=list)


class NewsArticleSchema(BaseModel):
    headline: str
    summary: str
    category: str
    date: Optional[str] = None
    source: str
    confidence: int


class NewsResearchSchema(BaseModel):
    articles: List[NewsArticleSchema] = Field(default_factory=list)


class HiringDepartmentSchema(BaseModel):
    department: str
    open_count: int
    key_roles: List[str] = Field(default_factory=list)


class HiringResearchSchema(BaseModel):
    departments: List[HiringDepartmentSchema] = Field(default_factory=list)
    open_positions_count: int = 0
    hiring_velocity: str
    growth_stage: str
    expansion_signals: List[str] = Field(default_factory=list)


class TechnologyResearchSchema(BaseModel):
    frontend: List[str] = Field(default_factory=list)
    backend: List[str] = Field(default_factory=list)
    cloud_hosting: List[str] = Field(default_factory=list)
    analytics: List[str] = Field(default_factory=list)
    crm: List[str] = Field(default_factory=list)
    marketing: List[str] = Field(default_factory=list)
    payments: List[str] = Field(default_factory=list)
    cdn: List[str] = Field(default_factory=list)
    database: List[str] = Field(default_factory=list)
    security: List[str] = Field(default_factory=list)
    developer_tools: List[str] = Field(default_factory=list)
    languages_frameworks: List[str] = Field(default_factory=list)
    tech_maturity: str
    migration_opportunities: List[str] = Field(default_factory=list)


class CompetitorSchema(BaseModel):
    name: str
    product_name: Optional[str] = None
    market_position: str
    pricing: Optional[str] = None
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    differentiators: List[str] = Field(default_factory=list)


class CompetitorResearchSchema(BaseModel):
    competitors: List[CompetitorSchema] = Field(default_factory=list)
    market_position_summary: Optional[str] = None


class SocialPlatformSchema(BaseModel):
    platform: str
    url: Optional[str] = None
    posting_frequency: str
    engagement_level: str
    audience_growth_signal: str


class SocialResearchSchema(BaseModel):
    platforms: List[SocialPlatformSchema] = Field(default_factory=list)
    overall_presence_score: int


class GraphNodeSchema(BaseModel):
    id: str
    label: str
    type: str


class GraphEdgeSchema(BaseModel):
    source_id: str
    target_id: str
    relation_type: str
    weight: float


class RelationshipGraphSchema(BaseModel):
    nodes: List[GraphNodeSchema] = Field(default_factory=list)
    edges: List[GraphEdgeSchema] = Field(default_factory=list)


class SWOTAnalysisSchema(BaseModel):
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    opportunities: List[str] = Field(default_factory=list)
    threats: List[str] = Field(default_factory=list)


class AIResearchSummarySchema(BaseModel):
    executive_summary: Optional[str] = None
    swot: Optional[SWOTAnalysisSchema] = None
    business_overview: Optional[str] = None
    sales_opportunity: Optional[str] = None
    risks: List[str] = Field(default_factory=list)
    expansion_opportunities: List[str] = Field(default_factory=list)
    buying_signals: List[str] = Field(default_factory=list)
    pitch_angle: Optional[str] = None
    objections: List[str] = Field(default_factory=list)
    recommended_strategy: Optional[str] = None


class ResearchReportResponse(BaseModel):
    id: str
    lead_id: str
    company_name: str
    website_url: Optional[str] = None
    status: str
    progress: float
    overall_confidence: int
    error_message: Optional[str] = None

    website_findings: Optional[WebsiteResearchSchema] = None
    news_findings: Optional[NewsResearchSchema] = None
    hiring_findings: Optional[HiringResearchSchema] = None
    tech_findings: Optional[TechnologyResearchSchema] = None
    competitor_findings: Optional[CompetitorResearchSchema] = None
    social_findings: Optional[SocialResearchSchema] = None

    knowledge_graph: Optional[RelationshipGraphSchema] = None
    verified_facts: List[VerifiedFactSchema] = Field(default_factory=list)
    ai_summary: Optional[AIResearchSummarySchema] = None

    analyzed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
