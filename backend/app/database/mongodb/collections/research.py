"""
Beanie MongoDB Document collections for Phase 9: AI Research Agents.

Collections:
- ResearchReport (Main Beanie Document)
  Contains embedded schemas for:
  - VerifiedFact
  - WebsiteResearchFinding
  - NewsArticleFinding
  - HiringResearchFinding
  - TechnologyResearchFinding
  - CompetitorResearchFinding
  - SocialResearchFinding
  - ResearchKnowledgeGraph
  - AIResearchSummary
"""
from datetime import datetime, timezone
from typing import Dict, List, Optional
from beanie import Document, PydanticObjectId
from pydantic import BaseModel, Field


class VerifiedFact(BaseModel):
    fact: str = Field(..., description="Statement of verified finding")
    confidence: int = Field(80, ge=0, le=100)
    source: str = Field(..., description="URL or data source")
    agent: str = Field(..., description="Name of agent that verified fact")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    verification_method: str = Field("DOM Crawl & Cross-Validation")


class WebsiteResearchFinding(BaseModel):
    executive_summary: Optional[str] = None
    products: List[str] = Field(default_factory=list)
    services: List[str] = Field(default_factory=list)
    business_model: Optional[str] = None
    target_customers: List[str] = Field(default_factory=list)
    markets: List[str] = Field(default_factory=list)
    technology: List[str] = Field(default_factory=list)
    pain_points: List[str] = Field(default_factory=list)
    crawled_pages: List[str] = Field(default_factory=list)


class NewsArticleFinding(BaseModel):
    headline: str
    summary: str
    category: str = Field("funding", description="funding | acquisition | layoff | leadership | product_launch | partnership | award | expansion")
    date: Optional[str] = None
    source: str
    confidence: int = Field(85, ge=0, le=100)


class NewsResearchFinding(BaseModel):
    articles: List[NewsArticleFinding] = Field(default_factory=list)


class HiringDepartmentSummary(BaseModel):
    department: str
    open_count: int
    key_roles: List[str] = Field(default_factory=list)


class HiringResearchFinding(BaseModel):
    departments: List[HiringDepartmentSummary] = Field(default_factory=list)
    open_positions_count: int = 0
    hiring_velocity: str = Field("Medium", description="High | Medium | Low")
    growth_stage: str = Field("Expansion")
    expansion_signals: List[str] = Field(default_factory=list)


class TechnologyResearchFinding(BaseModel):
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
    tech_maturity: str = Field("Modern Enterprise Stack")
    migration_opportunities: List[str] = Field(default_factory=list)


class CompetitorItem(BaseModel):
    name: str
    product_name: Optional[str] = None
    market_position: str = Field("Direct Competitor")
    pricing: Optional[str] = None
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    differentiators: List[str] = Field(default_factory=list)


class CompetitorResearchFinding(BaseModel):
    competitors: List[CompetitorItem] = Field(default_factory=list)
    market_position_summary: Optional[str] = None


class SocialPlatformFinding(BaseModel):
    platform: str
    url: Optional[str] = None
    posting_frequency: str = Field("Weekly")
    engagement_level: str = Field("Moderate")
    audience_growth_signal: str = Field("Steady Growth")


class SocialResearchFinding(BaseModel):
    platforms: List[SocialPlatformFinding] = Field(default_factory=list)
    overall_presence_score: int = Field(75, ge=0, le=100)


class GraphNode(BaseModel):
    id: str
    label: str
    type: str = Field(..., description="company | product | service | person | competitor | tech | industry | news | hiring")


class GraphEdge(BaseModel):
    source_id: str
    target_id: str
    relation_type: str
    weight: float = 1.0


class ResearchKnowledgeGraph(BaseModel):
    nodes: List[GraphNode] = Field(default_factory=list)
    edges: List[GraphEdge] = Field(default_factory=list)


class SWOTAnalysis(BaseModel):
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    opportunities: List[str] = Field(default_factory=list)
    threats: List[str] = Field(default_factory=list)


class AIResearchSummary(BaseModel):
    executive_summary: Optional[str] = None
    swot: Optional[SWOTAnalysis] = None
    business_overview: Optional[str] = None
    sales_opportunity: Optional[str] = None
    risks: List[str] = Field(default_factory=list)
    expansion_opportunities: List[str] = Field(default_factory=list)
    buying_signals: List[str] = Field(default_factory=list)
    pitch_angle: Optional[str] = None
    objections: List[str] = Field(default_factory=list)
    recommended_strategy: Optional[str] = None


class ResearchReport(Document):
    lead_id: PydanticObjectId
    company_name: str
    website_url: Optional[str] = None
    owner_id: PydanticObjectId

    status: str = Field("pending", description="pending | running | completed | failed")
    progress: float = Field(0.0, ge=0.0, le=100.0)
    overall_confidence: int = Field(85, ge=0, le=100)
    error_message: Optional[str] = None

    # Agent Findings
    website_findings: Optional[WebsiteResearchFinding] = None
    news_findings: Optional[NewsResearchFinding] = None
    hiring_findings: Optional[HiringResearchFinding] = None
    tech_findings: Optional[TechnologyResearchFinding] = None
    competitor_findings: Optional[CompetitorResearchFinding] = None
    social_findings: Optional[SocialResearchFinding] = None

    # Knowledge Graph & Verification
    knowledge_graph: Optional[ResearchKnowledgeGraph] = None
    verified_facts: List[VerifiedFact] = Field(default_factory=list)

    # Consolidated AI Summary
    ai_summary: Optional[AIResearchSummary] = None

    analyzed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "research_reports"
        indexes = [
            [("owner_id", 1), ("lead_id", 1)],
            [("owner_id", 1), ("status", 1)],
            [("overall_confidence", -1)],
        ]
