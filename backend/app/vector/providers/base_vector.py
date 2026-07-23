from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class BaseVectorProvider(ABC):
    """Abstract base class for Vector Store Provider Adapters."""

    @abstractmethod
    async def upsert_chunks(self, chunks: List[Dict[str, Any]]) -> bool:
        """Upsert vector chunks into vector database index."""
        raise NotImplementedError

    @abstractmethod
    async def search_vectors(
        self,
        query_vector: List[float],
        owner_id: str,
        collection_name: Optional[str] = None,
        lead_id: Optional[str] = None,
        top_k: int = 10,
        score_threshold: float = 0.0,
    ) -> List[Dict[str, Any]]:
        """Perform similarity vector search with metadata filters."""
        raise NotImplementedError

    @abstractmethod
    async def delete_document_chunks(self, document_id: str, owner_id: str) -> bool:
        """Delete chunks for a specific document_id."""
        raise NotImplementedError

    @abstractmethod
    async def get_status(self, owner_id: str) -> Dict[str, Any]:
        """Fetch vector store provider health and chunk metrics."""
        raise NotImplementedError
