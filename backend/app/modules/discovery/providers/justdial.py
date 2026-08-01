import logging
from typing import List
from app.modules.discovery.providers.base_provider import BaseDiscoveryProvider
from app.modules.discovery.providers.search_helper import fetch_real_directory_leads

logger = logging.getLogger(__name__)


class JustDialProvider(BaseDiscoveryProvider):
    def __init__(self):
        super().__init__("justdial")

    async def discover(self, keyword: str, location: str, limit: int = 20, website_filter: str = "all", **kwargs) -> List[dict]:
        """JustDial provider extracting real live local directory listings."""
        clean_keyword = keyword.strip()
        clean_location = location.strip()
        logger.info(f"Extracting real JustDial directory leads for '{clean_keyword}' in '{clean_location}'")
        
        return fetch_real_directory_leads(
            clean_keyword,
            clean_location,
            self.provider_name,
            limit=limit,
            website_filter=website_filter
        )
