import asyncio
import random
from typing import List
from app.modules.discovery.providers.base_provider import BaseDiscoveryProvider


class JustDialProvider(BaseDiscoveryProvider):
    def __init__(self):
        super().__init__("justdial")

    async def discover(self, keyword: str, location: str, limit: int = 20) -> List[dict]:
        """JustDial provider simulation yielding local directory listing entries."""
        # Simulate network request latencies
        await asyncio.sleep(random.uniform(1.0, 2.0))
        
        clean_keyword = keyword.strip()
        clean_location = location.strip()
        
        results = []
        name_modifiers = ["Enterprises", "Agency", "World", "Hub", "Distributors", "Stores", "Stall", "Point"]
        
        for i in range(1, limit + 1):
            modifier = name_modifiers[(i - 1) % len(name_modifiers)]
            name = f"{clean_keyword} {modifier} {clean_location}"
            domain = f"{clean_keyword.lower().replace(' ', '')}{modifier.lower()}.in"
            
            # Local contact numbers format
            phone = f"+91-98765-{i:05d}"
            
            results.append({
                "name": name,
                "website": f"https://www.{domain}",
                "phone": phone,
                "email": f"sales@{domain}",
                "location": f"{clean_location}, India",
                "score": random.randint(55, 90),
                "provider": self.provider_name
            })
            
        return results
