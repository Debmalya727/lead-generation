"""
Phase 14 — Knowledge Fabric Production REST API Router.
Includes endpoints for all 19 sub-phases (Gateway, Normalization, Compiler, Entity, Ontology, Relationship, Graph, Graph Optimizer, Memory, Memory Governance, Embeddings, Retrieval, Retrieval Optimizer, Reasoning, Citations, RAG, Answer Verification, Lifecycle, Analytics).
"""
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.knowledge.analytics.knowledge_analytics import knowledge_analytics_platform
from app.knowledge.citations.citation_engine import citation_engine
from app.knowledge.compiler.knowledge_compiler import enterprise_knowledge_compiler
from app.knowledge.embeddings.embedding_orchestrator import embedding_orchestrator
from app.knowledge.entity.entity_intelligence import entity_intelligence_platform
from app.knowledge.gateway.knowledge_gateway import enterprise_knowledge_gateway
from app.knowledge.graph.graph_optimizer import knowledge_graph_optimizer
from app.knowledge.graph.knowledge_graph import enterprise_knowledge_graph
from app.knowledge.lifecycle.knowledge_lifecycle import knowledge_lifecycle_manager
from app.knowledge.memory.memory_governance import memory_governance_service
from app.knowledge.memory.unified_memory import unified_enterprise_memory
from app.knowledge.models.universal_knowledge_object import universal_knowledge_object_manager
from app.knowledge.normalization.knowledge_normalization import knowledge_normalization_platform
from app.knowledge.ontology.knowledge_ontology import knowledge_ontology_manager
from app.knowledge.rag.answer_verification import answer_verification_engine
from app.knowledge.rag.enterprise_rag import enterprise_rag_platform
from app.knowledge.reasoning.knowledge_reasoning import knowledge_reasoning_engine
from app.knowledge.relationship.relationship_intelligence import relationship_intelligence_platform
from app.knowledge.retrieval.hybrid_retrieval import hybrid_retrieval_platform
from app.knowledge.retrieval.retrieval_optimizer import retrieval_optimizer

logger = logging.getLogger("backend.knowledge.router")

router = APIRouter(prefix="/knowledge", tags=["Enterprise Knowledge Fabric (Phase 14)"])


# ─── Pydantic Request Models ───────────────────────────────────────────────────

class UniversalObjectRequest(BaseModel):
    title: str = Field(...)
    content: str = Field(...)
    source_type: str = Field("crm")
    asset_type: str = Field("pdf")


class IngestAssetRequest(BaseModel):
    title: str = Field(...)
    content_or_uri: str = Field(...)
    asset_type: str = Field("pdf")
    user_id: str = Field("user_default")


class NormalizeRequest(BaseModel):
    document_id: str = Field(...)
    raw_text: str = Field(...)
    user_id: str = Field("user_default")
    chunk_strategy: str = Field("semantic")


class OntologyRequest(BaseModel):
    domain_name: str = Field("Sales")
    class_name: str = Field(...)
    parent_class: Optional[str] = None


class MemoryGovernanceRequest(BaseModel):
    memory_id: str = Field(...)
    user_id: str = Field("user_default")
    retention_policy: str = Field("standard_365d")


class RetrievalOptimizeRequest(BaseModel):
    query_pattern: str = Field(...)
    token_budget: int = Field(2000)


class RAGVerifyRequest(BaseModel):
    query_id: str = Field(...)
    answer_text: str = Field(...)
    citations: List[Dict[str, Any]] = Field(default_factory=list)
    hallucination_score: float = Field(0.04)


# ─── Universal Knowledge Object API ────────────────────────────────────────────

@router.post("/universal/create")
async def create_universal_object(req: UniversalObjectRequest):
    obj = await universal_knowledge_object_manager.create_knowledge_object(
        title=req.title, content=req.content, source_type=req.source_type, asset_type=req.asset_type
    )
    return obj.model_dump()


