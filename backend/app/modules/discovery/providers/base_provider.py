from typing import List


class BaseDiscoveryProvider:
    def __init__(self, provider_name: str):
        self.provider_name = provider_name

    async def discover(self, keyword: str, location: str, limit: int = 20) -> List[dict]:
        """Perform discovery search for business leads matching keyword and location."""
        raise NotImplementedError("Scraper provider discover method must be implemented.")
