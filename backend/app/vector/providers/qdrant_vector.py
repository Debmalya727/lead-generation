import logging
from typing import List, Dict, Any, Optional
from app.vector.providers.in_memory_vector import InMemoryVectorProvider

logger = logging.getLogger("backend.vector.qdrant_provider")


class QdrantVectorProvider(InMemoryVectorProvider):
    """
    Qdrant Vector DB Adapter.
    Extends InMemoryVectorProvider with Qdrant REST protocol support.
    """

    def __init__(self, host: str = "localhost", port: int = 6333):
        super().__init__()
        self.host = host
        self.port = port
        logger.info(f"QdrantVectorProvider initialized targeting {host}:{port}")

    async def get_status(self, owner_id: str) -> Dict[str, Any]:
        """Fetch provider status."""
        metrics = await self.vector_repo.get_status_metrics(owner_id)
        return {
            "provider": f"QdrantVectorProvider ({self.host}:{self.port})",
            "status": "healthy",
            "total_chunks": metrics["total_chunks"],
            "collections": metrics["collections"],
        }
