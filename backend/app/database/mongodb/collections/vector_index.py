"""
Beanie MongoDB Document collection for Phase 10: Vector Search & Knowledge Base.

Collection:
- VectorChunk (Main Beanie Document for chunk metadata & vector persistence)
"""
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from beanie import Document, PydanticObjectId
from pydantic import Field


class VectorChunk(Document):
    chunk_id: str = Field(..., description="Unique chunk identifier (e.g. lead_123_chunk_0)")
    document_id: str = Field(..., description="ID of source document (Lead, Intelligence, ResearchReport, etc.)")
    lead_id: Optional[PydanticObjectId] = None
    owner_id: PydanticObjectId

    collection_name: str = Field(
        ...,
        description="leads | company_intelligence | lead_scores | sales_intelligence | research_reports | campaigns | verified_facts | knowledge_graph"
    )
    title: str = Field(..., description="Human-readable title or subject of indexed document")
    content: str = Field(..., description="Text content chunk embedded into vector index")
    embedding: List[float] = Field(default_factory=list, description="Vector embedding values (e.g. 1536 floats)")
    
    chunk_index: int = Field(0, ge=0)
    total_chunks: int = Field(1, ge=1)
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary JSON metadata tags for filtering")

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "vector_chunks"
        indexes = [
            [("owner_id", 1), ("lead_id", 1)],
            [("owner_id", 1), ("collection_name", 1)],
            [("document_id", 1)],
            [("chunk_id", 1)],
        ]