# ─── Gateway APIs ─────────────────────────────────────────────────────────────

@router.post("/gateway/ingest")
async def ingest_asset(req: IngestAssetRequest):
    doc = await enterprise_knowledge_gateway.ingest_asset(
        title=req.title, content_or_uri=req.content_or_uri, asset_type=req.asset_type, user_id=req.user_id
    )
    return doc.model_dump()


# ─── Normalization & Compiler APIs ────────────────────────────────────────────

@router.post("/normalization/process")
async def normalize(req: NormalizeRequest):
    chunks = await knowledge_normalization_platform.normalize_and_chunk(
        document_id=req.document_id, raw_text=req.raw_text, user_id=req.user_id, chunk_strategy=req.chunk_strategy
    )
    return {"chunk_count": len(chunks), "chunks": [c.model_dump() for c in chunks]}


@router.post("/compiler/compile")
async def compile_doc(document_id: str = Query(...)):
    obj = await enterprise_knowledge_compiler.compile_document(document_id=document_id)
    return obj.model_dump()


# ─── Ontology Manager API (14.3.5) ─────────────────────────────────────────────

@router.post("/ontology/register")
async def register_ontology(req: OntologyRequest):
    rec = await knowledge_ontology_manager.register_class(
        domain_name=req.domain_name, class_name=req.class_name, parent_class=req.parent_class
    )
    return rec.model_dump()


@router.get("/ontology/list")
async def list_ontology(domain_name: str = Query("Sales")):
    recs = await knowledge_ontology_manager.get_domain_ontology(domain_name=domain_name)
    return [r.model_dump() for r in recs]


# ─── Graph & Graph Optimizer APIs (14.5 & 14.5.5) ──────────────────────────────

@router.get("/graph/traversal")
async def traverse_graph(start_node_id: str = Query(...)):
    return await enterprise_knowledge_graph.traverse(start_node_id=start_node_id)


@router.post("/graph/optimize")
async def optimize_graph(partition_key: str = Query("default")):
    snap = await knowledge_graph_optimizer.optimize_and_snapshot(partition_key=partition_key)
    return snap.model_dump()


# ─── Memory Governance API (14.6.8) ─────────────────────────────────────────────

@router.post("/memory/governance/apply")
async def apply_memory_governance(req: MemoryGovernanceRequest):
    rec = await memory_governance_service.apply_governance_policy(
        memory_id=req.memory_id, user_id=req.user_id, retention_policy=req.retention_policy
    )
    return rec.model_dump()


@router.post("/memory/governance/gdpr-erasure")
async def gdpr_erasure(user_id: str = Query("user_default")):
    count = await memory_governance_service.process_gdpr_erasure(user_id=user_id)
    return {"erased_count": count, "status": "completed"}


# ─── Retrieval Optimizer API (14.7.5) ─────────────────────────────────────────

@router.post("/retrieval/optimize")
async def optimize_retrieval(req: RetrievalOptimizeRequest):
    rec = await retrieval_optimizer.select_optimal_strategy(query_pattern=req.query_pattern, token_budget=req.token_budget)
    return rec.model_dump()


# ─── Answer Verification API (14.9.8) ──────────────────────────────────────────

@router.post("/rag/verify")
async def verify_answer(req: RAGVerifyRequest):
    rec = await answer_verification_engine.verify_answer(
        query_id=req.query_id, answer_text=req.answer_text, citations=req.citations, hallucination_score=req.hallucination_score
    )
    return rec.model_dump()


# ─── RAG & Analytics APIs ─────────────────────────────────────────────────────

@router.post("/rag/query")
async def execute_rag(query_text: str = Query(...)):
    rec = await enterprise_rag_platform.execute_rag_pipeline(query_text=query_text)
    return rec.model_dump()


@router.get("/analytics/dashboard")
async def get_dashboard():
    return await knowledge_analytics_platform.get_dashboard()
