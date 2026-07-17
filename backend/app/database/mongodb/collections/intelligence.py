from datetime import datetime, timezone
from typing import List, Optional
from beanie import Document, PydanticObjectId
from pydantic import BaseModel, Field
from pymongo import IndexModel, ASCENDING


class TechStackItem(BaseModel):
    name: str = Field(..., description="Technology name, e.g. WordPress, Google Analytics")
    category: str = Field(..., description="Category: CMS, Analytics, Hosting, Framework, CDN, etc.")


class IntelligencePayload(BaseModel):
    """Structured output extracted by the LLM from website content."""
    executive_summary: Optional[str] = Field(None, description="One-paragraph company snapshot")
    company_description: Optional[str] = Field(None, description="Detailed company description")
    products: List[str] = Field(default_factory=list, description="Key products offered")
    services: List[str] = Field(default_factory=list, description="Key services offered")
    industry: Optional[str] = Field(None, description="Primary industry vertical")
    company_size: Optional[str] = Field(None, description="Estimated headcount range, e.g. '10-50 employees'")
    revenue_estimate: Optional[str] = Field(None, description="Estimated annual revenue range")
    revenue_confidence: Optional[str] = Field(None, description="Confidence in revenue estimate: low, medium, high")
    pain_points: List[str] = Field(default_factory=list, description="Likely business pain points")
    buying_signals: List[str] = Field(default_factory=list, description="Positive buying signal indicators")
    ideal_sales_angle: Optional[str] = Field(None, description="Recommended approach for sales engagement")
    confidence_score: Optional[int] = Field(None, ge=0, le=100, description="Overall analysis confidence 0-100")


class CompanyIntelligence(Document):
    lead_id: PydanticObjectId = Field(..., description="ID of the associated Lead document")
    owner_id: PydanticObjectId = Field(..., description="Operator owner ID for access control")
    website_url: str = Field(..., description="URL that was analyzed")
    company_name: str = Field(..., description="Company name from the lead")

    # Job tracking
    status: str = Field(default="pending", description="pending, running, completed, failed")
    progress: float = Field(default=0.0, description="Completion progress 0.0-100.0")
    error_message: Optional[str] = Field(None, description="Error detail if failed")

    # Intelligence payload (populated on completion)
    intelligence: Optional[IntelligencePayload] = Field(None, description="Extracted intelligence data")

    # Crawler-extracted fields (deterministic, no LLM needed)
    tech_stack: List[TechStackItem] = Field(default_factory=list, description="Detected technology stack")
    social_links: dict = Field(default_factory=dict, description="Social media platform -> URL mapping")
    contact_page: Optional[str] = Field(None, description="Detected contact page URL")
    careers_page: Optional[str] = Field(None, description="Detected careers/jobs page URL")
    about_page: Optional[str] = Field(None, description="Detected about page URL")

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    analyzed_at: Optional[datetime] = Field(None, description="Timestamp of last successful analysis")

    class Settings:
        name = "company_intelligence"
        indexes = [
            IndexModel([("lead_id", ASCENDING), ("owner_id", ASCENDING)], name="idx_intel_lead_owner", unique=True),
            IndexModel([("owner_id", ASCENDING)], name="idx_intel_owner"),
            IndexModel([("status", ASCENDING)], name="idx_intel_status"),
        ]

    async def update_timestamp(self) -> None:
        """Update the updated_at timestamp on modification."""
        self.updated_at = datetime.now(timezone.utc)
        await self.save()
