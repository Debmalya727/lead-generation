"""
Feature Extractor for Lead Scoring Engine.

Pulls structured features from Lead document + CompanyIntelligence report
into a typed FeatureVector used by the rule engine and LLM prompt builder.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class FeatureVector:
    """Typed container for all scoring inputs."""

    # Identity
    company_name: str = ""
    website_url: Optional[str] = None

    # Lead contact completeness
    has_website: bool = False
    has_email: bool = False
    has_phone: bool = False
    has_location: bool = False

    # Intelligence-derived features
    has_intelligence: bool = False
    intelligence_confidence: int = 0

    # Company profile
    industry: Optional[str] = None
    company_size_raw: Optional[str] = None      # e.g. "10-50 employees"
    revenue_estimate_raw: Optional[str] = None  # e.g. "$1M-$5M"
    revenue_confidence_raw: Optional[str] = None

    # Sales signals
    buying_signals: List[str] = field(default_factory=list)
    pain_points: List[str] = field(default_factory=list)

    # Tech stack
    tech_stack: List[Dict[str, str]] = field(default_factory=list)

    # Social presence
    social_links: Dict[str, str] = field(default_factory=dict)

    # Key page availability
    has_contact_page: bool = False
    has_careers_page: bool = False
    has_about_page: bool = False

    # Computed helpers
    buying_signals_count: int = 0
    pain_points_count: int = 0
    tech_stack_count: int = 0
    social_count: int = 0
    contact_completeness: int = 0  # 0-3 (website + email + phone)


class ScoringFeatureExtractor:
    """Extracts a FeatureVector from Lead + CompanyIntelligence documents."""

    def extract(self, lead: object, intel_doc: Optional[object]) -> FeatureVector:
        """
        Build a FeatureVector from a Lead document and an optional
        CompanyIntelligence document.

        Args:
            lead: Lead Beanie document
            intel_doc: CompanyIntelligence Beanie document or None
        """
        fv = FeatureVector()

        # ── Lead fields ──────────────────────────────────────────
        fv.company_name = getattr(lead, "name", "") or ""
        fv.website_url = getattr(lead, "website", None)
        fv.has_website = bool(fv.website_url)
        fv.has_email = bool(getattr(lead, "email", None))
        fv.has_phone = bool(getattr(lead, "phone", None))
        fv.has_location = bool(getattr(lead, "location", None))

        # Contact completeness score (max 3)
        fv.contact_completeness = sum([fv.has_website, fv.has_email, fv.has_phone])

        # ── Intelligence fields (if available and completed) ─────
        if intel_doc and getattr(intel_doc, "status", "") == "completed":
            fv.has_intelligence = True
            intel = getattr(intel_doc, "intelligence", None)

            if intel:
                fv.intelligence_confidence = int(getattr(intel, "confidence_score", 0) or 0)
                fv.industry = getattr(intel, "industry", None)
                fv.company_size_raw = getattr(intel, "company_size", None)
                fv.revenue_estimate_raw = getattr(intel, "revenue_estimate", None)
                fv.revenue_confidence_raw = getattr(intel, "revenue_confidence", None)
                fv.buying_signals = list(getattr(intel, "buying_signals", []) or [])
                fv.pain_points = list(getattr(intel, "pain_points", []) or [])

            fv.tech_stack = [
                {"name": t.name, "category": t.category}
                for t in (getattr(intel_doc, "tech_stack", []) or [])
            ]
            fv.social_links = dict(getattr(intel_doc, "social_links", {}) or {})
            fv.has_contact_page = bool(getattr(intel_doc, "contact_page", None))
            fv.has_careers_page = bool(getattr(intel_doc, "careers_page", None))
            fv.has_about_page = bool(getattr(intel_doc, "about_page", None))

        # Derived counts
        fv.buying_signals_count = len(fv.buying_signals)
        fv.pain_points_count = len(fv.pain_points)
        fv.tech_stack_count = len(fv.tech_stack)
        fv.social_count = len(fv.social_links)

        return fv
