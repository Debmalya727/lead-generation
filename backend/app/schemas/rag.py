"""
Pydantic v2 Validation Schemas for RAG API.
"""
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field


class RAGQueryRequest(BaseModel):
    question: str = Field(..., description="User question to answer using grounded knowledge base context")
    collection_name: Optional[str] = Field(None, description="Optional collection scope")
    lead_id: Optional[str] = Field(None, description="Optional target lead scope")
    top_k: int = Field(5, ge=1, le=20, description="Top evidence chunks to retrieve for context")


class RAGSourceCitation(BaseModel):
    doc_num: int
    collection: str
    document_id: str
    lead_id: Optional[str] = None
    title: str
    score: float
    content_snippet: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RAGQueryResponse(BaseModel):
    question: str
    answer: str
    confidence_score: int = Field(..., ge=0, le=100)
    summary_points: List[str] = Field(default_factory=list)
    sources: List[RAGSourceCitation] = Field(default_factory=list)
