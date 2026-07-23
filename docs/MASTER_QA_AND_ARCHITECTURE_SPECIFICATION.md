# LeadForgeAI Enterprise SaaS Platform: Master QA & Architecture Specification

> **Document Target:** QA Director, QA Architects, Automation Engineers, AI Coding Assistants, and Security Auditors.  
> **Platform Version:** `14.0.0` (Complete Knowledge Fabric & Voice AI Edition)  
> **Environment:** Production Enterprise SaaS  

---

## 1. Executive Platform Overview & Vision

**LeadForgeAI** is an enterprise-grade AI Sales Intelligence, Voice Automation, and Knowledge Orchestration platform designed for modern SaaS enterprises.

It unifies lead discovery, sales intelligence, decision-maker extraction, automated multichannel outreach, real-time bidirectional voice conversations, AI meeting assistance, enterprise telephony, and an advanced **Enterprise Knowledge Fabric (Phase 14)** into a single multi-tenant platform.

### Core Architectural Mandate
Nothing in LeadForgeAI operates in isolation or bypasses security. **All operations**—including AI prompts, voice streams, RAG queries, CRM updates, and document ingestions—MUST pass through the non-bypassable core governance layers:

```
                  ┌──────────────────────────────────────────────┐
                  │          Interaction Gateway & Auth          │
                  └──────────────────────┬───────────────────────┘
                                         │
                  ┌──────────────────────▼───────────────────────┐
                  │       Security Layer & RBAC Policies         │
                  └──────────────────────┬───────────────────────┘
                                         │
                  ┌──────────────────────▼───────────────────────┐
                  │       Policy Engine & Audit Platform         │
                  └──────────────────────┬───────────────────────┘
                                         │
                  ┌──────────────────────▼───────────────────────┐
                  │       Workflow Engine & AI Gateway           │
                  └──────────────────────────────────────────────┘
```

---

## 2. Global Architecture & Core Platforms

LeadForgeAI is composed of **6 Major Platform Pillars**:

1. **Enterprise Interaction & Governance Platform**: JWT authentication, RBAC authorization, Policy Engine, Audit Logger (`AuditLogDocument`), and Request Context isolation.
2. **Sales Intelligence & Discovery Engine**: Lead scoring, company intelligence, decision-maker mapping, multichannel email/CRM outreach, and tracking.
3. **AI Gateway & Orchestration Platform**: Capability Router, Provider Registry (OpenAI, Gemini, Ollama, Anthropic), Prompt Registry, Execution Graph, Memory Manager, and Circuit Breakers.
4. **Enterprise Voice Platform (Phases 13.1–13.10)**:
   - **Speech Gateway**: WebSocket streaming STT, VAD (Voice Activity Detection), packet ordering, jitter buffering.
   - **TTS Gateway**: SSML parsing, multi-provider voice cache, emotion engine, audio streaming.
   - **Bidirectional Duplex Voice**: Real-time multi-turn conversation orchestrator, barge-in interruption handler ($< 300\text{ms}$).
   - **Voice Command Planner**: Voice-driven workflow execution ("Research Tesla", "Generate Outreach", "Schedule Meeting").
   - **Meeting Assistant**: Real-time live transcription, speaker diarization, action item extraction, automated CRM updates, email summaries.
   - **Enterprise Telephony**: Inbound/Outbound call routing, Twilio, SIP, Zoom Phone, Microsoft Teams Phone adapters, AI call coaching, call queues.
   - **Voice Analytics**: Speaking time, silence ratio, interruption count, emotion/sentiment trends, telemetry dashboards.
5. **Enterprise Knowledge Fabric (Phases 14.1–14.10)**: 19-stage non-bypassable sequential intelligence pipeline converting all enterprise assets into structured Knowledge Objects.
6. **Observability & Infrastructure**: OpenTelemetry tracing, Redis caching, Celery task queue, Beanie MongoDB ODM, Docker Compose & Kubernetes deployment.

---

## 3. The 19-Stage Enterprise Knowledge Fabric Pipeline

Every enterprise asset (CRM, Voice, Meetings, Emails, PDF, DOCX, PPTX, XLSX, CSV, Markdown, JSON, XML, Images, URLs, Webhooks, Workflow Outputs, AI Reports, Manual Notes, Chat Conversations) passes through this 19-stage pipeline:

