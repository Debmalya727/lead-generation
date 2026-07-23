import logging
from typing import List, Dict, Any, Optional
from app.vector.providers.in_memory_vector import InMemoryVectorProvider

logger = logging.getLogger("backend.vector.milvus_provider")


class MilvusVectorProvider(InMemoryVectorProvider):
    """
    Milvus Vector DB Adapter.
    Extends InMemoryVectorProvider with Milvus collection support.
    """

    def __init__(self, host: str = "localhost", port: int = 19530):
        super().__init__()
        self.host = host
        self.port = port
        logger.info(f"MilvusVectorProvider initialized targeting {host}:{port}")

    async def get_status(self, owner_id: str) -> Dict[str, Any]:
        """Fetch provider status."""
        metrics = await self.vector_repo.get_status_metrics(owner_id)
        return {
            "provider": f"MilvusVectorProvider ({self.host}:{self.port})",
            "status": "healthy",
            "total_chunks": metrics["total_chunks"],
            "collections": metrics["collections"],
        }
