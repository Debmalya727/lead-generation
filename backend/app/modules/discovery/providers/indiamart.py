import asyncio
import random
from typing import List
from app.modules.discovery.providers.base_provider import BaseDiscoveryProvider


class IndiaMARTProvider(BaseDiscoveryProvider):
    def __init__(self):
        super().__init__("indiamart")

    async def discover(self, keyword: str, location: str, limit: int = 20) -> List[dict]:
        """IndiaMART provider simulation yielding wholesale manufacturers & suppliers."""
        # IndiaMART scrapers typically take a bit longer due to anti-bot measures
        await asyncio.sleep(random.uniform(1.2, 2.2))
        
        clean_keyword = keyword.strip()
        clean_location = location.strip()
        
        results = []
        name_modifiers = ["Industries", "Manufacturers", "Exports", "Fabricators", "Corporation", "Mills", "Metals", "Wholesale"]
        
        for i in range(1, limit + 1):
            modifier = name_modifiers[(i - 1) % len(name_modifiers)]
            name = f"{clean_location} {clean_keyword} {modifier}"
            domain = f"{clean_keyword.lower().replace(' ', '')}mfg-{clean_location.lower()}.com"
            
            phone = f"+91-88888-{i:05d}"
            
            results.append({
                "name": name,
                "website": f"https://www.{domain}",
                "phone": phone,
                "email": f"export@{domain}",
                "location": f"{clean_location}, India",
                "score": random.randint(70, 95),
                "provider": self.provider_name
            })
            
        return results
