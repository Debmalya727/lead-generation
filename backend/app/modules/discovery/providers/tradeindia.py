import asyncio
import random
from typing import List
from app.modules.discovery.providers.base_provider import BaseDiscoveryProvider


class TradeIndiaProvider(BaseDiscoveryProvider):
    def __init__(self):
        super().__init__("tradeindia")

    async def discover(self, keyword: str, location: str, limit: int = 20) -> List[dict]:
        """TradeIndia provider simulation yielding commercial exporters & wholesale traders."""
        await asyncio.sleep(random.uniform(0.7, 1.8))
        
        clean_keyword = keyword.strip()
        clean_location = location.strip()
        
        results = []
        name_modifiers = ["Traders", "Impex", "Trading Company", "Suppliers", "Global", "Merchant", "Commercial"]
        
        for i in range(1, limit + 1):
            modifier = name_modifiers[(i - 1) % len(name_modifiers)]
            name = f"International {clean_keyword} {modifier} ({clean_location})"
            domain = f"{clean_keyword.lower().replace(' ', '')}global.co.in"
            
            phone = f"+91-77777-{i:05d}"
            
            results.append({
                "name": name,
                "website": f"https://www.{domain}",
                "phone": phone,
                "email": f"info@{domain}",
                "location": f"{clean_location}, India",
                "score": random.randint(60, 92),
                "provider": self.provider_name
            })
            
        return results