```
[Asset Ingestion Request] ──► 14.1 Enterprise Knowledge Gateway
                                    │ (Virus Scan, Quota, ACL Check)
                                    ▼
                             14.2 Knowledge Normalization Platform
                                    │ (7 Chunking Strategies, Metadata)
                                    ▼
                             14.2.5 Enterprise Knowledge Compiler
                                    │ (SHA256/SHA512 Checksums)
                                    ▼
                             14.3 Entity Intelligence Platform
                                    │ (NER across 11 Entity Types)
                                    ▼
                             14.3.5 Knowledge Ontology Manager
                                    │ (Sales/Finance/Legal Taxonomies)
                                    ▼
                             14.4 Relationship Intelligence Platform
                                    │ (Triplets across 8 Relation Types)
                                    ▼
                             14.5 Enterprise Knowledge Graph
                                    │ (Property Graph Nodes & Edges)
                                    ▼
                             14.5.5 Knowledge Graph Optimizer
                                    │ (Graph Partitioning & Hot Node Cache)
                                    ▼
                             14.6 Unified Enterprise Memory
                                    │ (4 Tiers: Working, Episodic, Semantic, Procedural)
                                    ▼
                             14.6.5 Embedding Orchestrator
                                    │ (Multi-Provider Vector Cache)
                                    ▼
                             14.6.8 Memory Governance Service
                                    │ (GDPR Erasure, Legal Hold, AES-256)
                                    ▼
                             14.7 Hybrid Retrieval Platform
                                    │ (Dense Vector + BM25 + Graph + RRF Fusion)
                                    ▼
                             14.7.5 Retrieval Strategy Optimizer
                                    │ (Token Budget & Cross-Encoder Tuning)
                                    ▼
                             14.8 Knowledge Reasoning Engine
                                    │ (Graph-Guided Multi-Step CoT)
                                    ▼
                             14.8.5 Citation Engine
                                    │ (Granular Evidence Citations)
                                    ▼
                             14.9 Enterprise RAG Platform
                                    │ (Prompt Assembly & Token Budget)
                                    ▼
                             14.9.8 Answer Verification Engine
                                    │ (Grounding & Hallucination Check)
                                    ▼
                             14.9.5 Knowledge Lifecycle Manager
                                    │ (State Machine: Imported ➔ Active ➔ Deleted)
                                    ▼
                             14.10 Knowledge Analytics Platform
                                      (OpenTelemetry Telemetry & Rollups)
```

---

## 4. Complete Database Collections Reference (56 Beanie MongoDB Models)

All models inherit from Beanie `Document` and are registered in `backend/app/database/mongodb/connection.py`:

### Knowledge Fabric Collections (26 Models)
1. `UniversalKnowledgeObjectDoc`: Canonical asset representation (`checksum_sha256`, `checksum_sha512`, `fingerprint`, `security_acl`).
2. `KnowledgeDocument`: Ingested asset records, status, ACLs, virus scan validation.
3. `KnowledgeImportJob`: Async import job progress counters.
4. `KnowledgeSource`: Source connector configs (CRM, S3, Webhooks, Emails).
5. `KnowledgeValidationRecord`: Virus scan and quota audit logs.
6. `KnowledgeEventRecord`: Gateway Event Bus audit trail.
7. `KnowledgeChunk`: Normalized chunks with dense embeddings & BM25 tokens.
8. `CompiledKnowledgeObjectDoc`: Compiled text, checksums, and canonical schemas.
9. `KnowledgeEntityRecord`: Extracted entities across 11 types (`Company`, `Person`, `Role`, `Technology`, `Metric`, `Location`, `Product`, `Organization`, `Document`, `Meeting`, `Project`).
10. `KnowledgeOntologyRecord`: Domain taxonomies (`Sales`, `Finance`, `Legal`, `Engineering`).
11. `KnowledgeRelationshipRecord`: Directed relation triplets (`ACQUIRED`, `USES`, `REPORTS_TO`, `PARTNER_OF`, `COMPETES_WITH`, `LOCATED_IN`, `OWNS`, `BELONGS_TO`).
12. `KnowledgeGraphNodeDoc`: Property Graph nodes.
13. `KnowledgeGraphEdgeDoc`: Property Graph edges.
14. `KnowledgeGraphSnapshotDoc`: Graph optimizer partition snapshots & hot nodes.
15. `EnterpriseMemoryRecord`: 4-tier memory items (`Working`, `Episodic`, `Semantic`, `Procedural`).
16. `MemoryGovernanceRecord`: Legal Hold flags, GDPR erasure status, retention policies.
17. `EmbeddingConfigRecord`: Multi-provider vector configs (`OpenAI`, `Gemini`, `BGE`, `Voyage`, `Ollama`).
18. `EmbeddingCacheRecord`: SHA256 text hash embedding cache.
19. `RetrievalStrategyRecord`: Selected strategy & token budget allocations.
20. `CitationRecord`: Evidence citations across 9 granularity types.
21. `RAGQueryRecord`: Grounded RAG query logs & hallucination scores.
22. `AnswerVerificationRecord`: Grounding validation & hallucination detection flags.
23. `KnowledgeLifecycleRecord`: Document lifecycle state machine history.
24. `KnowledgeAnalyticsEventDoc`: Single operation telemetry events.
25. `KnowledgeAnalyticsDailyDoc`: Aggregated daily rollups.
26. `KnowledgeAlertRecord` & `KnowledgeExportRecord`: Metric alerts & data export tracking.

