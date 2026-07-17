"""
Rule Engine for Lead Scoring.

Computes a deterministic weighted score (0-100) from a FeatureVector.
Each rule contributes a sub-score with a one-line rationale.

Scoring profile "general_b2b" weights:
  buying_signals      → 20 pts
  pain_points         → 10 pts
  tech_stack          → 10 pts
  company_size        → 10 pts
  revenue_estimate    → 10 pts
  contact_complete    → 15 pts (website=5, email=5, phone=5)
  social_presence     → 10 pts
  intelligence_quality→ 10 pts
  key_pages           →  5 pts
  ─────────────────────────
  TOTAL               → 100 pts
"""
import logging
import re
from typing import List, Tuple

from app.modules.scoring.feature_extractor import FeatureVector

logger = logging.getLogger("backend.scoring.rule_engine")


# Maps company size keywords → mid-market relevance score multiplier
_SIZE_SCORES = {
    "1-10": 3,
    "10-50": 7,
    "50-200": 10,
    "200-500": 9,
    "500-1000": 7,
    "1000+": 5,
}

# Maps revenue keywords → score
_REVENUE_SCORES = {
    "under $1m": 3,
    "$1m": 6,
    "$5m": 9,
    "$10m": 10,
    "$50m": 9,
    "$100m": 7,
    "$500m": 5,
    "$1b": 3,
}


def _parse_size_score(size_raw: str) -> Tuple[int, str]:
    """Map company size string to a score."""
    if not size_raw:
        return 0, "No company size data available."
    lower = size_raw.lower()
    for key, pts in _SIZE_SCORES.items():
        if key.replace("-", " ") in lower or key in lower:
            return pts, f"Company size '{size_raw}' maps to {pts}/10 for B2B relevance."
    # fallback: mid-range assumption
    return 5, f"Company size '{size_raw}' — assumed mid-range."


def _parse_revenue_score(rev_raw: str, confidence: str) -> Tuple[int, str]:
    """Map revenue estimate to a score, adjusted by confidence level."""
    if not rev_raw:
        return 0, "No revenue estimate available."
    lower = rev_raw.lower().replace(",", "")
    base = 0
    for key, pts in _REVENUE_SCORES.items():
        if key in lower:
            base = pts
            break
    if base == 0:
        # Try to find any dollar amount
        match = re.search(r"\$(\d+)", lower)
        if match:
            amt = int(match.group(1))
            if amt < 1:
                base = 3
            elif amt < 10:
                base = 8
            else:
                base = 6
        else:
            base = 4

    # Confidence multiplier
    conf_lower = (confidence or "").lower()
    if conf_lower == "high":
        multiplier = 1.0
    elif conf_lower == "medium":
        multiplier = 0.75
    else:
        multiplier = 0.5

    final = min(10, round(base * multiplier))
    return final, f"Revenue '{rev_raw}' ({confidence} confidence) → {final}/10."


class ScoreBreakdownEntry:
    """Internal result from a single rule computation."""
    def __init__(self, feature: str, label: str, score: int, max_score: int, rationale: str):
        self.feature = feature
        self.label = label
        self.score = score
        self.max_score = max_score
        self.rationale = rationale

    def to_dict(self) -> dict:
        return {
            "feature": self.feature,
            "label": self.label,
            "score": self.score,
            "max_score": self.max_score,
            "rationale": self.rationale,
        }


