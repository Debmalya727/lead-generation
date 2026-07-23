"""
Beanie MongoDB Document collections for Phase 14: Enterprise Knowledge Fabric.
Includes 26 document collections:
  - Universal Knowledge Object (universal_knowledge_objects)
  - 14.1 Gateway (knowledge_documents, knowledge_import_jobs, knowledge_sources, knowledge_validation, knowledge_events)
  - 14.2 Normalization (knowledge_chunks)
  - 14.2.5 Compiler (compiled_knowledge_objects)
  - 14.3 Entity Intelligence (knowledge_entity_records)
  - 14.3.5 Ontology Manager (knowledge_ontology_records)
  - 14.4 Relationship Intelligence (knowledge_relationship_records)
  - 14.5 Enterprise Knowledge Graph (knowledge_graph_nodes_v2, knowledge_graph_edges_v2)
  - 14.5.5 Graph Optimizer (knowledge_graph_snapshots)
  - 14.6 Enterprise Memory (enterprise_memory_records)
  - 14.6.8 Memory Governance (memory_governance_records)
  - 14.6.5 Embedding Orchestrator (embedding_configs, embedding_caches)
  - 14.7.5 Retrieval Optimizer (retrieval_strategy_records)
  - 14.8.5 Citation Engine (citation_records)
  - 14.9 Enterprise RAG (rag_query_records)
  - 14.9.8 Answer Verification (answer_verification_records)
  - 14.9.5 Lifecycle Manager (knowledge_lifecycles)
  - 14.10 Analytics (knowledge_analytics_event_docs, knowledge_analytics_daily_docs, knowledge_alert_records, knowledge_export_records)
"""
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from beanie import Document
from pydantic import Field


# ─── UNIVERSAL KNOWLEDGE OBJECT COLLECTION ─────────────────────────────────────

class UniversalKnowledgeObjectDoc(Document):
    knowledge_id: str = Field(...)
    organization_id: str = Field("default_org")
    workspace_id: str = Field("default_workspace")
    owner_id: str = Field("user_default")
    
    source_type: str = Field("crm", description="crm | voice | meetings | emails | research | webhooks | documents | ai_reports")
    asset_type: str = Field("pdf", description="pdf | docx | pptx | xlsx | csv | markdown | json | xml | images | web_url")
    mime_type: str = Field("application/pdf")
    
    title: str = Field(...)
    description: Optional[str] = None
    summary: Optional[str] = None
    language: str = Field("en")
    
    checksum_sha256: str = Field(...)
    checksum_sha512: str = Field(...)
    fingerprint: str = Field(...)
    
    payload: Dict[str, Any] = Field(default_factory=dict)
    attachments: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    permissions: List[str] = Field(default_factory=lambda: ["user_default", "admin"])
    security_acl: List[str] = Field(default_factory=lambda: ["user_default", "admin"])
    classification: str = Field("Internal", description="Public | Internal | Confidential | Restricted")
    
    version: int = Field(1)
    status: str = Field("Active", description="Imported | Validated | Normalized | Compiled | Active | Archived | Deleted")
    tags: List[str] = Field(default_factory=list)
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "universal_knowledge_objects"
        indexes = [
            [("knowledge_id", 1)],
            [("organization_id", 1)],
            [("checksum_sha256", 1)],
            [("fingerprint", 1)],
            [("status", 1)],
            [("created_at", -1)],
        ]


# ─── 14.1 GATEWAY COLLECTIONS ──────────────────────────────────────────────────

class KnowledgeDocument(Document):
    document_id: str = Field(...)
    user_id: str = Field("user_default")
    org_id: Optional[str] = None
    title: str = Field(...)
    file_type: str = Field("pdf")
    file_size_bytes: int = Field(0)
    source_uri: Optional[str] = None
    
    security_acl: List[str] = Field(default_factory=lambda: ["user_default", "admin"])
    is_validated: bool = Field(True)
    virus_scan_passed: bool = Field(True)
    status: str = Field("completed")
    version: int = Field(1)
    
    total_chunks: int = Field(0)
    language: str = Field("en")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "knowledge_documents"
        indexes = [[("document_id", 1)], [("user_id", 1)], [("status", 1)], [("created_at", -1)]]


