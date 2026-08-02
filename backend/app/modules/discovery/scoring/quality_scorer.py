"""
Lead Quality Scoring Engine for Enterprise Lead Discovery Platform.
Calculates multi-factor quality scores (0-100) and assigns Hot/Warm/Cold tiers.
"""
import logging
from typing import Dict, Any, Tuple

logger = logging.getLogger("backend.discovery.scoring")


class LeadQualityScorer:
    """Multi-factor lead quality scoring and tier assignment."""

    def calculate_quality_score(self, lead_data: Dict[str, Any]) -> Tuple[int, str, Dict[str, int]]:
        """
        Calculate total score (0-100), quality tier (Hot/Warm/Cold), and component breakdown dict.
        """
        breakdown = {
            "website_quality": self._score_website(lead_data.get("website")),
            "contact_completeness": self._score_contact_completeness(lead_data.get("phones", []), lead_data.get("emails", []), lead_data.get("address")),
            "review_social_proof": self._score_reviews(lead_data.get("rating"), lead_data.get("review_count")),
            "business_maturity": self._score_maturity(lead_data.get("business_maturity"), lead_data.get("gst")),
            "social_activity": self._score_social(lead_data.get("social_profiles")),
            "tech_stack": self._score_tech(lead_data.get("tech_stack")),
            "ai_confidence": self._score_ai_confidence(lead_data.get("buyer_intent")),
        }

        total_score = min(100, max(0, sum(breakdown.values())))

        if total_score >= 70:
            tier = "Hot"
        elif total_score >= 40:
            tier = "Warm"
        else:
            tier = "Cold"

        return total_score, tier, breakdown

    def _score_website(self, website: Any) -> int:
        if not website:
            return 0
        web_str = str(website).lower()
        score = 10
        if web_str.startswith("https"):
            score += 5
        if ".com" in web_str or ".in" in web_str or ".co" in web_str:
            score += 5
        return score

    def _score_contact_completeness(self, phones: list, emails: list, address: Any) -> int:
        score = 0
        if phones:
            score += 8
        if emails:
            score += 8
        if address:
            score += 4
        return score

    def _score_reviews(self, rating: Any, review_count: Any) -> int:
        if not rating and not review_count:
            return 8 # Default neutral score
        score = 0
        r = float(rating or 0.0)
        rc = int(review_count or 0)

        if r >= 4.5:
            score += 10
        elif r >= 4.0:
            score += 7
        elif r >= 3.5:
            score += 4

        if rc > 100:
            score += 10
        elif rc > 20:
            score += 6
        elif rc > 0:
            score += 3
        return score

    def _score_maturity(self, maturity: Any, gst: Any) -> int:
        score = 5
        if gst:
            score += 5 # GST compliance is a strong B2B verification signal
        mat_str = str(maturity or "").lower()
        if "enterprise" in mat_str:
            score += 5
        elif "established" in mat_str:
            score += 3
        return score

    def _score_social(self, social: Any) -> int:
        if not social or not isinstance(social, dict):
            return 4
        count = sum(1 for v in social.values() if v)
        return min(10, count * 2)

    def _score_tech(self, tech: Any) -> int:
        if not tech or not isinstance(tech, dict):
            return 4
        score = 4
        if tech.get("ssl"):
            score += 2
        if tech.get("ecommerce") or tech.get("cms"):
            score += 2
        if tech.get("frameworks"):
            score += 2
        return min(10, score)

    def _score_ai_confidence(self, buyer_intent: Any) -> int:
        intent_str = str(buyer_intent or "").lower()
        if intent_str == "high":
            return 5
        elif intent_str == "medium":
            return 3
        return 1


lead_quality_scorer = LeadQualityScorer()