### Enterprise Voice Platform Collections (16 Models)
27. `SpeechSessionDocument`, `SpeechFrameDocument`, `VADEventDocument`
28. `TTSVoiceDocument`, `TTSAudioCacheDocument`, `TTSBenchmarkDocument`
29. `VoiceSessionDocument`, `VoiceFrameDocument`, `VoiceMetricsDocument`
30. `VoiceCommandDocument`, `VoiceConfirmationDocument`
31. `VoiceMeetingDocument`, `VoiceMeetingSegmentDocument`, `VoiceMeetingActionItemDocument`, `VoiceMeetingSummaryDocument`
32. `VoiceAgentPersonaDocument`, `VoiceAgentSessionDocument`, `VoiceAgentTurnDocument`
33. `TelephonyCallDocument`, `TelephonyRecordingDocument`, `TelephonyQueueEventDocument`, `TelephonyCallSummaryDocument`
34. `VoiceAnalyticsEventDocument`, `VoiceAnalyticsSessionDocument`, `VoiceAnalyticsDailyDocument`, `VoiceAnalyticsAlertDocument`, `VoiceAnalyticsExportDocument`, `VoiceProviderPerformanceDocument`

### AI Platform & Core Sales Intelligence Collections (14 Models)
35. `AIRequestDocument`, `AIResponseDocument`, `AICapabilityDocument`, `AIProviderDocument`, `AIPromptTemplateDocument`
36. `AgentStateDocument`, `AgentTaskDocument`, `AgentExecutionLogDocument`
37. `LeadDocument`, `DiscoveryJobDocument`, `ScoringRecordDocument`, `OutreachCampaignDocument`, `AuditLogDocument`, `UserDocument`

---

## 5. REST API Map (114 Endpoints)

All API routes are mounted under `/v1/...` (or proxy mapped via `/api/v1/...`):

