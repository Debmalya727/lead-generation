"""
LeadScore Beanie document — AI-generated lead quality scoring report.

Stores:
- Overall score (0-100) with priority classification
- Rule engine sub-score breakdown per feature
- LLM-generated qualitative outputs (strengths, weaknesses, risks, outreach)
- Scoring version for future profile extensibility
"""
from datetime import datetime, timezone
from typing import List, Optional
from beanie import Document, PydanticObjectId
from pydantic import BaseModel, Field
from pymongo import IndexModel, ASCENDING


class ScoreBreakdown(BaseModel):
    """Per-feature scoring breakdown from the rule engine."""
    feature: str = Field(..., description="Feature name, e.g. 'buying_signals'")
    label: str = Field(..., description="Human-readable label, e.g. 'Buying Signals'")
    score: int = Field(..., ge=0, description="Points awarded for this feature")
    max_score: int = Field(..., ge=0, description="Maximum possible points for this feature")
    rationale: str = Field(..., description="One-line explanation of the score awarded")


class LeadScore(Document):
    """Complete AI lead scoring report associated with a Lead document."""
    lead_id: PydanticObjectId = Field(..., description="ID of the associated Lead")
    owner_id: PydanticObjectId = Field(..., description="Owner user ID for access control")
    company_name: str = Field(..., description="Company name from the lead")
    website_url: Optional[str] = Field(None, description="Website URL (if available)")

    # Job tracking
    status: str = Field(default="pending", description="pending | running | completed | failed")
    progress: float = Field(default=0.0, description="Progress 0.0–100.0")
    error_message: Optional[str] = Field(None, description="Error detail if failed")

    # Scoring results
    score: Optional[int] = Field(None, ge=0, le=100, description="Overall lead score 0-100")
    priority: Optional[str] = Field(None, description="Hot | Warm | Cold")
    rule_score: Optional[int] = Field(None, description="Raw rule engine score before LLM adjustment")
    llm_score_adjustment: int = Field(default=0, description="LLM delta applied to rule score")

    # Breakdown per feature
    score_breakdown: List[ScoreBreakdown] = Field(
        default_factory=list,
        description="Per-feature score breakdown from the rule engine"
    )

    # LLM qualitative outputs
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    risk_factors: List[str] = Field(default_factory=list)
    recommended_outreach: Optional[str] = Field(None, description="Recommended outreach strategy")
    score_explanation: Optional[str] = Field(None, description="Natural language explanation of the score")
    confidence_score: Optional[int] = Field(None, ge=0, le=100, description="AI confidence in the scoring 0-100")

    # Scoring profile versioning (future-proofing for industry-specific profiles)
    scoring_version: str = Field(default="v1", description="Scoring profile version")
    scoring_profile: str = Field(default="general_b2b", description="Scoring profile name")

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    scored_at: Optional[datetime] = Field(None, description="Timestamp of last successful scoring")

    class Settings:
        name = "lead_scores"
        indexes = [
            IndexModel(
                [("lead_id", ASCENDING), ("owner_id", ASCENDING)],
                name="idx_score_lead_owner",
                unique=True
            ),
            IndexModel([("owner_id", ASCENDING)], name="idx_score_owner"),
            IndexModel([("score", ASCENDING)], name="idx_score_value"),
            IndexModel([("priority", ASCENDING)], name="idx_score_priority"),
            IndexModel([("status", ASCENDING)], name="idx_score_status"),
        ]

    async def update_timestamp(self) -> None:
        """Update the updated_at timestamp on modification."""
        self.updated_at = datetime.now(timezone.utc)
        await self.save()