class KnowledgeImportJob(Document):
    job_id: str = Field(...)
    user_id: str = Field("user_default")
    source_name: str = Field(...)
    file_count: int = Field(1)
    status: str = Field("completed")
    processed_count: int = Field(0)
    error_log: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "knowledge_import_jobs"
        indexes = [[("job_id", 1)], [("user_id", 1)], [("status", 1)]]


class KnowledgeSource(Document):
    source_id: str = Field(...)
    name: str = Field(...)
    source_type: str = Field("crm")
    config: Dict[str, Any] = Field(default_factory=dict)
    is_active: bool = Field(True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "knowledge_sources"
        indexes = [[("source_id", 1)], [("source_type", 1)]]


class KnowledgeValidationRecord(Document):
    validation_id: str = Field(...)
    document_id: str = Field(...)
    quota_passed: bool = Field(True)
    virus_scan_passed: bool = Field(True)
    acl_passed: bool = Field(True)
    details: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "knowledge_validation"
        indexes = [[("validation_id", 1)], [("document_id", 1)]]


class KnowledgeEventRecord(Document):
    event_id: str = Field(...)
    event_type: str = Field(...)
    document_id: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "knowledge_events"
        indexes = [[("event_id", 1)], [("event_type", 1)], [("timestamp", -1)]]


# ─── 14.2 NORMALIZATION COLLECTION ─────────────────────────────────────────────

class KnowledgeChunk(Document):
    chunk_id: str = Field(...)
    document_id: str = Field(...)
    user_id: str = Field("user_default")
    
    chunk_index: int = Field(0)
    content: str = Field(...)
    token_count: int = Field(0)
    chunk_strategy: str = Field("semantic")
    
    embedding: List[float] = Field(default_factory=list)
    entity_ids: List[str] = Field(default_factory=list)
    bm25_tokens: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "knowledge_chunks"
        indexes = [[("chunk_id", 1)], [("document_id", 1)], [("user_id", 1)], [("created_at", -1)]]


# ─── 14.2.5 COMPILER COLLECTION ────────────────────────────────────────────────

class CompiledKnowledgeObjectDoc(Document):
    object_id: str = Field(...)
    document_id: str = Field(...)
    user_id: str = Field("user_default")
    
    compiled_text: str = Field(...)
    canonical_representation: Dict[str, Any] = Field(default_factory=dict)
    chunks_count: int = Field(0)
    entities_count: int = Field(0)
    tables_count: int = Field(0)
    images_count: int = Field(0)
    
    checksum: str = Field(...)
    version: int = Field(1)
    permissions: List[str] = Field(default_factory=lambda: ["user_default", "admin"])
    language: str = Field("en")
    
    compiled_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "compiled_knowledge_objects"
        indexes = [[("object_id", 1)], [("document_id", 1)], [("checksum", 1)]]


# ─── 14.3 ENTITY INTELLIGENCE COLLECTION ───────────────────────────────────────

class KnowledgeEntityRecord(Document):
    entity_id: str = Field(...)
    name: str = Field(...)
    canonical_name: str = Field(...)
    entity_type: str = Field("Company")
    
    aliases: List[str] = Field(default_factory=list)
    confidence_score: float = Field(0.95)
    properties: Dict[str, Any] = Field(default_factory=dict)
    document_ids: List[str] = Field(default_factory=list)
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "knowledge_entity_records"
        indexes = [[("entity_id", 1)], [("canonical_name", 1)], [("entity_type", 1)]]


# ─── 14.3.5 ONTOLOGY MANAGER COLLECTION ────────────────────────────────────────

class KnowledgeOntologyRecord(Document):
    ontology_id: str = Field(...)
    domain_name: str = Field("Sales", description="Sales | Finance | Legal | Engineering")
    class_name: str = Field(...)
    parent_class: Optional[str] = None
    properties_schema: Dict[str, Any] = Field(default_factory=dict)
    version: int = Field(1)
    is_active: bool = Field(True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "knowledge_ontology_records"
        indexes = [[("ontology_id", 1)], [("domain_name", 1)], [("class_name", 1)]]


# ─── 14.4 RELATIONSHIP INTELLIGENCE COLLECTION ──────────────────────────────────

class KnowledgeRelationshipRecord(Document):
    relationship_id: str = Field(...)
    source_entity_id: str = Field(...)
    target_entity_id: str = Field(...)
    relation_type: str = Field("ACQUIRED")
    
    confidence: float = Field(0.95)
    weight: float = Field(1.0)
    evidence_mapping: str = Field("")
    document_id: Optional[str] = None
    properties: Dict[str, Any] = Field(default_factory=dict)
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "knowledge_relationship_records"
        indexes = [[("relationship_id", 1)], [("source_entity_id", 1)], [("target_entity_id", 1)], [("relation_type", 1)]]


# ─── 14.5 ENTERPRISE KNOWLEDGE GRAPH COLLECTIONS ────────────────────────────────

class KnowledgeGraphNodeDoc(Document):
    node_id: str = Field(...)
    label: str = Field(...)
    node_type: str = Field(...)
    entity_id: Optional[str] = None
    properties: Dict[str, Any] = Field(default_factory=dict)
    degree: int = Field(0)
    centrality_score: float = Field(0.0)
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "knowledge_graph_nodes_v2"
        indexes = [[("node_id", 1)], [("label", 1)], [("node_type", 1)]]


class KnowledgeGraphEdgeDoc(Document):
    edge_id: str = Field(...)
    source_node_id: str = Field(...)
    target_node_id: str = Field(...)
    relation: str = Field(...)
    weight: float = Field(1.0)
    properties: Dict[str, Any] = Field(default_factory=dict)
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "knowledge_graph_edges_v2"
        indexes = [[("edge_id", 1)], [("source_node_id", 1)], [("target_node_id", 1)], [("relation", 1)]]


# ─── 14.5.5 GRAPH OPTIMIZER SNAPSHOT COLLECTION ──────────────────────────────

class KnowledgeGraphSnapshotDoc(Document):
    snapshot_id: str = Field(...)
    total_nodes: int = Field(0)
    total_edges: int = Field(0)
    partition_key: str = Field("default")
    hot_nodes: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "knowledge_graph_snapshots"
        indexes = [[("snapshot_id", 1)], [("partition_key", 1)]]


# ─── 14.6 UNIFIED ENTERPRISE MEMORY COLLECTION ─────────────────────────────────

class EnterpriseMemoryRecord(Document):
    memory_id: str = Field(...)
    user_id: str = Field("user_default")
    memory_type: str = Field("semantic")
    
    key: str = Field(...)
    value: str = Field(...)
    confidence: float = Field(0.95)
    decay_factor: float = Field(0.01)
    access_count: int = Field(1)
    retention_days: int = Field(365)
    
    associations: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_accessed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "enterprise_memory_records"
        indexes = [[("memory_id", 1)], [("user_id", 1)], [("memory_type", 1)], [("key", 1)]]


# ─── 14.6.8 MEMORY GOVERNANCE COLLECTION ───────────────────────────────────────

class MemoryGovernanceRecord(Document):
    governance_id: str = Field(...)
    memory_id: str = Field(...)
    user_id: str = Field(...)
    is_encrypted: bool = Field(True)
    is_legal_hold: bool = Field(False)
    gdpr_erasure_requested: bool = Field(False)
    retention_policy: str = Field("standard_365d")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "memory_governance_records"
        indexes = [[("governance_id", 1)], [("memory_id", 1)], [("user_id", 1)]]


# ─── 14.6.5 EMBEDDING ORCHESTRATOR COLLECTIONS ─────────────────────────────────

class EmbeddingConfigRecord(Document):
    config_id: str = Field(...)
    provider_name: str = Field("openai")
    model_name: str = Field("text-embedding-3-small")
    dimensions: int = Field(1536)
    is_default: bool = Field(True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "embedding_configs"
        indexes = [[("config_id", 1)], [("provider_name", 1)]]


class EmbeddingCacheRecord(Document):
    cache_id: str = Field(...)
    text_hash: str = Field(...)
    provider: str = Field("openai")
    model: str = Field("text-embedding-3-small")
    embedding: List[float] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "embedding_caches"
        indexes = [[("cache_id", 1)], [("text_hash", 1)]]


# ─── 14.7.5 RETRIEVAL OPTIMIZER COLLECTION ─────────────────────────────────────

class RetrievalStrategyRecord(Document):
    strategy_id: str = Field(...)
    query_pattern: str = Field(...)
    chosen_strategy: str = Field("hybrid", description="dense | sparse | graph | hybrid | cross_encoder")
    token_budget: int = Field(2000)
    efficiency_score: float = Field(0.95)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "retrieval_strategy_records"
        indexes = [[("strategy_id", 1)], [("chosen_strategy", 1)]]


# ─── 14.8.5 CITATION ENGINE COLLECTION ─────────────────────────────────────────

class CitationRecord(Document):
    citation_id: str = Field(...)
    citation_type: str = Field("chunk")
    source_id: str = Field(...)
    document_id: str = Field(...)
    location_reference: str = Field("")
    snippet: str = Field(...)
    speaker_name: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "citation_records"
        indexes = [[("citation_id", 1)], [("source_id", 1)], [("document_id", 1)]]


# ─── 14.9 ENTERPRISE RAG COLLECTION ────────────────────────────────────────────

class RAGQueryRecord(Document):
    query_id: str = Field(...)
    user_id: str = Field("user_default")
    query_text: str = Field(...)
    
    retrieval_strategy: str = Field("hybrid")
    retrieved_chunk_ids: List[str] = Field(default_factory=list)
    retrieved_node_ids: List[str] = Field(default_factory=list)
    
    answer_text: str = Field(...)
    hallucination_score: float = Field(0.04)
    citations: List[Dict[str, Any]] = Field(default_factory=list)
    latency_ms: float = Field(0.0)
    token_budget_used: int = Field(0)
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "rag_query_records"
        indexes = [[("query_id", 1)], [("user_id", 1)], [("created_at", -1)]]


# ─── 14.9.8 ANSWER VERIFICATION COLLECTION ─────────────────────────────────────

class AnswerVerificationRecord(Document):
    verification_id: str = Field(...)
    query_id: str = Field(...)
    evidence_validated: bool = Field(True)
    citations_valid: bool = Field(True)
    hallucination_detected: bool = Field(False)
    confidence_score: float = Field(0.98)
    verifier_notes: str = Field("Answer fully verified against enterprise Knowledge Graph and citations.")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "answer_verification_records"
        indexes = [[("verification_id", 1)], [("query_id", 1)]]


# ─── 14.9.5 LIFECYCLE MANAGER COLLECTION ───────────────────────────────────────

class KnowledgeLifecycleRecord(Document):
    lifecycle_id: str = Field(...)
    document_id: str = Field(...)
    state: str = Field("Active")
    is_legal_hold: bool = Field(False)
    retention_days: int = Field(365)
    soft_deleted: bool = Field(False)
    history: List[Dict[str, Any]] = Field(default_factory=list)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "knowledge_lifecycles"
        indexes = [[("lifecycle_id", 1)], [("document_id", 1)], [("state", 1)]]


# ─── 14.10 ANALYTICS COLLECTIONS ───────────────────────────────────────────────

class KnowledgeAnalyticsEventDoc(Document):
    event_id: str = Field(...)
    user_id: str = Field("user_default")
    event_type: str = Field(...)
    
    latency_ms: float = Field(0.0)
    precision_score: float = Field(1.0)
    recall_score: float = Field(1.0)
    cost_usd: float = Field(0.0)
    token_count: int = Field(0)
    cache_hit: bool = Field(False)
    
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "knowledge_analytics_event_docs"
        indexes = [[("event_id", 1)], [("user_id", 1)], [("event_type", 1)], [("timestamp", -1)]]


class KnowledgeAnalyticsDailyDoc(Document):
    date_key: str = Field(...)
    user_id: str = Field("global")
    
    total_queries: int = Field(0)
    total_ingestions: int = Field(0)
    avg_latency_ms: float = Field(0.0)
    avg_precision: float = Field(0.0)
    avg_recall: float = Field(0.0)
    cache_hit_rate: float = Field(0.0)
    total_cost_usd: float = Field(0.0)
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "knowledge_analytics_daily_docs"
        indexes = [[("date_key", 1)], [("user_id", 1)]]


class KnowledgeAlertRecord(Document):
    alert_id: str = Field(...)
    metric_name: str = Field(...)
    metric_value: float = Field(0.0)
    threshold_value: float = Field(0.0)
    severity: str = Field("warning")
    message: str = Field(...)
    resolved: bool = Field(False)
    triggered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "knowledge_alert_records"
        indexes = [[("alert_id", 1)], [("severity", 1)], [("resolved", 1)]]


class KnowledgeExportRecord(Document):
    export_id: str = Field(...)
    user_id: str = Field("user_default")
    format: str = Field("csv")
    row_count: int = Field(0)
    download_url: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "knowledge_export_records"
        indexes = [[("export_id", 1)], [("user_id", 1)]]