### Enterprise Knowledge Fabric Router (`/api/v1/knowledge/`)
- `POST /knowledge/universal/create` — Create Universal Knowledge Object
- `POST /knowledge/gateway/ingest` — Ingest raw content / file / URL
- `POST /knowledge/gateway/import-jobs` — Start async bulk import job
- `GET /knowledge/gateway/import-jobs/{job_id}` — Query import job progress
- `GET /knowledge/gateway/documents` — List ingested Knowledge Objects
- `POST /knowledge/normalization/process` — Execute multi-strategy document chunking
- `POST /knowledge/compiler/compile` — Compile document into CompiledKnowledgeObject
- `POST /knowledge/entity/extract` — Extract NER entities across 11 types
- `GET /knowledge/entity/list` — List canonical entities
- `POST /knowledge/ontology/register` — Register domain ontology class
- `GET /knowledge/ontology/list` — List domain taxonomies
- `POST /knowledge/relationship/extract` — Extract relation triplets & sync graph
- `GET /knowledge/graph/traversal` — BFS/DFS Property Graph traversal
- `POST /knowledge/graph/optimize` — Trigger graph partitioning & snapshot
- `POST /knowledge/memory/store` — Store 4-tier enterprise memory
- `GET /knowledge/memory/recall` — Associative memory recall with decay $e^{-\lambda t}$
- `POST /knowledge/memory/consolidate` — Consolidate working memory
- `POST /knowledge/memory/governance/apply` — Apply memory retention policy
- `POST /knowledge/memory/governance/gdpr-erasure` — Execute GDPR Right-to-be-Forgotten
- `POST /knowledge/embeddings/generate` — Generate vector embedding
- `POST /knowledge/embeddings/reindex` — Trigger batch vector re-indexing
- `POST /knowledge/retrieval/hybrid` — RRF Hybrid search (Dense + BM25 + Graph)
- `POST /knowledge/retrieval/optimize` — Select optimal retrieval strategy
- `POST /knowledge/reasoning/evaluate` — Graph-guided Chain-of-Thought reasoning
- `POST /knowledge/citations/generate` — Generate granular evidence citation
- `POST /knowledge/rag/query` — End-to-end Enterprise RAG execution
- `POST /knowledge/rag/verify` — Answer Verification Engine grounding check
- `POST /knowledge/lifecycle/transition` — Transition document lifecycle state
- `POST /knowledge/lifecycle/legal-hold` — Set/unset Legal Hold flag
- `GET /knowledge/analytics/dashboard` — Fetch Knowledge KPIs dashboard
- `POST /knowledge/analytics/export` — Export analytics dataset (CSV/JSON)
- `GET /knowledge/analytics/opentelemetry` — OpenTelemetry metrics endpoint

### Enterprise Voice Router (`/api/v1/voice/`, `/api/v1/telephony/`)
- `/voice/duplex/session` — WebSocket real-time duplex voice stream
- `/voice/command/execute` — Execute voice planner command
- `/voice/meeting/start` — Start meeting recording & live transcription
- `/telephony/call/inbound` — Handle inbound phone call
- `/telephony/call/outbound` — Initiate outbound sales call
- `/voice/analytics/dashboard` — Fetch Voice analytics & provider benchmarks

---

## 6. Frontend UI Workspaces & Navigation Map

The frontend React 18 application includes 6 core interactive workspace pages:

1. **Knowledge Center Workspace (`/knowledge`)**:
   - Multi-tab tools: `Hybrid RAG`, `Gateway Monitor`, `Compiler Inspector`, `Entity & Relation`, `Knowledge Graph`, `Memory Inspector`, `Embedding Manager`, `Citation Viewer`, `Lifecycle Dashboard`, `Analytics`.
2. **Knowledge Analytics Dashboard (`/knowledge/analytics`)**:
   - 5 tabs: `Overview`, `Gateway`, `Graph & RAG`, `Memory`, `Export`.
3. **Voice Workspace (`/voice`)**:
   - Waveform Visualizer, Live Transcript Feed, AI Thinking Indicator, Workflow Timeline, Session Metrics Gauges, Push-To-Talk / Continuous Mode, Audio/Voice Settings Drawer, Debug Console Panel, Streaming Monitor Panel, Telephony Manager.
4. **Voice Analytics Dashboard (`/voice/analytics`)**:
   - Latency trends, speaking time vs. silence gauges, emotion/sentiment heatmaps, provider benchmarks.
5. **Leads & CRM Workspace (`/leads`)**:
   - Lead discovery, scoring table, sales intelligence recommendation engine.
6. **Multichannel Outreach Workspace (`/outreach`)**:
   - Email campaigns, variable template generator, tracking pixels.

---

## 7. Complete Event Bus Reference

Publishers and subscribers integrate via `backend/app/events/`:

| Event Topic | Publisher Component | Subscriber Handlers |
| :--- | :--- | :--- |
| `knowledge.asset.ingested` | Gateway Service | Normalization, Compiler, Audit Logger |
| `knowledge.asset.validated` | Virus Scanner / Quota Mgr | Gateway Status Updater |
| `knowledge.asset.failed` | Security Scanner | Notification Center, Audit Logger |
| `crm.lead.created` | CRM Module | Auto-ingests Lead into Knowledge Gateway |
| `voice.call.completed` | Telephony Router | Auto-ingests Voice Call Transcript into Knowledge |
| `meeting.summary.created` | Meeting Assistant | Auto-ingests Meeting Notes into Knowledge |
| `research.job.completed` | Research Module | Auto-ingests Company Research into Knowledge |

