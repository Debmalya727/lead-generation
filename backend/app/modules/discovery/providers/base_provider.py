"""
Enterprise Discovery Provider Base Interface.
All lead discovery providers (Google Maps, Justdial, IndiaMART, TradeIndia, etc.)
must inherit from BaseDiscoveryProvider and implement all interface methods.
"""
import time
import logging
from typing import List, Dict, Any, Optional
from app.modules.discovery.normalization.models import NormalizedLead
from app.modules.discovery.normalization.lead_normalizer import lead_normalizer
from app.modules.discovery.providers.circuit_breaker import CircuitBreaker

logger = logging.getLogger("backend.discovery.base_provider")


class BaseDiscoveryProvider:
    """Enterprise Common Provider Interface."""

    def __init__(self, provider_name: str, requests_per_minute: int = 60):
        self.provider_name = provider_name.lower().strip()
        self.requests_per_minute = requests_per_minute
        self.circuit_breaker = CircuitBreaker(provider_name=self.provider_name)

    async def search(self, keyword: str, location: str, limit: int = 20, website_filter: str = "all", **kwargs) -> List[NormalizedLead]:
        """
        Primary search method querying provider for business leads matching keyword and location.
        Must return normalized canonical NormalizedLead instances.
        """
        raise NotImplementedError(f"Provider {self.provider_name} must implement search()")

    async def get_business(self, business_id: str) -> Optional[NormalizedLead]:
        """Fetch detailed information for a specific business by provider ID."""
        raise NotImplementedError(f"Provider {self.provider_name} must implement get_business()")

    async def get_contact_information(self, business_id: str) -> Dict[str, Any]:
        """Extract public contact details (phones, emails, social profiles) for a business."""
        business = await self.get_business(business_id)
        if not business:
            return {"phones": [], "emails": [], "website": None}
        return {
            "phones": business.phones,
            "emails": business.emails,
            "website": business.website,
        }

    def normalize(self, raw_data: Dict[str, Any]) -> NormalizedLead:
        """Normalize raw provider record to canonical NormalizedLead model."""
        return lead_normalizer.normalize_raw_lead(raw_data, self.provider_name)

    def health(self) -> Dict[str, Any]:
        """Return real-time provider health metrics and circuit state."""
        status_dict = self.circuit_breaker.get_status_dict()
        circuit_state = status_dict["circuit_state"]
        
        status = "healthy"
        if circuit_state == "open":
            status = "down"
        elif circuit_state == "half_open" or status_dict["failure_count"] > 0:
            status = "degraded"

        return {
            "provider": self.provider_name,
            "status": status,
            "circuit_state": circuit_state,
            "requests_per_minute_quota": self.requests_per_minute,
            "total_requests": status_dict["total_requests"],
            "success_count": status_dict["success_count"],
            "failure_count": status_dict["failure_count"],
            "avg_latency_ms": status_dict["avg_latency_ms"],
            "last_error": status_dict["last_error"],
            "capabilities": self.capabilities(),
        }

    def capabilities(self) -> Dict[str, Any]:
        """Expose capabilities supported by this provider."""
        return {
            "keyword_search": True,
            "location_search": True,
            "radius_search": False,
            "polygon_search": False,
            "coordinate_search": False,
            "gst_extraction": False,
            "product_search": False,
            "pagination": True,
            "contact_extraction": True,
            "review_extraction": False,
        }

    async def discover(self, keyword: str, location: str, limit: int = 20, website_filter: str = "all", **kwargs) -> List[Dict[str, Any]]:
        """
        Backward compatible entrypoint wrapper returning dictionary representations.
        Executes circuit breaker check and updates metrics.
        """
        if not self.circuit_breaker.allow_request():
            logger.warning(f"Circuit Breaker for '{self.provider_name}' is OPEN. Aborting search request.")
            return []

        start_time = time.time()
        try:
            normalized_leads = await self.search(keyword, location, limit=limit, website_filter=website_filter, **kwargs)
            latency_ms = (time.time() - start_time) * 1000.0
            self.circuit_breaker.record_success(latency_ms)
            
            # Convert to dictionary representation for backward compatibility
            results = []
            for lead in normalized_leads:
                d = lead.to_dict()
                # Ensure legacy dict format keys exist
                d["name"] = lead.company_name
                d["phone"] = lead.phones[0] if lead.phones else ""
                d["email"] = lead.emails[0] if lead.emails else ""
                d["location"] = f"{lead.city or location}, {lead.country}"
                d["score"] = lead.initial_score
                d["provider"] = self.provider_name
                results.append(d)
            return results

        except Exception as e:
            logger.error(f"Error executing provider '{self.provider_name}': {str(e)}")
            self.circuit_breaker.record_failure(e)
            raise e
