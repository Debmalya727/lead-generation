"""
Pydantic v2 Validation Schemas for Vector API.
"""
from typing import List, Dict, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field


class VectorIndexRequest(BaseModel):
    lead_id: str = Field(..., description="ID of the lead/company to index into vector store")


class VectorSearchRequest(BaseModel):
    query: str = Field(..., description="Natural language semantic query string")
    collection_name: Optional[str] = Field(None, description="Optional collection filter (leads, company_intelligence, research_reports, etc.)")
    lead_id: Optional[str] = Field(None, description="Optional target lead_id filter")
    top_k: int = Field(5, ge=1, le=50, description="Number of top vector matches to retrieve")
    score_threshold: float = Field(0.0, ge=0.0, le=1.0, description="Minimum similarity score threshold (0.0 - 1.0)")


class VectorSearchResultItem(BaseModel):
    chunk_id: str
    document_id: str
    lead_id: Optional[str] = None
    collection_name: str
    title: str
    content: str
    score: float
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class VectorSearchResponse(BaseModel):
    query: str
    total_matches: int
    results: List[VectorSearchResultItem] = Field(default_factory=list)


class VectorStatusResponse(BaseModel):
    provider: str
    status: str
    total_chunks: int
    collections: Dict[str, int] = Field(default_factory=dict)