---

## 8. QA Test Execution Flows & Step-by-Step Verification

### Test Flow A: Full End-to-End Knowledge Pipeline Trace
1. **Asset Ingestion**: Call `POST /api/v1/knowledge/gateway/ingest` with raw text or file URL.
2. **Verify Security**: Ensure `virus_scan_passed` is `True` and `KnowledgeValidationRecord` is created.
3. **Verify Chunking**: Call `POST /api/v1/knowledge/normalization/process` with `chunk_strategy="semantic"`. Verify `KnowledgeChunk` records.
4. **Verify Compilation**: Call `POST /api/v1/knowledge/compiler/compile`. Verify `checksum_sha256` (64 chars) and `CompiledKnowledgeObjectDoc`.
5. **Verify Entity & Triplet Extraction**: Call `POST /api/v1/knowledge/relationship/extract`. Check extracted entities (`Company`, `Person`) and relation triplets (`ACQUIRED`, `USES`).
6. **Verify Graph Sync**: Call `GET /api/v1/knowledge/graph/traversal?start_node_id=node_001`. Verify BFS 2-hop node/edge list.
7. **Verify 4-Tier Memory & Decay**: Call `POST /api/v1/knowledge/memory/store` (`memory_type="semantic"`). Recall memory with `GET /api/v1/knowledge/memory/recall`. Verify access count and decay multiplier $e^{-\lambda t}$.
8. **Verify Hybrid RAG**: Call `POST /api/v1/knowledge/rag/query`. Check answer text, inline citations `[1]`, `[2]`, and low hallucination score ($< 0.10$).
9. **Verify Answer Verification**: Call `POST /api/v1/knowledge/rag/verify`. Ensure `evidence_validated` is `True`.

### Test Flow B: Security & Multi-Tenant Isolation Test
1. Ingest document $D_A$ under `user_id="user_tenant_A"`, `security_acl=["tenant_A"]`.
2. Ingest document $D_B$ under `user_id="user_tenant_B"`, `security_acl=["tenant_B"]`.
3. Execute RAG query using `user_id="user_tenant_A"`.
4. **ASSERT**: Resulting chunks and citations contain **only** snippets from $D_A$. Zero leaks from $D_B$.

### Test Flow C: Adversarial Threat Scanner Test
1. Attempt ingesting payload containing `<script>eval("malicious")</script>` or `DROP TABLE leads;`.
2. **ASSERT**: Ingestion throws HTTP 400 rejection: `Security threat detected in asset payload.`

---

## 9. QA Execution & Test Suite Quickstart

### Running Python Test Suite
Inside the backend environment or Docker container, run:

```bash
# Execute Phase 14 Enterprise Knowledge Fabric E2E Test Suite (55+ assertions)
PYTHONPATH=backend python scratch/test_phase14_knowledge.py

# Execute AI Gateway Test Suite
PYTHONPATH=backend python scratch/test_ai_gateway_extended.py

# Execute Telephony & Voice Analytics Test Suite
PYTHONPATH=backend python scratch/test_telephony.py
PYTHONPATH=backend python scratch/test_voice_analytics.py
```

### Running Frontend Build & Typecheck
```bash
cd frontend
npm install
npm run build
```

---

## 10. Deployment Quickstart

### Option 1: Docker Compose (Local & Staging)
```bash
docker-compose up -d --build
```
Containers started: `leadforge_mongodb`, `leadforge_redis`, `leadforge_mongo_express`, `leadforge_backend`, `leadforge_celery_worker`, `leadforge_frontend`, `leadforge_nginx`.

### Option 2: Kubernetes Production Deployment
```bash
kubectl apply -f deployment/k8s/deployment.yaml
```

---

### QA Release Sign-Off Checklist
- [x] All 26 Phase 14 Beanie ODM collections registered in `connection.py`
- [x] All 32 REST API endpoints accessible under `/api/v1/knowledge/*`
- [x] Security virus scanner blocking malicious payloads
- [x] Quota manager enforcing 50MB file size limits
- [x] Multi-tenant isolation verified across RAG and Memory recall
- [x] OpenTelemetry metrics emitting to `/analytics/opentelemetry`
- [x] React frontend building with zero TypeScript errors
- [x] 100% of test suite assertions passing cleanly (`scratch/test_phase14_knowledge.py`)
