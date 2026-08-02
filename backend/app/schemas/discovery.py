"""
Discovery Platform Pydantic Schemas.
Request/Response models for discovery jobs, enriched leads, deduplication logs,
provider health metrics, and analytics dashboards.
"""
from datetime import datetime
from typing import List, Dict, Optional, Any
from beanie import PydanticObjectId
from pydantic import BaseModel, Field


class DiscoveryStartRequest(BaseModel):
    keyword: str = Field(..., min_length=1, description="Keyword target (e.g. HVAC, Restaurant)")
    location: str = Field(..., min_length=1, description="Location filter (e.g. Chicago, Kolkata)")
    providers: List[str] = Field(..., min_length=1, description="Target directories: google_maps, justdial, indiamart, tradeindia")
    website_filter: Optional[str] = Field("all", description="all, without_website, with_website")
    limit: Optional[int] = Field(20, ge=1, le=200, description="Target limit of leads to discover")


class DiscoveredLeadResponse(BaseModel):
    id: str
    name: str
    website: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    location: Optional[str] = None
    score: Optional[int] = None
    provider: str


class DiscoveredCompanyResponse(BaseModel):
    id: str
    company_name: str
    trade_name: Optional[str] = None
    fingerprint: str
    is_merged: bool = False
    merged_from: List[str] = Field(default_factory=list)
    phones: List[str] = Field(default_factory=list)
    emails: List[str] = Field(default_factory=list)
    website: Optional[str] = None
    website_domain: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: str = "IN"
    coordinates: Optional[Dict[str, float]] = None
    gst: Optional[str] = None
    categories: List[str] = Field(default_factory=list)
    industry: Optional[str] = None
    products: List[str] = Field(default_factory=list)
    business_type: Optional[str] = None
    rating: Optional[float] = None
    review_count: Optional[int] = None
    photos: List[str] = Field(default_factory=list)
    ai_summary: Optional[str] = None
    business_maturity: Optional[str] = None
    buyer_intent: Optional[str] = None
    employees_estimate: Optional[str] = None
    quality_score: Optional[int] = None
    quality_tier: Optional[str] = None
    scoring_breakdown: Optional[Dict[str, Any]] = None
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    source_providers: List[str] = Field(default_factory=list)
    crm_created: bool = False
    knowledge_created: bool = False


class DuplicateMergeLogResponse(BaseModel):
    canonical_fingerprint: str
    merged_fingerprints: List[str]
    merged_company_names: List[str]
    merged_providers: List[str]
    match_reasons: List[str]
    confidence: float


class JobStatusResponse(BaseModel):
    id: PydanticObjectId
    keyword: str
    location: str
    providers: List[str]
    status: str
    progress: float
    total_results: int
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        populate_by_name = True


class ProviderHealthResponse(BaseModel):
    provider: str
    status: str
    circuit_state: str
    requests_per_minute_quota: int
    total_requests: int
    success_count: int
    failure_count: int
    avg_latency_ms: float
    last_error: Optional[str] = None
    capabilities: Dict[str, Any] = Field(default_factory=dict)


class SaveLeadsRequest(BaseModel):
    lead_ids: List[str] = Field(..., min_length=1, description="List of discovered lead IDs or fingerprints to import to CRM")
