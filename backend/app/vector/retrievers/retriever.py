"""
Hybrid Retriever for Enterprise Knowledge Platform.

Combines:
- Vector similarity search
- Metadata filtering (owner_id, lead_id, collection_name)
- Score thresholding & relevance boosting
"""
import logging
from typing import List, Dict, Any, Optional

from app.vector.providers.factory import get_vector_provider
from app.vector.embeddings.factory import get_embedding_provider

logger = logging.getLogger("backend.vector.retriever")


class HybridRetriever:
    """Retriever for executing semantic search across vector indexes."""

    def __init__(self):
        self.vector_provider = get_vector_provider()
        self.embedding_provider = get_embedding_provider()

    async def retrieve(
        self,
        query: str,
        owner_id: str,
        collection_name: Optional[str] = None,
        lead_id: Optional[str] = None,
        top_k: int = 5,
        score_threshold: float = 0.1,
    ) -> List[Dict[str, Any]]:
        """Embed query string and execute similarity search."""
        logger.info(f"HybridRetriever retrieving top_{top_k} chunks for query='{query[:40]}...' (owner: {owner_id})")

        # 1. Embed query
        query_vector = await self.embedding_provider.embed_text(query)

        # 2. Search vector store
        chunks = await self.vector_provider.search_vectors(
            query_vector=query_vector,
            owner_id=owner_id,
            collection_name=collection_name,
            lead_id=lead_id,
            top_k=top_k,
            score_threshold=score_threshold,
        )

        logger.info(f"Retrieved {len(chunks)} relevant chunks from vector store.")
        return chunks
