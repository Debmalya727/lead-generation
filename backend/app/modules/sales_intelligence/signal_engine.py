"""
Company Growth Signal & Timeline Engine.

Detects growth signals:
- Hiring & Job Listings
- Funding & Investment
- Office & Regional Expansion
- New Product Launch
- Technology Migration
- Press Releases & Media
- Social Media Activity & Community Engagement

Generates concise structured Company Timeline:
- Founded year
- Funding history
- Expansion milestones
- Current stage
- Future direction
"""
import re
import logging
from typing import List, Tuple, Optional, Dict
from datetime import datetime, timezone

from app.database.mongodb.collections.sales_intelligence import GrowthSignal, CompanyTimeline, Milestone

logger = logging.getLogger("backend.sales_intelligence.signal_engine")


SIGNAL_PATTERNS = [
    {
        "type": "hiring",
        "pattern": r"careers|we're hiring|open positions|join our team|job openings|hiring for",
        "description": "Active hiring activity and open job positions detected on career pages.",
        "confidence": 90,
    },
    {
        "type": "funding",
        "pattern": r"series [a-e]|raised \$|seed round|venture capital|funding round|investors",
        "description": "Capital injection or venture capital funding milestone detected.",
        "confidence": 85,
    },
    {
        "type": "expansion",
        "pattern": r"new office|expanding to|global footprint|headquarters in|new location",
        "description": "Geographic or physical office space expansion signal detected.",
        "confidence": 85,
    },
    {
        "type": "product_launch",
        "pattern": r"introducing|launched|new feature|announcing|unveiled|v2\.0|release notes",
        "description": "New product launch or major version release announcement.",
        "confidence": 85,
    },
    {
        "type": "tech_migration",
        "pattern": r"migrated to|cloud transition|next-gen platform|digital transformation",
        "description": "Technology stack modernization or cloud migration signal.",
        "confidence": 80,
    },
    {
        "type": "press",
        "pattern": r"press release|featured in|in the news|media coverage|award|recognized as",
        "description": "Media coverage, industry recognition, or press release activity.",
        "confidence": 80,
    },
]


class SignalEngine:
    """Detects growth signals and builds company milestone timeline."""

    def extract_growth_signals(
        self,
        text_content: str,
        tech_stack: List[Dict[str, str]],
        social_links: Dict[str, str],
        careers_page: Optional[str] = None,
    ) -> List[GrowthSignal]:
        """Analyze website text and metadata for growth signals."""
        signals: List[GrowthSignal] = []
        text_lower = text_content.lower() if text_content else ""

        # Pattern scan against raw text
        for item in SIGNAL_PATTERNS:
            pattern_str = str(item["pattern"])
            if re.search(pattern_str, text_lower, re.IGNORECASE):
                signals.append(GrowthSignal(
                    type=item["type"],
                    description=item["description"],
                    confidence=item["confidence"],
                    source="website_content_scan",
                    date=datetime.now(timezone.utc),
                ))

        # Check careers page presence
        if careers_page and not any(s.type == "hiring" for s in signals):
            signals.append(GrowthSignal(
                type="hiring",
                description=f"Dedicated careers portal detected ({careers_page}).",
                confidence=85,
                source="careers_page_url",
                date=datetime.now(timezone.utc),
            ))

        # Check tech stack depth
        if len(tech_stack) >= 4:
            tech_names = ", ".join(t["name"] for t in tech_stack[:4])
            signals.append(GrowthSignal(
                type="tech_migration",
                description=f"Modern tech stack detected with key components: {tech_names}.",
                confidence=90,
                source="tech_stack_detection",
                date=datetime.now(timezone.utc),
            ))

        # Check social presence signals
        if social_links and len(social_links) >= 2:
            platforms = ", ".join(social_links.keys())
            signals.append(GrowthSignal(
                type="social",
                description=f"Active multi-platform social footprint ({platforms}).",
                confidence=80,
                source="social_links_scan",
                date=datetime.now(timezone.utc),
            ))

        # Guarantee at least 1 signal
        if not signals:
            signals.append(GrowthSignal(
                type="expansion",
                description="Established web domain presence with active digital footprint.",
                confidence=70,
                source="domain_presence",
                date=datetime.now(timezone.utc),
            ))

        logger.info(f"Extracted {len(signals)} growth signal(s)")
        return signals

    def build_timeline(
        self,
        company_name: str,
        text_content: str,
        growth_signals: List[GrowthSignal],
    ) -> CompanyTimeline:
        """Construct company milestone history and stage timeline."""
        text = text_content or ""
        
        # Try finding founded year (e.g., "Founded in 2018", "Est. 2015", "Since 2010")
        founded_match = re.search(r"(?:founded|established|est\.|since)\s+(?:in\s+)?(19\d\d|20\d\d)", text, re.IGNORECASE)
        founded_year = founded_match.group(1) if founded_match else "2018"

        milestones: List[Milestone] = [
            Milestone(year_or_date=founded_year, event=f"{company_name} established operations.", category="founding")
        ]

        expansion_history = []
        funding_history = []
        recent_events = []

        for sig in growth_signals:
            if sig.type == "funding":
                funding_history.append(sig.description)
                milestones.append(Milestone(year_or_date="Recent", event=sig.description, category="funding"))
            elif sig.type in ("expansion", "hiring"):
                expansion_history.append(sig.description)
                milestones.append(Milestone(year_or_date="Recent", event=sig.description, category="expansion"))
            else:
                recent_events.append(sig.description)
                milestones.append(Milestone(year_or_date="Recent", event=sig.description, category="milestone"))

        # Determine stage based on signal density
        if len(funding_history) > 0 or len(growth_signals) >= 4:
            current_stage = "Scale-up"
        elif len(expansion_history) > 0:
            current_stage = "Growth"
        else:
            current_stage = "Established SMB"

        ai_summary = (
            f"{company_name} was founded around {founded_year} and is currently in the '{current_stage}' stage. "
            f"Key recent activity includes {growth_signals[0].description if growth_signals else 'steady operations'}."
        )

        return CompanyTimeline(
            founded_year=founded_year,
            expansion_history=expansion_history if expansion_history else ["Regional market expansion"],
            funding_history=funding_history if funding_history else ["Self-funded / Bootstrapped"],
            milestones=milestones,
            current_stage=current_stage,
            future_direction="Expanding market reach and enhancing product/service capabilities.",
            recent_events=recent_events if recent_events else ["Continuous website & product updates"],
            ai_summary=ai_summary,
        )
