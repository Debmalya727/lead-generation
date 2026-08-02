import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

export const KnowledgeCenterPage: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const [activeTab, setActiveTab] = useState<
    'rag' | 'gateway' | 'compiler' | 'entity' | 'graph' | 'memory' | 'embeddings' | 'citations' | 'lifecycle' | 'analytics'
  >('rag');

  // Input states
  const [question, setQuestion] = useState<string>('What technologies and architecture power LeadForgeAI?');
  const [ingestTitle, setIngestTitle] = useState('Enterprise Knowledge Policy 2026');
  const [ingestContent, setIngestContent] = useState('LeadForgeAI integrates Knowledge Fabric with Graph Reasoning, 4-Tier Memory, and RAG.');
  const [ingestType, setIngestType] = useState('pdf');

  // Results
  const [ragResult, setRagResult] = useState<any>(null);
  const [ingestResult, setIngestResult] = useState<any>(null);
  const [compilerResult, setCompilerResult] = useState<any>(null);
  const [entitiesResult, setEntitiesResult] = useState<any[]>([]);
  const [graphResult, setGraphResult] = useState<any>(null);
  const [memoriesResult, setMemoriesResult] = useState<any[]>([]);
  const [embeddingResult, setEmbeddingResult] = useState<any>(null);
  const [citationResult, setCitationResult] = useState<any>(null);
  const [lifecycleResult, setLifecycleResult] = useState<any>(null);
  const [analyticsResult, setAnalyticsResult] = useState<any>(null);

  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const token = () => localStorage.getItem('access_token');
  const headers = () => ({ Authorization: `Bearer ${token()}`, 'Content-Type': 'application/json' });

  // 14.1 Gateway Ingest
  const handleIngest = async () => {
    try {
      setIsProcessing(true);
      setErrorMessage(null);
      const res = await fetch('/api/v1/knowledge/gateway/ingest', {
        method: 'POST',
        headers: headers(),
        body: JSON.stringify({ title: ingestTitle, content_or_uri: ingestContent, asset_type: ingestType }),
      });
      const data = await res.json();
      setIngestResult(data);
    } catch (err: any) {
      setErrorMessage('Failed to ingest asset through Knowledge Gateway.');
    } finally {
      setIsProcessing(false);
    }
  };

  // 14.9 Enterprise RAG Query
  const handleRAGQuery = async () => {
    if (!question.trim()) return;
    try {
      setIsProcessing(true);
      setErrorMessage(null);
      const res = await fetch('/api/v1/knowledge/rag/query', {
        method: 'POST',
        headers: headers(),
        body: JSON.stringify({ query_text: question, top_k: 5, retrieval_strategy: 'hybrid' }),
      });
      const data = await res.json();
      setRagResult(data);
    } catch (err: any) {
      setErrorMessage('Failed to execute Enterprise RAG query.');
    } finally {
      setIsProcessing(false);
    }
  };

  // 14.2.5 Compiler
  const handleCompile = async () => {
    if (!ingestResult?.document_id) return alert('Ingest a document first.');
    try {
      setIsProcessing(true);
      const res = await fetch('/api/v1/knowledge/compiler/compile', {
        method: 'POST',
        headers: headers(),
        body: JSON.stringify({ document_id: ingestResult.document_id }),
      });
      const data = await res.json();
      setCompilerResult(data);
    } catch (err: any) {
      setErrorMessage('Compilation failed.');
    } finally {
      setIsProcessing(false);
    }
  };

  // 14.3 Entity & Relationship Extraction
  const handleExtractEntities = async () => {
    try {
      setIsProcessing(true);
      const res = await fetch('/api/v1/knowledge/relationship/extract', {
        method: 'POST',
        headers: headers(),
        body: JSON.stringify({ text: ingestContent, document_id: ingestResult?.document_id }),
      });
      const data = await res.json();
      setEntitiesResult(data.entities || []);
    } catch (err: any) {
      setErrorMessage('Entity extraction failed.');
    } finally {
      setIsProcessing(false);
    }
  };

  // 14.5 Graph Traversal
  const handleFetchGraph = async () => {
    try {
      setIsProcessing(true);
      const res = await fetch('/api/v1/knowledge/graph/traversal?start_node_id=node_001&strategy=bfs&max_hops=2', {
        headers: { Authorization: `Bearer ${token()}` },
      });
      const data = await res.json();
      setGraphResult(data);
    } catch (err: any) {
      setErrorMessage('Graph traversal failed.');
    } finally {
      setIsProcessing(false);
    }
  };

  // 14.6 Memory Recall
  const handleRecallMemory = async () => {
    try {
      setIsProcessing(true);
      const res = await fetch('/api/v1/knowledge/memory/recall?key=leadforge', {
        headers: { Authorization: `Bearer ${token()}` },
      });
      const data = await res.json();
      setMemoriesResult(data || []);
    } catch (err: any) {
      setErrorMessage('Memory recall failed.');
    } finally {
      setIsProcessing(false);
    }
  };

  // 14.6.5 Generate Embedding
  const handleGenerateEmbedding = async () => {
    try {
      setIsProcessing(true);
      const res = await fetch('/api/v1/knowledge/embeddings/generate', {
        method: 'POST',
        headers: headers(),
        body: JSON.stringify({ text: question, provider: 'openai' }),
      });
      const data = await res.json();
      setEmbeddingResult(data);
    } catch (err: any) {
      setErrorMessage('Embedding generation failed.');
    } finally {
      setIsProcessing(false);
    }
  };

  // 14.8.5 Generate Citation
  const handleGenerateCitation = async () => {
    try {
      setIsProcessing(true);
      const res = await fetch('/api/v1/knowledge/citations/generate', {
        method: 'POST',
        headers: headers(),
        body: JSON.stringify({
          source_id: 'src_doc_01',
          document_id: ingestResult?.document_id || 'doc_sample',
          snippet: 'LeadForgeAI integrates Enterprise Knowledge Fabric.',
          citation_type: 'chunk',
        }),
      });
      const data = await res.json();
      setCitationResult(data);
    } catch (err: any) {
      setErrorMessage('Citation generation failed.');
    } finally {
      setIsProcessing(false);
    }
  };

  // 14.9.5 Transition Lifecycle
  const handleTransitionLifecycle = async (targetState: string) => {
    if (!ingestResult?.document_id) return alert('Ingest a document first.');
    try {
      setIsProcessing(true);
      const res = await fetch('/api/v1/knowledge/lifecycle/transition', {
        method: 'POST',
        headers: headers(),
        body: JSON.stringify({ document_id: ingestResult.document_id, target_state: targetState }),
      });
      const data = await res.json();
      setLifecycleResult(data);
    } catch (err: any) {
      setErrorMessage('Lifecycle state transition failed.');
    } finally {
      setIsProcessing(false);
    }
  };

  // 14.10 Fetch Analytics Dashboard
  const handleFetchAnalytics = async () => {
    try {
      setIsProcessing(true);
      const res = await fetch('/api/v1/knowledge/analytics/dashboard', {
        headers: { Authorization: `Bearer ${token()}` },
      });
      const data = await res.json();
      setAnalyticsResult(data);
    } catch (err: any) {
      setErrorMessage('Analytics dashboard load failed.');
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans flex flex-col">
      {/* Top Header Navigation */}
      <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-8">
            <div className="flex items-center space-x-3 cursor-pointer" onClick={() => navigate('/leads')}>
              <div className="h-9 w-9 rounded-xl bg-gradient-to-tr from-cyan-500 via-teal-500 to-blue-500 flex items-center justify-center font-bold text-white shadow-lg shadow-cyan-500/25">
                LF
              </div>
              <span className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white via-slate-200 to-slate-400">
                LeadForgeAI
              </span>
            </div>

            <nav className="hidden md:flex items-center space-x-1">
              <Link to="/leads" className="px-3 py-2 rounded-lg text-sm font-medium text-slate-400 hover:text-white hover:bg-slate-800/50 transition">Leads</Link>
              <Link to="/knowledge" className="px-3 py-2 rounded-lg text-sm font-medium text-cyan-400 bg-cyan-500/10 border border-cyan-500/20">Knowledge Fabric</Link>
              <Link to="/knowledge/analytics" className="px-3 py-2 rounded-lg text-sm font-medium text-slate-400 hover:text-white hover:bg-slate-800/50 transition">📊 Analytics</Link>
            </nav>
          </div>

          <div className="flex items-center space-x-4">
            <span className="text-xs text-slate-400 hidden sm:inline">{user?.email}</span>
            <button onClick={() => logout()} className="text-xs px-3 py-1.5 rounded-lg border border-slate-700 text-slate-300 hover:bg-slate-800 hover:text-white transition">
              Logout
            </button>
          </div>
        </div>
      </header>

      {/* Main Workspace Layout */}
      <div className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8 flex flex-col space-y-6">
        
        {/* Banner */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-extrabold text-white tracking-tight flex items-center space-x-3">
              <span>Enterprise Knowledge Fabric</span>
              <span className="text-xs px-2.5 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 font-mono">
                Phase 14 Central Intelligence
              </span>
            </h1>
            <p className="text-xs text-slate-400 mt-1">
              Central Intelligence Layer transforming CRM, Voice, Meetings, Documents, and Research into structured Knowledge Objects.
            </p>
          </div>

          <button onClick={() => navigate('/knowledge/analytics')} className="px-4 py-2 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-semibold text-xs transition shadow-lg shadow-cyan-500/20">
            📊 View Full Analytics Dashboard
          </button>
        </div>

        {errorMessage && (
          <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs">
            ⚠️ {errorMessage}
          </div>
        )}

        {/* 10 Tool Navigation Tabs */}
        <div className="border-b border-slate-800 flex space-x-1 overflow-x-auto pb-1 custom-scrollbar">
          {[
            { id: 'rag', label: '🤖 Hybrid RAG' },
            { id: 'gateway', label: '🚪 Gateway Monitor' },
            { id: 'compiler', label: '📦 Compiler Inspector' },
            { id: 'entity', label: '👤 Entity & Relation' },
            { id: 'graph', label: '🕸️ Knowledge Graph' },
            { id: 'memory', label: '🧠 Memory Inspector' },
            { id: 'embeddings', label: '⚡ Embedding Manager' },
            { id: 'citations', label: '📌 Citation Viewer' },
            { id: 'lifecycle', label: '🔄 Lifecycle Dashboard' },
            { id: 'analytics', label: '📊 Analytics' },
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => {
                setActiveTab(tab.id as any);
                if (tab.id === 'graph') handleFetchGraph();
                if (tab.id === 'memory') handleRecallMemory();
                if (tab.id === 'analytics') handleFetchAnalytics();
              }}
              className={`px-3.5 py-2 text-xs font-semibold rounded-xl transition whitespace-nowrap ${
                activeTab === tab.id
                  ? 'bg-cyan-600 text-white shadow-lg shadow-cyan-500/20'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800/40'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* TAB: RAG CONSOLE */}
        {activeTab === 'rag' && (
          <div className="space-y-6">
            <div className="bg-slate-900/40 border border-slate-800 p-5 rounded-2xl space-y-4">
              <h3 className="text-sm font-bold text-cyan-400 uppercase">Hybrid RAG Query Console</h3>
              <div className="flex gap-3">
                <input
                  type="text"
                  value={question}
                  onChange={e => setQuestion(e.target.value)}
                  className="flex-1 bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-slate-100"
                />
                <button onClick={handleRAGQuery} disabled={isProcessing} className="px-5 py-2.5 rounded-xl bg-cyan-600 hover:bg-cyan-500 font-semibold text-xs text-white">
                  {isProcessing ? 'Reasoning...' : 'Execute RAG'}
                </button>
              </div>
            </div>

            {ragResult && (
              <div className="bg-slate-900/60 border border-slate-800 p-6 rounded-2xl space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-xs font-bold text-emerald-400">Grounded Answer</span>
                  <span className="text-xs px-2.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 font-mono">
                    Hallucination Score: {ragResult.hallucination_score}
                  </span>
                </div>
                <div className="text-sm text-slate-200 leading-relaxed whitespace-pre-wrap">{ragResult.answer_text}</div>

                <div className="pt-3 border-t border-slate-800">
                  <h4 className="text-xs font-bold text-slate-400 uppercase mb-2">Citations ({ragResult.citations?.length || 0})</h4>
                  <div className="space-y-2">
                    {(ragResult.citations || []).map((c: any, i: number) => (
                      <div key={i} className="p-3 bg-slate-950 rounded-xl border border-slate-900 text-xs text-slate-300">
                        <span className="text-cyan-400 font-mono font-bold">[{c.citation_index || i+1}]</span> Doc: {c.document_id} — {c.snippet}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* TAB: GATEWAY MONITOR */}
        {activeTab === 'gateway' && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-slate-900/40 border border-slate-800 p-5 rounded-2xl space-y-4">
              <h3 className="text-sm font-bold text-cyan-400 uppercase">14.1 Knowledge Gateway Ingestion</h3>
              <div>
                <label className="text-xs text-slate-400 block mb-1">Asset Title</label>
                <input value={ingestTitle} onChange={e => setIngestTitle(e.target.value)} className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-xs text-slate-100" />
              </div>
              <div>
                <label className="text-xs text-slate-400 block mb-1">Asset Type</label>
                <select value={ingestType} onChange={e => setIngestType(e.target.value)} className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-xs text-slate-300">
                  {['crm', 'voice', 'meetings', 'emails', 'pdf', 'word', 'excel', 'csv', 'json', 'markdown', 'web_url', 'research', 'manual_notes'].map(t => (
                    <option key={t} value={t}>{t.toUpperCase()}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="text-xs text-slate-400 block mb-1">Asset Content / Payload</label>
                <textarea value={ingestContent} onChange={e => setIngestContent(e.target.value)} className="w-full h-24 bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-xs text-slate-100" />
              </div>
              <button onClick={handleIngest} disabled={isProcessing} className="w-full py-2.5 rounded-xl bg-cyan-600 hover:bg-cyan-500 font-semibold text-xs text-white">
                📥 Ingest Asset into Knowledge Fabric
              </button>
            </div>

            <div className="bg-slate-900/40 border border-slate-800 p-5 rounded-2xl space-y-4">
              <h3 className="text-sm font-bold text-cyan-400 uppercase">Ingestion Status & Validation</h3>
              {ingestResult ? (
                <div className="bg-slate-950 p-4 rounded-xl border border-emerald-500/30 text-xs space-y-2">
                  <div className="text-emerald-400 font-bold">✅ Knowledge Object Created</div>
                  <div>ID: <span className="font-mono text-cyan-400">{ingestResult.document_id}</span></div>
                  <div>Title: <span className="text-slate-200">{ingestResult.title}</span></div>
                  <div>Security Scan: <span className="text-emerald-400 font-bold">{String(ingestResult.virus_scan_passed)}</span></div>
                </div>
              ) : <div className="text-xs text-slate-500 py-8 text-center">Ingest an asset using the form.</div>}
            </div>
          </div>
        )}

        {/* TAB: COMPILER INSPECTOR */}
        {activeTab === 'compiler' && (
          <div className="bg-slate-900/40 border border-slate-800 p-5 rounded-2xl space-y-4">
            <h3 className="text-sm font-bold text-cyan-400 uppercase">14.2.5 Enterprise Knowledge Compiler</h3>
            <button onClick={handleCompile} disabled={isProcessing} className="px-4 py-2 rounded-xl bg-cyan-600 text-xs font-semibold text-white">
              ⚙️ Compile Ingested Document
            </button>
            {compilerResult && (
              <div className="p-4 bg-slate-950 rounded-xl border border-slate-800 text-xs space-y-2 font-mono">
                <div>Object ID: <span className="text-cyan-400">{compilerResult.object_id}</span></div>
                <div>Checksum: <span className="text-emerald-400">{compilerResult.checksum}</span></div>
                <div>Version: {compilerResult.version}</div>
                <div>Language: {compilerResult.language}</div>
              </div>
            )}
          </div>
        )}

        {/* TAB: ENTITY & RELATION */}
        {activeTab === 'entity' && (
          <div className="bg-slate-900/40 border border-slate-800 p-5 rounded-2xl space-y-4">
            <h3 className="text-sm font-bold text-cyan-400 uppercase">14.3 & 14.4 Entity & Relationship Extraction</h3>
            <button onClick={handleExtractEntities} disabled={isProcessing} className="px-4 py-2 rounded-xl bg-cyan-600 text-xs font-semibold text-white">
              🔍 Extract Entities & Relationships
            </button>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
              {entitiesResult.map((e, idx) => (
                <div key={idx} className="p-3 bg-slate-950 rounded-xl border border-slate-800 text-xs flex justify-between items-center">
                  <div>
                    <div className="font-bold text-white">{e.name}</div>
                    <div className="text-[10px] text-slate-400">Canonical: {e.canonical_name}</div>
                  </div>
                  <span className="px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-400 font-mono text-[10px]">
                    {e.entity_type}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* TAB: KNOWLEDGE GRAPH */}
        {activeTab === 'graph' && (
          <div className="bg-slate-900/40 border border-slate-800 p-5 rounded-2xl space-y-4">
            <h3 className="text-sm font-bold text-cyan-400 uppercase">14.5 Enterprise Knowledge Graph Traversal</h3>
            {graphResult ? (
              <div className="p-4 bg-slate-950 rounded-xl border border-slate-800 text-xs space-y-3 font-mono">
                <div>Strategy: {graphResult.strategy} | Max Hops: {graphResult.max_hops}</div>
                <div>Nodes Traversed: <strong className="text-cyan-400">{graphResult.nodes_count}</strong></div>
                <div>Edges Traversed: <strong className="text-emerald-400">{graphResult.edges_count}</strong></div>
              </div>
            ) : <div className="text-xs text-slate-500 py-8 text-center">Loading graph traversal...</div>}
          </div>
        )}

        {/* TAB: MEMORY INSPECTOR */}
        {activeTab === 'memory' && (
          <div className="bg-slate-900/40 border border-slate-800 p-5 rounded-2xl space-y-4">
            <h3 className="text-sm font-bold text-cyan-400 uppercase">14.6 Unified Enterprise Memory (4-Tier)</h3>
            <div className="space-y-2">
              {memoriesResult.map((m, idx) => (
                <div key={idx} className="p-3 bg-slate-950 rounded-xl border border-slate-800 text-xs flex justify-between items-center">
                  <div>
                    <span className="font-bold text-purple-400">[{m.memory_type?.toUpperCase()}]</span> <span className="text-white font-bold">{m.key}</span>
                    <div className="text-slate-300 mt-0.5">{m.value}</div>
                  </div>
                  <span className="text-[10px] text-slate-500 font-mono">Confidence: {m.confidence}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* TAB: EMBEDDINGS */}
        {activeTab === 'embeddings' && (
          <div className="bg-slate-900/40 border border-slate-800 p-5 rounded-2xl space-y-4">
            <h3 className="text-sm font-bold text-cyan-400 uppercase">14.6.5 Embedding Orchestrator</h3>
            <button onClick={handleGenerateEmbedding} disabled={isProcessing} className="px-4 py-2 rounded-xl bg-cyan-600 text-xs font-semibold text-white">
              ⚡ Generate Vector Embedding
            </button>
            {embeddingResult && (
              <div className="p-4 bg-slate-950 rounded-xl border border-slate-800 text-xs space-y-2 font-mono">
                <div>Provider: <span className="text-cyan-400">{embeddingResult.provider}</span></div>
                <div>Vector Dimensions: <span className="text-emerald-400">{embeddingResult.dimensions}</span></div>
                <div>Vector Preview: {JSON.stringify(embeddingResult.embedding)}</div>
              </div>
            )}
          </div>
        )}

        {/* TAB: CITATIONS */}
        {activeTab === 'citations' && (
          <div className="bg-slate-900/40 border border-slate-800 p-5 rounded-2xl space-y-4">
            <h3 className="text-sm font-bold text-cyan-400 uppercase">14.8.5 Citation Engine</h3>
            <button onClick={handleGenerateCitation} disabled={isProcessing} className="px-4 py-2 rounded-xl bg-cyan-600 text-xs font-semibold text-white">
              📌 Generate Evidence Citation
            </button>
            {citationResult && (
              <div className="p-4 bg-slate-950 rounded-xl border border-slate-800 text-xs space-y-2 font-mono">
                <div>Citation ID: <span className="text-cyan-400">{citationResult.citation_id}</span></div>
                <div>Type: {citationResult.citation_type}</div>
                <div>Snippet: {citationResult.snippet}</div>
              </div>
            )}
          </div>
        )}

        {/* TAB: LIFECYCLE */}
        {activeTab === 'lifecycle' && (
          <div className="bg-slate-900/40 border border-slate-800 p-5 rounded-2xl space-y-4">
            <h3 className="text-sm font-bold text-cyan-400 uppercase">14.9.5 Knowledge Lifecycle Manager</h3>
            <div className="flex gap-2">
              {['Active', 'Archived', 'Deleted'].map(st => (
                <button key={st} onClick={() => handleTransitionLifecycle(st)} className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-200 rounded-lg">
                  Set State: {st}
                </button>
              ))}
            </div>
            {lifecycleResult && (
              <div className="p-4 bg-slate-950 rounded-xl border border-slate-800 text-xs space-y-2 font-mono">
                <div>Lifecycle ID: {lifecycleResult.lifecycle_id}</div>
                <div>Current State: <span className="text-emerald-400 font-bold">{lifecycleResult.state}</span></div>
                <div>Legal Hold: {String(lifecycleResult.is_legal_hold)}</div>
              </div>
            )}
          </div>
        )}

        {/* TAB: ANALYTICS */}
        {activeTab === 'analytics' && (
          <div className="bg-slate-900/40 border border-slate-800 p-5 rounded-2xl space-y-4">
            <h3 className="text-sm font-bold text-cyan-400 uppercase">14.10 Knowledge Analytics & OpenTelemetry</h3>
            {analyticsResult ? (
              <div className="p-4 bg-slate-950 rounded-xl border border-slate-800 text-xs space-y-2 font-mono">
                <div>Events: {analyticsResult.kpis?.total_events}</div>
                <div>Avg Latency: {analyticsResult.kpis?.avg_latency_ms}ms</div>
                <div>Precision: {analyticsResult.kpis?.avg_precision}</div>
                <div>Total Cost: ${analyticsResult.kpis?.total_cost_usd}</div>
              </div>
            ) : <div className="text-xs text-slate-500 py-8 text-center">Loading analytics dashboard...</div>}
          </div>
        )}

      </div>
    </div>
  );
};

export default KnowledgeCenterPage;
