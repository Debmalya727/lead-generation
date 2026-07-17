import asyncio
import random
from typing import List
from app.modules.discovery.providers.base_provider import BaseDiscoveryProvider


class GoogleMapsProvider(BaseDiscoveryProvider):
    def __init__(self):
        super().__init__("google_maps")

    async def discover(self, keyword: str, location: str, limit: int = 20) -> List[dict]:
        """Google Maps provider simulation yielding rich local directory businesses."""
        # Simulate scraping delay and rate limits
        await asyncio.sleep(random.uniform(0.8, 1.5))
        
        # Clean inputs
        clean_keyword = keyword.strip()
        clean_location = location.strip()
        
        results = []
        name_modifiers = ["Pro", "Elite", "Solutions", "Experts", "Group", "Services", "Partners", "Hub"]
        
        for i in range(1, limit + 1):
            modifier = name_modifiers[(i - 1) % len(name_modifiers)]
            name = f"{clean_location} {clean_keyword} {modifier}"
            domain = f"{name.lower().replace(' ', '')}.com"
            
            # Formulate realistic phone formats
            area_code = random.randint(200, 999)
            phone = f"+1-{area_code}-555-{i:04d}"
            
            results.append({
                "name": name,
                "website": f"https://www.{domain}",
                "phone": phone,
                "email": f"info@{domain}",
                "location": f"{clean_location}, USA",
                "score": random.randint(65, 98),
                "provider": self.provider_name
            })
            
        return results
