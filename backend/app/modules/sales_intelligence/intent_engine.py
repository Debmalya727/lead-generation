"""
Intent Detection & Opportunity Classification Engine.

Computes multi-signal Buying Intent Score (0-100):
- Intent Levels: Very Low (<30), Low (30-49), Medium (50-69), High (70-84), Very High (85-100)
- Combines:
  1. Growth Signals (hiring, funding, expansion, product launches)
  2. Tech Stack modern updates
  3. Lead Score quality
  4. Company Intelligence confidence
  5. Contact completeness

Classifies companies into opportunity tags:
- Hot Opportunity, Expansion Candidate, Technology Upgrade, Enterprise Target,
  Startup, SMB, High Growth, Recruitment Driven, Cloud Migration Candidate
"""
import logging
from typing import List, Tuple, Dict, Any

from app.database.mongodb.collections.sales_intelligence import GrowthSignal, SalesOpportunityClassification

logger = logging.getLogger("backend.sales_intelligence.intent_engine")


class IntentEngine:
    """Calculates intent score, intent level, and opportunity classification."""

    def compute_intent(
        self,
        lead_score_val: int,
        intel_confidence: int,
        growth_signals: List[GrowthSignal],
        has_email: bool,
        has_phone: bool,
        tech_count: int,
    ) -> Tuple[int, str, str]:
        """
        Compute Buying Intent Score (0-100), Intent Level, and Rationale.
        """
        base_score = 30  # Baseline

        # Signal count weight (max 30 pts)
        signal_weights = {
            "funding": 15,
            "hiring": 12,
            "expansion": 10,
            "product_launch": 8,
            "tech_migration": 8,
            "social": 5,
            "press": 5,
        }
        signal_pts = sum(signal_weights.get(s.type, 5) for s in growth_signals)
        signal_pts = min(35, signal_pts)

        # Lead score weight (max 20 pts)
        lead_score_pts = min(20, round(lead_score_val * 0.2))

        # Intelligence confidence weight (max 10 pts)
        intel_pts = min(10, round(intel_confidence * 0.1))

        # Contactability weight (max 10 pts)
        contact_pts = (5 if has_email else 0) + (5 if has_phone else 0)

        # Tech stack weight (max 5 pts)
        tech_pts = min(5, tech_count * 2)

        total_score = min(100, base_score + signal_pts + lead_score_pts + intel_pts + contact_pts + tech_pts)

        # Determine level
        if total_score >= 85:
            level = "Very High"
        elif total_score >= 70:
            level = "High"
        elif total_score >= 50:
            level = "Medium"
        elif total_score >= 30:
            level = "Low"
        else:
            level = "Very Low"

        # Construct intent rationale
        reasons = []
        if signal_pts > 15:
            reasons.append(f"multiple active growth signals ({len(growth_signals)} detected)")
        if lead_score_val >= 70:
            reasons.append(f"high lead quality score ({lead_score_val}/100)")
        if has_email and has_phone:
            reasons.append("complete verified contact channels")

        if not reasons:
            reasons.append("baseline web domain presence")

        rationale = f"Intent score set to {total_score}/100 ({level}) driven by " + ", ".join(reasons) + "."

        logger.info(f"Computed intent score: {total_score} ({level})")
        return total_score, level, rationale

    def classify_opportunity(
        self,
        company_name: str,
        intent_score: int,
        lead_score_val: int,
        growth_signals: List[GrowthSignal],
        tech_stack: List[Dict[str, str]],
        company_size: str = "",
    ) -> SalesOpportunityClassification:
        """Classify opportunity into category tags."""
        tags = []

        if intent_score >= 75 or lead_score_val >= 75:
            tags.append("Hot Opportunity")

        if any(s.type == "hiring" for s in growth_signals):
            tags.append("Recruitment Driven")

        if any(s.type == "expansion" for s in growth_signals):
            tags.append("Expansion Candidate")

        if any(s.type == "tech_migration" for s in growth_signals) or len(tech_stack) >= 5:
            tags.append("Technology Upgrade")
            tags.append("Cloud Migration Candidate")

        size_lower = (company_size or "").lower()
        if "500" in size_lower or "1000" in size_lower or "enterprise" in size_lower:
            tags.append("Enterprise Target")
        elif "1-10" in size_lower or "startup" in size_lower:
            tags.append("Startup")
        else:
            tags.append("SMB")

        if len(growth_signals) >= 3:
            tags.append("High Growth")

        primary = tags[0] if tags else "SMB"
        rationale = f"Classified '{company_name}' as '{primary}' based on intent score ({intent_score}/100) and signal density."

        return SalesOpportunityClassification(
            categories=tags,
            primary_category=primary,
            rationale=rationale,
        )
