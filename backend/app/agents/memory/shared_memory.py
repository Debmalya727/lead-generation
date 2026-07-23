"""
Unified Shared Memory System for Enterprise Agent Runtime.

Integrates with Phase 10 Vector Search, RAG Pipelines, Research Reports,
Sales Intelligence, Lead Scores, Company Intelligence, and Knowledge Graph.
"""
import logging
from typing import Dict, Any, List, Optional

from app.vector.services.vector_service import VectorService
from app.vector.pipelines.rag_pipeline import RAGPipeline

logger = logging.getLogger("backend.agents.memory")


class SharedMemory:
    """Shared Memory providing unified knowledge retrieval and storage across platform modules."""

    def __init__(self, vector_service: Optional[VectorService] = None):
        self.vector_service = vector_service
        self.rag_pipeline = RAGPipeline()
        self._transient_memory: Dict[str, Any] = {}

    async def search(
        self,
        query: str,
        owner_id: str,
        collection_name: Optional[str] = None,
        lead_id: Optional[str] = None,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """Perform semantic search across indexed platform memory."""
        if self.vector_service:
            return await self.vector_service.search_vectors(
                query=query,
                owner_id=owner_id,
                collection_name=collection_name,
                lead_id=lead_id,
                top_k=top_k,
            )
        return []

    async def retrieve_rag(
        self,
        question: str,
        owner_id: str,
        collection_name: Optional[str] = None,
        lead_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Execute grounded RAG query over shared memory context."""
        return await self.rag_pipeline.execute_query(
            question=question,
            owner_id=owner_id,
            collection_name=collection_name,
            lead_id=lead_id,
        )

    def store(self, key: str, value: Any) -> None:
        """Store key-value data in transient memory."""
        self._transient_memory[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Fetch key-value data from transient memory."""
        return self._transient_memory.get(key, default)

    async def summarize(self, doc_type: str, doc_id: str, owner_id: str) -> str:
        """Generate a summary of a specific memory document."""
        chunks = await self.search(query=doc_id, owner_id=owner_id, top_k=3)
        if chunks:
            return "\n".join([c["content"] for c in chunks])
        return f"No memory record found for {doc_type} '{doc_id}'."
