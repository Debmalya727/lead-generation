"""
Enterprise Lead Discovery Platform — MongoDB ODM Collections.
Defines canonical documents for discovered companies, provider health,
deduplication merge logs, and discovery analytics.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from beanie import Document, PydanticObjectId
from pydantic import BaseModel, Field
from pymongo import IndexModel, ASCENDING, DESCENDING, TEXT


# ─── Sub-document Models ────────────────────────────────────────────

class ProviderSourceRecord(BaseModel):
    """Record of a provider contributing data to this company."""
    provider: str
    provider_id: Optional[str] = None
    raw_name: Optional[str] = None
    raw_phone: Optional[str] = None
    raw_address: Optional[str] = None
    discovered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    confidence: float = Field(default=1.0)


class SocialProfiles(BaseModel):
    """Extracted social media profiles."""
    linkedin: Optional[str] = None
    facebook: Optional[str] = None
    twitter: Optional[str] = None
    instagram: Optional[str] = None
    youtube: Optional[str] = None
    whatsapp: Optional[str] = None


class TechnologyStack(BaseModel):
    """Detected technology stack from website analysis."""
    cms: Optional[str] = None
    ecommerce: Optional[str] = None
    analytics: Optional[str] = None
    crm: Optional[str] = None
    frameworks: List[str] = Field(default_factory=list)
    hosting: Optional[str] = None
    ssl: bool = False


class BusinessHours(BaseModel):
    """Business operating hours."""
    monday: Optional[str] = None
    tuesday: Optional[str] = None
    wednesday: Optional[str] = None
    thursday: Optional[str] = None
    friday: Optional[str] = None
    saturday: Optional[str] = None
    sunday: Optional[str] = None
    is_24_hours: bool = False


# ─── Enterprise Discovered Company Document ────────────────────────

class DiscoveredCompanyDocument(Document):
    """
    Canonical enriched lead document after normalization, deduplication,
    enrichment, and quality scoring. One document per unique business.
    """

    # Identity
    job_id: str = Field(..., description="Discovery job ID that first found this company")
    owner_id: str = Field(..., description="User who owns this discovery job")

    # Deduplication fingerprint
    fingerprint: str = Field(..., description="Canonical dedup hash: normalized_name+domain+e164_phone")
    is_merged: bool = Field(default=False, description="Whether this is a merged record from multiple providers")
    merged_from: List[str] = Field(default_factory=list, description="List of fingerprints merged into this record")

    # Core business identity
    company_name: str = Field(..., description="Normalized canonical company name")
    trade_name: Optional[str] = Field(None, description="Trade/DBA name if different from company name")

    # Contact information
    phones: List[str] = Field(default_factory=list, description="All E.164 normalized phone numbers")
    emails: List[str] = Field(default_factory=list, description="All verified email addresses")
    website: Optional[str] = Field(None, description="Canonical website URL")
    website_domain: Optional[str] = Field(None, description="Normalized domain for dedup key")

    # Address
    address: Optional[str] = Field(None, description="Full street address")
    city: Optional[str] = Field(None, description="City")
    state: Optional[str] = Field(None, description="State or province")
    postal_code: Optional[str] = Field(None, description="ZIP or postal code")
    country: str = Field(default="IN", description="ISO 3166-1 alpha-2 country code")
    coordinates: Optional[Dict[str, float]] = Field(None, description="{lat: float, lng: float}")

    # India-specific compliance fields
    gst: Optional[str] = Field(None, description="GST registration number (15 chars)")
    pan: Optional[str] = Field(None, description="PAN number")
    cin: Optional[str] = Field(None, description="Company Identification Number")

    # Business classification
    categories: List[str] = Field(default_factory=list, description="Business categories from all providers")
    industry: Optional[str] = Field(None, description="AI-classified primary industry")
    products: List[str] = Field(default_factory=list, description="Products offered (from IndiaMART/TradeIndia)")
    business_type: Optional[str] = Field(None, description="Manufacturer/Supplier/Retailer/Service")

    # Ratings & social proof
    rating: Optional[float] = Field(None, description="Average rating (0-5)")
    review_count: Optional[int] = Field(None, description="Total number of reviews")
    photos: List[str] = Field(default_factory=list, description="Photo URLs")
    business_status: Optional[str] = Field(None, description="OPERATIONAL/CLOSED_TEMPORARILY/CLOSED_PERMANENTLY")

    # Hours
    business_hours: Optional[BusinessHours] = None

    # Social profiles
    social_profiles: Optional[SocialProfiles] = None

    # Technology stack (from enrichment)
    tech_stack: Optional[TechnologyStack] = None

    # Description & AI-generated content
    description: Optional[str] = Field(None, description="Company description (crawled or extracted)")
    ai_summary: Optional[str] = Field(None, description="AI-generated 2-3 sentence company summary")
    business_maturity: Optional[str] = Field(None, description="AI assessment: Startup/SME/Enterprise/Established")
    buyer_intent: Optional[str] = Field(None, description="AI estimated buyer intent: High/Medium/Low")
    employees_estimate: Optional[str] = Field(None, description="Estimated employee count range")

    # Quality scoring
    quality_score: Optional[int] = Field(None, description="Calculated quality score 0-100")
    quality_tier: Optional[str] = Field(None, description="Hot/Warm/Cold")
    scoring_breakdown: Optional[Dict[str, Any]] = Field(None, description="Score component breakdown")

    # Multi-provider source tracking
    sources: List[ProviderSourceRecord] = Field(default_factory=list, description="All provider source records")
    source_providers: List[str] = Field(default_factory=list, description="Provider names that found this company")

    # Integration tracking
    enrichment_status: str = Field(default="pending", description="pending/running/completed/failed/skipped")
    enriched_at: Optional[datetime] = None
    crm_id: Optional[str] = Field(None, description="CRM Lead document ID after save")
    knowledge_object_id: Optional[str] = Field(None, description="Knowledge Fabric document ID")
    crm_created: bool = Field(default=False)
    knowledge_created: bool = Field(default=False)

    # Timestamps
    discovered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "discovered_companies"
        indexes = [
            IndexModel([("fingerprint", ASCENDING)], name="idx_dc_fingerprint", unique=True),
            IndexModel([("owner_id", ASCENDING)], name="idx_dc_owner_id"),
            IndexModel([("job_id", ASCENDING)], name="idx_dc_job_id"),
            IndexModel([("quality_tier", ASCENDING)], name="idx_dc_quality_tier"),
            IndexModel([("quality_score", DESCENDING)], name="idx_dc_quality_score"),
            IndexModel([("source_providers", ASCENDING)], name="idx_dc_providers"),
            IndexModel([("enrichment_status", ASCENDING)], name="idx_dc_enrichment_status"),
            IndexModel([("city", ASCENDING), ("state", ASCENDING)], name="idx_dc_location"),
            IndexModel([("company_name", TEXT)], name="idx_dc_text_search"),
            IndexModel([("discovered_at", DESCENDING)], name="idx_dc_discovered_at"),
        ]


# ─── Deduplication Merge Log ────────────────────────────────────────

class DuplicateMergeLogDocument(Document):
    """Tracks every deduplication merge event for audit and UI display."""

    job_id: str
    owner_id: str
    canonical_fingerprint: str = Field(..., description="Fingerprint of the surviving record")
    merged_fingerprints: List[str] = Field(..., description="Fingerprints that were merged in")
    merged_company_names: List[str] = Field(default_factory=list)
    merged_providers: List[str] = Field(default_factory=list)
    match_reasons: List[str] = Field(default_factory=list, description="Why these were considered duplicates")
    confidence: float = Field(..., description="Dedup confidence 0.0-1.0")
    merged_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "duplicate_merge_logs"
        indexes = [
            IndexModel([("job_id", ASCENDING)], name="idx_dml_job_id"),
            IndexModel([("owner_id", ASCENDING)], name="idx_dml_owner_id"),
            IndexModel([("canonical_fingerprint", ASCENDING)], name="idx_dml_fingerprint"),
            IndexModel([("merged_at", DESCENDING)], name="idx_dml_merged_at"),
        ]


# ─── Provider Health Document ────────────────────────────────────────

class DiscoveryProviderHealthDocument(Document):
    """Real-time health tracking per discovery provider."""

    provider: str = Field(..., description="Provider name: google_maps, justdial, indiamart, tradeindia")
    status: str = Field(default="healthy", description="healthy/degraded/down")
    circuit_state: str = Field(default="closed", description="closed/open/half_open")
    failure_count: int = Field(default=0)
    success_count: int = Field(default=0)
    total_requests: int = Field(default=0)
    avg_latency_ms: float = Field(default=0.0)
    last_success_at: Optional[datetime] = None
    last_failure_at: Optional[datetime] = None
    last_error: Optional[str] = None
    leads_discovered_total: int = Field(default=0)
    capabilities: Dict[str, Any] = Field(default_factory=dict)
    checked_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "discovery_provider_health"
        indexes = [
            IndexModel([("provider", ASCENDING)], name="idx_dph_provider", unique=True),
            IndexModel([("status", ASCENDING)], name="idx_dph_status"),
            IndexModel([("checked_at", DESCENDING)], name="idx_dph_checked_at"),
        ]


# ─── Discovery Analytics Document ────────────────────────────────────

class DiscoveryAnalyticsDocument(Document):
    """Daily analytics snapshot for discovery platform performance."""

    date: str = Field(..., description="Date string YYYY-MM-DD")
    owner_id: Optional[str] = Field(None, description="Owner scope (None = global)")

    # Volume metrics
    jobs_started: int = Field(default=0)
    jobs_completed: int = Field(default=0)
    jobs_failed: int = Field(default=0)
    total_discovered: int = Field(default=0)
    total_duplicates_merged: int = Field(default=0)
    total_enriched: int = Field(default=0)

    # Quality metrics
    hot_leads: int = Field(default=0)
    warm_leads: int = Field(default=0)
    cold_leads: int = Field(default=0)
    avg_quality_score: float = Field(default=0.0)

    # Provider metrics (provider_name → metric dict)
    provider_stats: Dict[str, Dict[str, Any]] = Field(default_factory=dict)

    # Performance metrics
    avg_enrichment_time_ms: float = Field(default=0.0)
    avg_job_duration_ms: float = Field(default=0.0)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "discovery_analytics"
        indexes = [
            IndexModel([("date", ASCENDING), ("owner_id", ASCENDING)], name="idx_da_date_owner", unique=True),
            IndexModel([("date", DESCENDING)], name="idx_da_date"),
        ]