class RuleEngine:
    """
    Deterministic weighted scoring engine for general B2B lead scoring.
    Returns total score (0-100) and per-feature breakdown.
    """

    def compute(self, fv: FeatureVector) -> Tuple[int, List[ScoreBreakdownEntry]]:
        """
        Run all rules against the FeatureVector.

        Returns:
            (total_score, breakdown_list)
        """
        breakdown: List[ScoreBreakdownEntry] = []
        total = 0

        # ── Rule 1: Buying Signals (max 20) ─────────────────────
        sig_count = fv.buying_signals_count
        sig_score = min(20, sig_count * 5)
        if sig_count == 0:
            sig_rationale = "No buying signals detected. Lead may not be actively seeking vendors."
        elif sig_count == 1:
            sig_rationale = f"1 buying signal detected — low intent indicator."
        else:
            sig_rationale = f"{sig_count} buying signals detected — strong purchase intent."
        breakdown.append(ScoreBreakdownEntry(
            "buying_signals", "Buying Signals", sig_score, 20, sig_rationale
        ))
        total += sig_score

        # ── Rule 2: Pain Points (max 10) ─────────────────────────
        pp_count = fv.pain_points_count
        pp_score = min(10, pp_count * 3)
        if pp_count == 0:
            pp_rationale = "No pain points identified — harder to position your solution."
        else:
            pp_rationale = f"{pp_count} pain point(s) identified — {pp_score}/10 potential fit."
        breakdown.append(ScoreBreakdownEntry(
            "pain_points", "Pain Points", pp_score, 10, pp_rationale
        ))
        total += pp_score

        # ── Rule 3: Tech Stack (max 10) ──────────────────────────
        ts_count = fv.tech_stack_count
        ts_score = min(10, ts_count * 2)
        ts_rationale = (
            f"Tech stack has {ts_count} detected technologies — {ts_score}/10."
            if ts_count > 0 else
            "No technology signals detected — website may be minimal or static."
        )
        breakdown.append(ScoreBreakdownEntry(
            "tech_stack", "Technology Stack", ts_score, 10, ts_rationale
        ))
        total += ts_score

        # ── Rule 4: Company Size (max 10) ────────────────────────
        size_score, size_rationale = _parse_size_score(fv.company_size_raw)
        breakdown.append(ScoreBreakdownEntry(
            "company_size", "Company Size", size_score, 10, size_rationale
        ))
        total += size_score

        # ── Rule 5: Revenue Estimate (max 10) ────────────────────
        rev_score, rev_rationale = _parse_revenue_score(
            fv.revenue_estimate_raw or "",
            fv.revenue_confidence_raw or "low"
        )
        breakdown.append(ScoreBreakdownEntry(
            "revenue_estimate", "Revenue Estimate", rev_score, 10, rev_rationale
        ))
        total += rev_score

        # ── Rule 6: Contact Completeness (max 15) ────────────────
        cc = fv.contact_completeness
        cc_website = 5 if fv.has_website else 0
        cc_email = 5 if fv.has_email else 0
        cc_phone = 5 if fv.has_phone else 0
        cc_score = cc_website + cc_email + cc_phone
        cc_parts = []
        if fv.has_website:
            cc_parts.append("website ✓")
        if fv.has_email:
            cc_parts.append("email ✓")
        if fv.has_phone:
            cc_parts.append("phone ✓")
        cc_rationale = (
            f"Contact data: {', '.join(cc_parts) if cc_parts else 'none'} → {cc_score}/15."
        )
        breakdown.append(ScoreBreakdownEntry(
            "contact_completeness", "Contact Completeness", cc_score, 15, cc_rationale
        ))
        total += cc_score

        # ── Rule 7: Social Presence (max 10) ─────────────────────
        sc_count = fv.social_count
        sc_score = min(10, sc_count * 3)
        sc_rationale = (
            f"{sc_count} social profile(s) found (LinkedIn, Twitter, etc.) → {sc_score}/10."
            if sc_count > 0 else
            "No social media presence detected."
        )
        breakdown.append(ScoreBreakdownEntry(
            "social_presence", "Social Presence", sc_score, 10, sc_rationale
        ))
        total += sc_score

        # ── Rule 8: Intelligence Quality (max 10) ────────────────
        if not fv.has_intelligence:
            iq_score = 0
            iq_rationale = "No Company Intelligence report available. Run Intelligence analysis first."
        else:
            iq_score = round(fv.intelligence_confidence / 10)
            iq_rationale = f"Intelligence confidence: {fv.intelligence_confidence}/100 → {iq_score}/10."
        breakdown.append(ScoreBreakdownEntry(
            "intelligence_quality", "Intelligence Quality", iq_score, 10, iq_rationale
        ))
        total += iq_score

        # ── Rule 9: Key Pages (max 5) ────────────────────────────
        kp_score = sum([
            2 if fv.has_contact_page else 0,
            2 if fv.has_about_page else 0,
            1 if fv.has_careers_page else 0,
        ])
        kp_parts = []
        if fv.has_contact_page:
            kp_parts.append("contact")
        if fv.has_about_page:
            kp_parts.append("about")
        if fv.has_careers_page:
            kp_parts.append("careers")
        kp_rationale = (
            f"Key pages found: {', '.join(kp_parts)} → {kp_score}/5."
            if kp_parts else
            "No key pages (contact/about/careers) detected."
        )
        breakdown.append(ScoreBreakdownEntry(
            "key_pages", "Key Pages", kp_score, 5, kp_rationale
        ))
        total += kp_score

        final_score = min(100, total)
        logger.debug(f"Rule engine total for '{fv.company_name}': {final_score}/100")
        return final_score, breakdown
