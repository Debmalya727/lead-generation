"""
AI Deduplication Engine for Enterprise Lead Discovery.
Merges records of the same business appearing across multiple discovery providers
(Google Maps, Justdial, IndiaMART, TradeIndia) into unified canonical records.
"""
import re
import logging
from typing import List, Dict, Any, Tuple, Optional
from app.modules.discovery.normalization.models import NormalizedLead

logger = logging.getLogger("backend.discovery.deduplication")


class DeduplicationResult:
    """Result of multi-provider lead deduplication."""
    def __init__(self, canonical_leads: List[Dict[str, Any]], merge_logs: List[Dict[str, Any]]):
        self.canonical_leads = canonical_leads
        self.merge_logs = merge_logs
        self.total_raw = sum(len(l.get("sources", [])) for l in canonical_leads)
        self.total_unified = len(canonical_leads)
        self.merged_count = self.total_raw - self.total_unified


class AIDeduplicationEngine:
    """Fuzzy matching deduplication engine across multi-provider lead sources."""

    def __init__(self, name_similarity_threshold: float = 0.82):
        self.name_similarity_threshold = name_similarity_threshold

    def calculate_string_similarity(self, s1: str, s2: str) -> float:
        """Calculate normalized similarity ratio between two strings (0.0 to 1.0)."""
        str1 = re.sub(r"[^a-z0-9]", "", s1.lower().strip())
        str2 = re.sub(r"[^a-z0-9]", "", s2.lower().strip())
        
        if not str1 or not str2:
            return 0.0
        if str1 == str2:
            return 1.0
        if str1 in str2 or str2 in str1:
            len_ratio = min(len(str1), len(str2)) / max(len(str1), len(str2))
            return max(0.80, len_ratio)

        # Bigram Dice coefficient similarity calculation
        bigrams1 = set(str1[i:i+2] for i in range(len(str1)-1))
        bigrams2 = set(str2[i:i+2] for i in range(len(str2)-1))
        if not bigrams1 or not bigrams2:
            return 0.0

        intersection = len(bigrams1.intersection(bigrams2))
        total = len(bigrams1) + len(bigrams2)
        return (2.0 * intersection) / total

    def evaluate_match(self, lead1: NormalizedLead, lead2: NormalizedLead) -> Tuple[bool, float, List[str]]:
        """
        Evaluate if two normalized leads represent the same business.
        Returns: (is_match: bool, confidence: float, match_reasons: List[str])
        """
        reasons = []
        confidence = 0.0

        # Rule 1: Exact GST match (Highest confidence in India B2B)
        if lead1.gst and lead2.gst and lead1.gst == lead2.gst:
            reasons.append(f"Exact GSTIN Match ({lead1.gst})")
            return True, 1.0, reasons

        # Rule 2: Exact domain match + name similarity
        domain1 = lead1.website_domain
        domain2 = lead2.website_domain
        name_sim = self.calculate_string_similarity(lead1.company_name, lead2.company_name)

        if domain1 and domain2 and domain1 == domain2:
            reasons.append(f"Exact Website Domain Match ({domain1})")
            if name_sim >= 0.5:
                reasons.append(f"Name Similarity ({round(name_sim*100)}%)")
                return True, min(0.95 + (name_sim * 0.05), 1.0), reasons
            return True, 0.90, reasons

        # Rule 3: Exact phone match + name similarity
        phones1 = set(lead1.phones)
        phones2 = set(lead2.phones)
        common_phones = phones1.intersection(phones2)
        if common_phones:
            reasons.append(f"Matching Phone Number ({list(common_phones)[0]})")
            if name_sim >= 0.60:
                reasons.append(f"Name Similarity ({round(name_sim*100)}%)")
                return True, min(0.85 + (name_sim * 0.15), 1.0), reasons

        # Rule 4: High name similarity + same city
        if name_sim >= self.name_similarity_threshold:
            city1 = (lead1.city or "").lower().strip()
            city2 = (lead2.city or "").lower().strip()
            if city1 and city2 and city1 == city2:
                reasons.append(f"High Name Similarity ({round(name_sim*100)}%) in same city ({lead1.city})")
                return True, round(name_sim, 2), reasons

        return False, 0.0, []

    def deduplicate(self, raw_normalized_leads: List[NormalizedLead]) -> DeduplicationResult:
        """
        Deduplicate a list of NormalizedLead records into unified canonical lead records.
        """
        canonical_records: List[Dict[str, Any]] = []
        merge_logs: List[Dict[str, Any]] = []
        visited = [False] * len(raw_normalized_leads)

        for i in range(len(raw_normalized_leads)):
            if visited[i]:
                continue
            
            base = raw_normalized_leads[i]
            cluster = [base]
            visited[i] = True
            merge_reasons_cluster = []
            max_confidence = 1.0

            for j in range(i + 1, len(raw_normalized_leads)):
                if visited[j]:
                    continue
                candidate = raw_normalized_leads[j]
                
                is_match, conf, reasons = self.evaluate_match(base, candidate)
                if is_match:
                    visited[j] = True
                    cluster.append(candidate)
                    merge_reasons_cluster.extend(reasons)
                    max_confidence = max(max_confidence, conf)

            # Merge cluster into single canonical record dict
            merged_dict = self._merge_cluster(cluster)
            canonical_records.append(merged_dict)

            if len(cluster) > 1:
                merge_logs.append({
                    "canonical_fingerprint": merged_dict["fingerprint"],
                    "merged_fingerprints": [c.fingerprint for c in cluster],
                    "merged_company_names": [c.company_name for c in cluster],
                    "merged_providers": [c.provider_name for c in cluster],
                    "match_reasons": list(set(merge_reasons_cluster)),
                    "confidence": max_confidence,
                })

        logger.info(f"[DeduplicationEngine] Reduced {len(raw_normalized_leads)} raw leads to {len(canonical_records)} canonical leads (Merged: {len(raw_normalized_leads) - len(canonical_records)})")
        return DeduplicationResult(canonical_records, merge_logs)

    def _merge_cluster(self, cluster: List[NormalizedLead]) -> Dict[str, Any]:
        """Combine multiple matched leads into a single canonical dictionary representation."""
        # Pick primary record with highest initial score / richest data
        primary = max(cluster, key=lambda l: (l.initial_score, len(l.website or ""), len(l.phones)))

        all_phones = []
        all_emails = []
        all_categories = []
        all_products = []
        all_photos = []
        sources = []
        provider_names = []

        for item in cluster:
            if item.provider_name not in provider_names:
                provider_names.append(item.provider_name)
            
            sources.append({
                "provider": item.provider_name,
                "provider_id": item.provider_id,
                "raw_name": item.company_name,
                "raw_phone": item.phones[0] if item.phones else None,
                "raw_address": item.address,
                "confidence": 1.0,
            })

            for p in item.phones:
                if p not in all_phones:
                    all_phones.append(p)

            for e in item.emails:
                if e not in all_emails:
                    all_emails.append(e)

            for c in item.categories:
                if c not in all_categories:
                    all_categories.append(c)

            for pr in item.products:
                if pr not in all_products:
                    all_products.append(pr)

            for ph in item.photos:
                if ph not in all_photos:
                    all_photos.append(ph)

        # Merge website (prefer https)
        best_website = primary.website
        if not best_website:
            for item in cluster:
                if item.website:
                    best_website = item.website
                    break

        # Merge GST
        best_gst = primary.gst
        if not best_gst:
            for item in cluster:
                if item.gst:
                    best_gst = item.gst
                    break

        return {
            "company_name": primary.company_name,
            "trade_name": primary.trade_name,
            "fingerprint": primary.fingerprint,
            "is_merged": len(cluster) > 1,
            "merged_from": [item.fingerprint for item in cluster if item.fingerprint != primary.fingerprint],
            "phones": all_phones,
            "emails": all_emails,
            "website": best_website,
            "website_domain": primary.website_domain,
            "address": primary.address,
            "city": primary.city,
            "state": primary.state,
            "postal_code": primary.postal_code,
            "country": primary.country,
            "coordinates": primary.coordinates,
            "gst": best_gst,
            "categories": all_categories,
            "products": all_products,
            "business_type": primary.business_type or "Business Lead",
            "rating": primary.rating,
            "review_count": primary.review_count,
            "photos": all_photos,
            "description": primary.description,
            "sources": sources,
            "source_providers": provider_names,
            "initial_score": max(item.initial_score for item in cluster),
        }


deduplication_engine = AIDeduplicationEngine()
