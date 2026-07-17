from datetime import datetime
from typing import List, Optional
from beanie import PydanticObjectId
from pydantic import BaseModel, Field


class ScoringAnalyzeRequest(BaseModel):
    lead_id: str = Field(..., description="Lead ID to score")


class ScoreBreakdownSchema(BaseModel):
    """Per-feature scoring breakdown entry."""
    feature: str
    label: str
    score: int
    max_score: int
    rationale: str


class ScoringStatusResponse(BaseModel):
    """Lightweight status response for progress polling."""
    id: PydanticObjectId
    lead_id: PydanticObjectId
    company_name: str
    status: str
    progress: float
    score: Optional[int] = None
    priority: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_orm(cls, doc: object) -> "ScoringStatusResponse":
        data = {field: getattr(doc, field, None) for field in cls.model_fields}
        return cls.model_validate(data)

    class Config:
        from_attributes = True
        populate_by_name = True
        arbitrary_types_allowed = True


class ScoringResponse(BaseModel):
    """Full scoring report response."""
    id: PydanticObjectId
    lead_id: PydanticObjectId
    owner_id: PydanticObjectId
    company_name: str
    website_url: Optional[str] = None
    status: str
    progress: float
    error_message: Optional[str] = None

    # Scoring outputs
    score: Optional[int] = None
    priority: Optional[str] = None
    rule_score: Optional[int] = None
    llm_score_adjustment: int = 0
    score_breakdown: List[ScoreBreakdownSchema] = []

    # LLM qualitative outputs
    strengths: List[str] = []
    weaknesses: List[str] = []
    risk_factors: List[str] = []
    recommended_outreach: Optional[str] = None
    score_explanation: Optional[str] = None
    confidence_score: Optional[int] = None

    # Metadata
    scoring_version: str = "v1"
    scoring_profile: str = "general_b2b"
    created_at: datetime
    updated_at: datetime
    scored_at: Optional[datetime] = None

    @classmethod
    def from_orm(cls, doc: object) -> "ScoringResponse":
        """Custom from_orm handling conversion of nested ScoreBreakdown models."""
        data = {}
        for field in cls.model_fields:
            data[field] = getattr(doc, field, None)

        # Convert score_breakdown list of Beanie models → dicts → ScoreBreakdownSchema
        breakdown_val = getattr(doc, "score_breakdown", [])
        data["score_breakdown"] = [
            ScoreBreakdownSchema.model_validate(
                b if isinstance(b, dict)
                else (b.model_dump() if hasattr(b, "model_dump") else dict(b))
            )
            for b in (breakdown_val or [])
        ]

        return cls.model_validate(data)

    class Config:
        from_attributes = True
        populate_by_name = True
        arbitrary_types_allowed = True
