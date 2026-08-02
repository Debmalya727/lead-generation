"""
Canonical Data Models for Lead Normalization.
Provides standardized dataclasses across all discovery providers.
"""
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class NormalizedLead:
    """Canonical lead data representation produced by provider normalization."""
    # Identity
    provider_name: str
    provider_id: Optional[str] = None
    raw_data: Dict[str, Any] = field(default_factory=dict)

    # Core details
    company_name: str = ""
    trade_name: Optional[str] = None
    
    # Contact
    phones: List[str] = field(default_factory=list) # E.164 format
    emails: List[str] = field(default_factory=list)
    website: Optional[str] = None
    website_domain: Optional[str] = None # Strip scheme & www for dedup matching

    # Address
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: str = "IN"
    coordinates: Optional[Dict[str, float]] = None # {"lat": float, "lng": float}

    # Tax & Compliance
    gst: Optional[str] = None
    pan: Optional[str] = None
    cin: Optional[str] = None

    # Categories & Business metadata
    categories: List[str] = field(default_factory=list)
    industry: Optional[str] = None
    products: List[str] = field(default_factory=list)
    business_type: Optional[str] = None

    # Ratings & Proof
    rating: Optional[float] = None
    review_count: Optional[int] = None
    photos: List[str] = field(default_factory=list)
    business_status: Optional[str] = "OPERATIONAL"

    # Additional text
    description: Optional[str] = None
    
    # Provider-calculated quality score initial estimate
    initial_score: int = 50

    # Fingerprint key generated during normalization
    fingerprint: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert normalized lead to standard Python dictionary."""
        return {
            "provider_name": self.provider_name,
            "provider_id": self.provider_id,
            "company_name": self.company_name,
            "trade_name": self.trade_name,
            "phones": self.phones,
            "emails": self.emails,
            "website": self.website,
            "website_domain": self.website_domain,
            "address": self.address,
            "city": self.city,
            "state": self.state,
            "postal_code": self.postal_code,
            "country": self.country,
            "coordinates": self.coordinates,
            "gst": self.gst,
            "pan": self.pan,
            "cin": self.cin,
            "categories": self.categories,
            "industry": self.industry,
            "products": self.products,
            "business_type": self.business_type,
            "rating": self.rating,
            "review_count": self.review_count,
            "photos": self.photos,
            "business_status": self.business_status,
            "description": self.description,
            "initial_score": self.initial_score,
            "fingerprint": self.fingerprint,
        }
