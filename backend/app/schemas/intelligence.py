from datetime import datetime
from typing import Dict, List, Optional
from beanie import PydanticObjectId
from pydantic import BaseModel, Field


class IntelligenceAnalyzeRequest(BaseModel):
    lead_id: str = Field(..., description="Lead ID to analyze")


class TechStackItemSchema(BaseModel):
    name: str
    category: str


class IntelligencePayloadSchema(BaseModel):
    """Structured intelligence extracted by the LLM."""
    executive_summary: Optional[str] = None
    company_description: Optional[str] = None
    products: List[str] = []
    services: List[str] = []
    industry: Optional[str] = None
    company_size: Optional[str] = None
    revenue_estimate: Optional[str] = None
    revenue_confidence: Optional[str] = None
    pain_points: List[str] = []
    buying_signals: List[str] = []
    ideal_sales_angle: Optional[str] = None
    confidence_score: Optional[int] = None


class IntelligenceStatusResponse(BaseModel):
    """Lightweight status response for progress polling."""
    id: PydanticObjectId
    lead_id: PydanticObjectId
    company_name: str
    website_url: str
    status: str
    progress: float
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        populate_by_name = True


class IntelligenceResponse(BaseModel):
    """Full intelligence report response."""
    id: PydanticObjectId
    lead_id: PydanticObjectId
    owner_id: PydanticObjectId
    company_name: str
    website_url: str
    status: str
    progress: float
    error_message: Optional[str] = None

    # AI-extracted payload
    intelligence: Optional[IntelligencePayloadSchema] = None

    # Crawler-extracted fields
    tech_stack: List[TechStackItemSchema] = []
    social_links: Dict[str, str] = {}
    contact_page: Optional[str] = None
    careers_page: Optional[str] = None
    about_page: Optional[str] = None

    created_at: datetime
    updated_at: datetime
    analyzed_at: Optional[datetime] = None

    @classmethod
    def from_orm(cls, doc: object) -> "IntelligenceResponse":
        """Custom from_orm that handles conversion of nested Beanie models."""
        data = {}
        for field in cls.model_fields:
            val = getattr(doc, field, None)
            data[field] = val

        # Convert IntelligencePayload Beanie model -> IntelligencePayloadSchema dict
        intelligence_val = getattr(doc, "intelligence", None)
        if intelligence_val is not None and not isinstance(intelligence_val, dict):
            data["intelligence"] = IntelligencePayloadSchema.model_validate(
                intelligence_val.model_dump() if hasattr(intelligence_val, "model_dump") else dict(intelligence_val)
            )

        # Convert tech_stack list of dicts/Beanie models
        tech_stack_val = getattr(doc, "tech_stack", [])
        data["tech_stack"] = [
            TechStackItemSchema.model_validate(
                t if isinstance(t, dict) else (t.model_dump() if hasattr(t, "model_dump") else dict(t))
            )
            for t in (tech_stack_val or [])
        ]

        return cls.model_validate(data)

    class Config:
        from_attributes = True
        populate_by_name = True
        arbitrary_types_allowed = True
