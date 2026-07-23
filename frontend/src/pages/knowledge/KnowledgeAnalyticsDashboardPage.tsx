import React, { useEffect, useState, useCallback } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "../../contexts/AuthContext";

interface KnowledgeKPIs {
  total_events: number;
  avg_latency_ms: number;
  avg_precision: number;
  total_cost_usd: number;
  active_alerts: number;
}

interface KnowledgeEvent {
  event_id: string;
  event_type: string;
  latency_ms: number;
  precision_score: number;
  recall_score: number;
  cost_usd: number;
  cache_hit: boolean;
  timestamp: string;
}

interface KnowledgeAlert {
  alert_id: string;
  metric_name: string;
  metric_value: number;
  threshold_value: number;
  severity: string;
  message: string;
  resolved: boolean;
  triggered_at: string;
}

interface DailyRollup {
  date_key: string;
  total_queries: number;
  total_ingestions: number;
  avg_latency_ms: number;
  avg_precision: number;
  cache_hit_rate: number;
  total_cost_usd: number;
}

interface RAGQuery {
  query_id: string;
  query_text: string;
  retrieval_strategy: string;
  answer_text: string;
  hallucination_score: number;
  latency_ms: number;
  created_at: string;
}

interface DashboardData {
  kpis: KnowledgeKPIs;
  recent_events: KnowledgeEvent[];
  active_alerts: KnowledgeAlert[];
  daily_rollups: DailyRollup[];
  recent_rag_queries: RAGQuery[];
  generated_at: string;
}

const badge = (label: string, color = "#a5b4fc", bg = "rgba(99,102,241,0.15)") => (
  <span style={{ fontSize: "0.7rem", padding: "0.15rem 0.5rem", borderRadius: "100px", background: bg, color, fontWeight: 700 }}>
    {label}
  </span>
);

export const KnowledgeAnalyticsDashboardPage: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const [activeTab, setActiveTab] = useState<"overview" | "gateway" | "graph" | "memory" | "export">("overview");
  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // Ingestion form state
  const [ingestTitle, setIngestTitle] = useState("Enterprise AI Guidelines");
  const [ingestContent, setIngestContent] = useState("LeadForgeAI uses multi-modal RAG with graph reasoning.");
  const [ingestType, setIngestType] = useState("pdf");
  const [ingestResult, setIngestResult] = useState<any>(null);

  // RAG tester state
  const [ragQuery, setRagQuery] = useState("What technologies are used in LeadForgeAI?");
  const [ragResult, setRagResult] = useState<any>(null);
  const [isQueryingRAG, setIsQueryingRAG] = useState(false);

  // Memory state
  const [memKey, setMemKey] = useState("user_preference_model");
  const [memVal, setMemVal] = useState("Prefers Claude Sonnet 4.6 for complex reasoning");
  const [memTier, setMemTier] = useState("semantic");
  const [recalledMemories, setRecalledMemories] = useState<any[]>([]);

  // Export state
  const [exportFormat, setExportFormat] = useState("csv");
  const [exportDoc, setExportDoc] = useState<any>(null);

  const token = () => localStorage.getItem("access_token");
  const headers = () => ({ Authorization: `Bearer ${token()}`, "Content-Type": "application/json" });

  const fetchDashboard = useCallback(async () => {
    try {
      const res = await fetch("/api/v1/knowledge/analytics/dashboard", { headers: { Authorization: `Bearer ${token()}` } });
      const data = await res.json();
      setDashboard(data);
    } catch (e) {
      console.error("Dashboard load error", e);
    }
  }, []);

  const loadAll = useCallback(async () => {
    setIsLoading(true);
    await fetchDashboard();
    setIsLoading(false);
  }, [fetchDashboard]);

  useEffect(() => { loadAll(); }, [loadAll]);

  const handleIngest = async () => {
    try {
      const res = await fetch("/api/v1/knowledge/gateway/ingest", {
        method: "POST",
        headers: headers(),
        body: JSON.stringify({ title: ingestTitle, content_or_uri: ingestContent, file_type: ingestType }),
      });
      const data = await res.json();
      setIngestResult(data);
      await fetchDashboard();
    } catch (e) {
      console.error(e);
    }
  };

  const handleExecuteRAG = async () => {
    setIsQueryingRAG(true);
    try {
      const res = await fetch("/api/v1/knowledge/rag/query", {
        method: "POST",
        headers: headers(),
        body: JSON.stringify({ query_text: ragQuery, top_k: 5, retrieval_strategy: "hybrid" }),
      });
      const data = await res.json();
      setRagResult(data);
      await fetchDashboard();
    } catch (e) {
      console.error(e);
    } finally {
      setIsQueryingRAG(false);
    }
  };

  const handleStoreMemory = async () => {
    try {
      await fetch("/api/v1/knowledge/memory/store", {
        method: "POST",
        headers: headers(),
        body: JSON.stringify({ key: memKey, value: memVal, memory_tier: memTier }),
      });
      handleRecallMemory();
    } catch (e) {
      console.error(e);
    }
  };

  const handleRecallMemory = async () => {
    try {
      const res = await fetch(`/api/v1/knowledge/memory/recall?key=${encodeURIComponent(memKey)}`, {
        headers: { Authorization: `Bearer ${token()}` },
      });
      const data = await res.json();
      setRecalledMemories(Array.isArray(data) ? data : []);
    } catch (e) {
      console.error(e);
    }
  };

  const handleExport = async () => {
    try {
      const res = await fetch("/api/v1/knowledge/analytics/export", {
        method: "POST",
        headers: headers(),
        body: JSON.stringify({ format: exportFormat }),
      });
      const data = await res.json();
      setExportDoc(data);
    } catch (e) {
      console.error(e);
    }
  };

  const kpis = dashboard?.kpis;

  return (
    <div style={{ minHeight: "100vh", background: "#090d16", color: "#e2e8f0", fontFamily: "'Inter', sans-serif", display: "flex", flexDirection: "column" }}>
      {/* Navigation Bar */}
      <nav style={{ background: "rgba(15,23,42,0.95)", borderBottom: "1px solid rgba(6,182,212,0.2)", padding: "0 2rem", height: "60px", display: "flex", alignItems: "center", justifyContent: "space-between", backdropFilter: "blur(12px)", position: "sticky", top: 0, zIndex: 100 }}>
        <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
          <div onClick={() => navigate("/leads")} style={{ fontSize: "1.4rem", fontWeight: 800, background: "linear-gradient(135deg, #06b6d4, #3b82f6)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent", cursor: "pointer" }}>
            LeadForgeAI
          </div>
          <div style={{ color: "#64748b", fontSize: "0.85rem" }}>/ Knowledge Architecture & RAG Analytics</div>
          {badge("Phase 14", "#06b6d4", "rgba(6,182,212,0.15)")}
        </div>

        <div style={{ display: "flex", gap: "0.4rem" }}>
          {(["overview", "gateway", "graph", "memory", "export"] as const).map(tab => (
            <button key={tab} onClick={() => setActiveTab(tab)} style={{
              padding: "0.4rem 0.85rem", borderRadius: "6px", fontSize: "0.8rem", fontWeight: 600, cursor: "pointer",
              border: activeTab === tab ? "1px solid #06b6d4" : "1px solid transparent",
              background: activeTab === tab ? "rgba(6,182,212,0.18)" : "none",
              color: activeTab === tab ? "#22d3ee" : "#94a3b8",
            }}>
              {tab === "overview" ? "📊 Overview" : tab === "gateway" ? "🚪 Gateway" : tab === "graph" ? "🕸️ Graph & RAG" : tab === "memory" ? "🧠 Memory" : "📤 Export"}
            </button>
          ))}
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
          <span style={{ color: "#64748b", fontSize: "0.8rem" }}>{user?.email}</span>
          <Link to="/knowledge" style={{ color: "#a5b4fc", fontSize: "0.85rem", textDecoration: "none" }}>📚 Knowledge Center</Link>
          <button onClick={() => logout()} style={{ background: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.3)", color: "#f87171", padding: "0.35rem 0.85rem", borderRadius: "6px", cursor: "pointer", fontSize: "0.8rem" }}>Logout</button>
        </div>
      </nav>

      <main style={{ flex: 1, padding: "2rem", display: "flex", flexDirection: "column", gap: "1.5rem", maxWidth: "1600px", margin: "0 auto", width: "100%", boxSizing: "border-box" }}>

        {isLoading ? (
          <div style={{ textAlign: "center", padding: "4rem", color: "#64748b" }}>⏳ Loading Knowledge Analytics...</div>
        ) : (
          <>
            {/* Header Banner */}
            <div style={{ background: "linear-gradient(135deg, rgba(6,182,212,0.12), rgba(59,130,246,0.06))", border: "1px solid rgba(6,182,212,0.25)", borderRadius: "16px", padding: "1.5rem 2rem", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div>
                <h1 style={{ margin: 0, fontSize: "1.5rem", fontWeight: 800, background: "linear-gradient(135deg, #22d3ee, #60a5fa)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
                  🧠 Enterprise Knowledge & Advanced RAG Platform
                </h1>
                <p style={{ margin: "0.3rem 0 0", color: "#94a3b8", fontSize: "0.88rem" }}>
                  Sub-phases 14.1 - 14.10: Ingestion Gateway · Normalization · Entity & Relationship Graph · 4-Tier Memory · Hybrid RAG
                </p>
              </div>
              <div style={{ display: "flex", gap: "0.5rem" }}>
                {badge(`${kpis?.total_events || 0} Events`, "#22d3ee")}
                {badge(`$${kpis?.total_cost_usd?.toFixed(4) || "0.0000"}`, "#fbbf24", "rgba(251,191,36,0.12)")}
                {badge(`Precision: ${((kpis?.avg_precision || 1) * 100).toFixed(1)}%`, "#34d399", "rgba(52,211,153,0.12)")}
              </div>
            </div>

            {/* TAB 1: OVERVIEW */}
            {activeTab === "overview" && (
              <>
                {/* KPI Cards */}
                <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "1rem" }}>
                  <div style={{ background: "rgba(15,23,42,0.9)", border: "1px solid rgba(6,182,212,0.25)", borderRadius: "14px", padding: "1.25rem" }}>
                    <div style={{ fontSize: "0.75rem", color: "#64748b", fontWeight: 700, textTransform: "uppercase" }}>Avg Query Latency</div>
                    <div style={{ fontSize: "1.8rem", fontWeight: 800, color: "#22d3ee", marginTop: "0.2rem" }}>{kpis?.avg_latency_ms?.toFixed(1)} <span style={{ fontSize: "0.8rem", color: "#64748b" }}>ms</span></div>
                    <div style={{ fontSize: "0.72rem", color: "#475569", marginTop: "0.2rem" }}>Hybrid Dense + Sparse + Graph</div>
                  </div>

                  <div style={{ background: "rgba(15,23,42,0.9)", border: "1px solid rgba(52,211,153,0.25)", borderRadius: "14px", padding: "1.25rem" }}>
                    <div style={{ fontSize: "0.75rem", color: "#64748b", fontWeight: 700, textTransform: "uppercase" }}>Retrieval Precision</div>
                    <div style={{ fontSize: "1.8rem", fontWeight: 800, color: "#34d399", marginTop: "0.2rem" }}>{((kpis?.avg_precision || 1) * 100).toFixed(1)}%</div>
                    <div style={{ fontSize: "0.72rem", color: "#475569", marginTop: "0.2rem" }}>Zero-hallucination benchmark</div>
                  </div>

                  <div style={{ background: "rgba(15,23,42,0.9)", border: "1px solid rgba(251,191,36,0.25)", borderRadius: "14px", padding: "1.25rem" }}>
                    <div style={{ fontSize: "0.75rem", color: "#64748b", fontWeight: 700, textTransform: "uppercase" }}>Total RAG Cost</div>
                    <div style={{ fontSize: "1.8rem", fontWeight: 800, color: "#fbbf24", marginTop: "0.2rem" }}>${kpis?.total_cost_usd?.toFixed(4)}</div>
                    <div style={{ fontSize: "0.72rem", color: "#475569", marginTop: "0.2rem" }}>Cumulative retrieval & reasoning</div>
                  </div>

                  <div style={{ background: "rgba(15,23,42,0.9)", border: "1px solid rgba(248,113,113,0.25)", borderRadius: "14px", padding: "1.25rem" }}>
                    <div style={{ fontSize: "0.75rem", color: "#64748b", fontWeight: 700, textTransform: "uppercase" }}>Active Alerts</div>
                    <div style={{ fontSize: "1.8rem", fontWeight: 800, color: kpis?.active_alerts ? "#f87171" : "#34d399", marginTop: "0.2rem" }}>{kpis?.active_alerts || 0}</div>
                    <div style={{ fontSize: "0.72rem", color: "#475569", marginTop: "0.2rem" }}>Metric threshold breaches</div>
                  </div>
                </div>

                {/* Daily Rollups & Recent Queries */}
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.5rem" }}>
                  <div style={{ background: "rgba(15,23,42,0.9)", border: "1px solid rgba(6,182,212,0.2)", borderRadius: "14px", padding: "1.5rem" }}>
                    <h3 style={{ margin: "0 0 1rem", fontSize: "1rem", fontWeight: 700, color: "#22d3ee" }}>📅 Daily Rollup Analytics</h3>
                    {dashboard?.daily_rollups && dashboard.daily_rollups.length > 0 ? (
                      <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.8rem" }}>
                        <thead>
                          <tr style={{ borderBottom: "1px solid rgba(255,255,255,0.08)" }}>
                            <th style={{ padding: "0.4rem", textAlign: "left", color: "#64748b" }}>Date</th>
                            <th style={{ padding: "0.4rem", textAlign: "left", color: "#64748b" }}>Queries</th>
                            <th style={{ padding: "0.4rem", textAlign: "left", color: "#64748b" }}>Avg Latency</th>
                            <th style={{ padding: "0.4rem", textAlign: "left", color: "#64748b" }}>Hit Rate</th>
                          </tr>
                        </thead>
                        <tbody>
                          {dashboard.daily_rollups.map((d, idx) => (
                            <tr key={idx} style={{ borderBottom: "1px solid rgba(255,255,255,0.04)" }}>
                              <td style={{ padding: "0.4rem", color: "#94a3b8" }}>{d.date_key}</td>
                              <td style={{ padding: "0.4rem", color: "#e2e8f0", fontWeight: 700 }}>{d.total_queries}</td>
                              <td style={{ padding: "0.4rem", color: "#22d3ee" }}>{d.avg_latency_ms}ms</td>
                              <td style={{ padding: "0.4rem", color: "#34d399" }}>{d.cache_hit_rate}%</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    ) : <div style={{ color: "#475569", fontSize: "0.85rem" }}>No daily rollups recorded.</div>}
                  </div>

                  <div style={{ background: "rgba(15,23,42,0.9)", border: "1px solid rgba(99,102,241,0.2)", borderRadius: "14px", padding: "1.5rem" }}>
                    <h3 style={{ margin: "0 0 1rem", fontSize: "1rem", fontWeight: 700, color: "#a5b4fc" }}>💬 Recent RAG Execution Logs</h3>
                    {dashboard?.recent_rag_queries && dashboard.recent_rag_queries.length > 0 ? (
                      <div style={{ display: "flex", flexDirection: "column", gap: "0.6rem" }}>
                        {dashboard.recent_rag_queries.map((q, idx) => (
                          <div key={idx} style={{ background: "rgba(10,15,30,0.8)", border: "1px solid rgba(255,255,255,0.05)", borderRadius: "8px", padding: "0.75rem", fontSize: "0.8rem" }}>
                            <div style={{ color: "#e2e8f0", fontWeight: 700 }}>"{q.query_text}"</div>
                            <div style={{ color: "#94a3b8", marginTop: "0.2rem" }}>{q.answer_text}</div>
                            <div style={{ display: "flex", gap: "0.8rem", marginTop: "0.4rem", fontSize: "0.72rem", color: "#64748b" }}>
                              <span>Strategy: <strong style={{ color: "#22d3ee" }}>{q.retrieval_strategy}</strong></span>
                              <span>Latency: <strong style={{ color: "#34d399" }}>{q.latency_ms}ms</strong></span>
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : <div style={{ color: "#475569", fontSize: "0.85rem" }}>No recent RAG queries logged.</div>}
                  </div>
                </div>
              </>
            )}

            {/* TAB 2: GATEWAY */}
            {activeTab === "gateway" && (
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.5rem" }}>
                <div style={{ background: "rgba(15,23,42,0.9)", border: "1px solid rgba(6,182,212,0.25)", borderRadius: "14px", padding: "1.5rem", display: "flex", flexDirection: "column", gap: "1rem" }}>
                  <h3 style={{ margin: 0, color: "#22d3ee", fontWeight: 700 }}>🚪 Enterprise Knowledge Gateway (14.1)</h3>
                  <div>
                    <label style={{ fontSize: "0.8rem", color: "#94a3b8", display: "block", marginBottom: "0.3rem" }}>Document Title</label>
                    <input value={ingestTitle} onChange={e => setIngestTitle(e.target.value)} style={{ width: "100%", background: "rgba(10,15,30,0.8)", border: "1px solid rgba(6,182,212,0.3)", color: "#e2e8f0", padding: "0.5rem", borderRadius: "6px", fontSize: "0.85rem", boxSizing: "border-box" }} />
                  </div>

                  <div>
                    <label style={{ fontSize: "0.8rem", color: "#94a3b8", display: "block", marginBottom: "0.3rem" }}>File Type</label>
                    <select value={ingestType} onChange={e => setIngestType(e.target.value)} style={{ width: "100%", background: "rgba(10,15,30,0.8)", border: "1px solid rgba(6,182,212,0.3)", color: "#e2e8f0", padding: "0.5rem", borderRadius: "6px", fontSize: "0.85rem" }}>
                      {["pdf", "docx", "csv", "json", "markdown", "web_url", "raw_text"].map(t => <option key={t} value={t}>{t.toUpperCase()}</option>)}
                    </select>
                  </div>

                  <div>
                    <label style={{ fontSize: "0.8rem", color: "#94a3b8", display: "block", marginBottom: "0.3rem" }}>Document Content / Source URI</label>
                    <textarea value={ingestContent} onChange={e => setIngestContent(e.target.value)} style={{ width: "100%", height: "100px", background: "rgba(10,15,30,0.8)", border: "1px solid rgba(6,182,212,0.3)", color: "#e2e8f0", padding: "0.5rem", borderRadius: "6px", fontSize: "0.85rem", boxSizing: "border-box" }} />
                  </div>

                  <button onClick={handleIngest} style={{ padding: "0.65rem", borderRadius: "8px", border: "none", background: "linear-gradient(135deg, #06b6d4, #3b82f6)", color: "#fff", fontWeight: 700, fontSize: "0.9rem", cursor: "pointer" }}>
                    📥 Ingest Document
                  </button>
                </div>

                <div style={{ background: "rgba(15,23,42,0.9)", border: "1px solid rgba(6,182,212,0.25)", borderRadius: "14px", padding: "1.5rem" }}>
                  <h3 style={{ margin: "0 0 1rem", color: "#22d3ee", fontWeight: 700 }}>📄 Ingestion Result</h3>
                  {ingestResult ? (
                    <div style={{ background: "rgba(10,15,30,0.8)", border: "1px solid rgba(52,211,153,0.3)", borderRadius: "8px", padding: "1rem", fontSize: "0.82rem", color: "#94a3b8" }}>
                      <div style={{ color: "#34d399", fontWeight: 700, marginBottom: "0.4rem" }}>✅ Document Ingested & Validated</div>
                      <div>Doc ID: <span style={{ color: "#22d3ee", fontFamily: "monospace" }}>{ingestResult.document_id}</span></div>
                      <div>Title: <span style={{ color: "#fff" }}>{ingestResult.title}</span></div>
                      <div>Security ACL: <span style={{ color: "#a5b4fc" }}>{(ingestResult.security_acl || []).join(", ")}</span></div>
                      <div>Virus Scan Passed: <span style={{ color: "#34d399" }}>{String(ingestResult.virus_scan_passed)}</span></div>
                    </div>
                  ) : <div style={{ color: "#475569", fontSize: "0.85rem" }}>Ingest a document using the left panel.</div>}
                </div>
              </div>
            )}

            {/* TAB 3: GRAPH & RAG */}
            {activeTab === "graph" && (
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.5rem" }}>
                <div style={{ background: "rgba(15,23,42,0.9)", border: "1px solid rgba(59,130,246,0.25)", borderRadius: "14px", padding: "1.5rem", display: "flex", flexDirection: "column", gap: "1rem" }}>
                  <h3 style={{ margin: 0, color: "#60a5fa", fontWeight: 700 }}>🤖 Enterprise RAG Tester (14.9)</h3>
                  <textarea value={ragQuery} onChange={e => setRagQuery(e.target.value)} style={{ width: "100%", height: "80px", background: "rgba(10,15,30,0.8)", border: "1px solid rgba(59,130,246,0.3)", color: "#e2e8f0", padding: "0.5rem", borderRadius: "6px", fontSize: "0.85rem", boxSizing: "border-box" }} />
                  <button onClick={handleExecuteRAG} disabled={isQueryingRAG} style={{ padding: "0.65rem", borderRadius: "8px", border: "none", background: "linear-gradient(135deg, #3b82f6, #6366f1)", color: "#fff", fontWeight: 700, fontSize: "0.9rem", cursor: "pointer" }}>
                    {isQueryingRAG ? "⏳ Reason & Retrieve..." : "🔍 Execute Hybrid RAG Query"}
                  </button>
                </div>

                <div style={{ background: "rgba(15,23,42,0.9)", border: "1px solid rgba(59,130,246,0.25)", borderRadius: "14px", padding: "1.5rem" }}>
                  <h3 style={{ margin: "0 0 1rem", color: "#60a5fa", fontWeight: 700 }}>💡 RAG Output & Citations</h3>
                  {ragResult ? (
                    <div style={{ background: "rgba(10,15,30,0.8)", border: "1px solid rgba(99,102,241,0.3)", borderRadius: "8px", padding: "1rem", fontSize: "0.82rem", display: "flex", flexDirection: "column", gap: "0.6rem" }}>
                      <div style={{ color: "#34d399", fontWeight: 700 }}>Answer:</div>
                      <div style={{ color: "#fff", fontSize: "0.9rem" }}>{ragResult.answer_text}</div>
                      <div style={{ borderTop: "1px solid rgba(255,255,255,0.05)", paddingTop: "0.4rem" }}>
                        <div style={{ color: "#a5b4fc", fontWeight: 700, marginBottom: "0.3rem" }}>Sources / Citations:</div>
                        {(ragResult.citations || []).map((c: any, i: number) => (
                          <div key={i} style={{ color: "#94a3b8", fontSize: "0.78rem" }}>
                            [{c.citation_index}] Document: <span style={{ color: "#22d3ee" }}>{c.document_id}</span> — {c.snippet}
                          </div>
                        ))}
                      </div>
                    </div>
                  ) : <div style={{ color: "#475569", fontSize: "0.85rem" }}>Execute a query on the left panel.</div>}
                </div>
              </div>
            )}

            {/* TAB 4: MEMORY */}
            {activeTab === "memory" && (
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.5rem" }}>
                <div style={{ background: "rgba(15,23,42,0.9)", border: "1px solid rgba(168,85,247,0.25)", borderRadius: "14px", padding: "1.5rem", display: "flex", flexDirection: "column", gap: "1rem" }}>
                  <h3 style={{ margin: 0, color: "#c084fc", fontWeight: 700 }}>🧠 Unified 4-Tier Memory (14.6)</h3>
                  <div>
                    <label style={{ fontSize: "0.8rem", color: "#94a3b8", display: "block", marginBottom: "0.3rem" }}>Memory Key</label>
                    <input value={memKey} onChange={e => setMemKey(e.target.value)} style={{ width: "100%", background: "rgba(10,15,30,0.8)", border: "1px solid rgba(168,85,247,0.3)", color: "#e2e8f0", padding: "0.5rem", borderRadius: "6px", fontSize: "0.85rem", boxSizing: "border-box" }} />
                  </div>
                  <div>
                    <label style={{ fontSize: "0.8rem", color: "#94a3b8", display: "block", marginBottom: "0.3rem" }}>Memory Value</label>
                    <input value={memVal} onChange={e => setMemVal(e.target.value)} style={{ width: "100%", background: "rgba(10,15,30,0.8)", border: "1px solid rgba(168,85,247,0.3)", color: "#e2e8f0", padding: "0.5rem", borderRadius: "6px", fontSize: "0.85rem", boxSizing: "border-box" }} />
                  </div>
                  <div>
                    <label style={{ fontSize: "0.8rem", color: "#94a3b8", display: "block", marginBottom: "0.3rem" }}>Memory Tier</label>
                    <select value={memTier} onChange={e => setMemTier(e.target.value)} style={{ width: "100%", background: "rgba(10,15,30,0.8)", border: "1px solid rgba(168,85,247,0.3)", color: "#e2e8f0", padding: "0.5rem", borderRadius: "6px", fontSize: "0.85rem" }}>
                      {["episodic", "semantic", "procedural", "working"].map(t => <option key={t} value={t}>{t.toUpperCase()}</option>)}
                    </select>
                  </div>
                  <div style={{ display: "flex", gap: "0.5rem" }}>
                    <button onClick={handleStoreMemory} style={{ flex: 1, padding: "0.6rem", borderRadius: "8px", border: "none", background: "linear-gradient(135deg, #a855f7, #ec4899)", color: "#fff", fontWeight: 700, fontSize: "0.85rem", cursor: "pointer" }}>Store Memory</button>
                    <button onClick={handleRecallMemory} style={{ flex: 1, padding: "0.6rem", borderRadius: "8px", border: "1px solid rgba(168,85,247,0.4)", background: "rgba(168,85,247,0.15)", color: "#c084fc", fontWeight: 700, fontSize: "0.85rem", cursor: "pointer" }}>Recall Memory</button>
                  </div>
                </div>

                <div style={{ background: "rgba(15,23,42,0.9)", border: "1px solid rgba(168,85,247,0.25)", borderRadius: "14px", padding: "1.5rem" }}>
                  <h3 style={{ margin: "0 0 1rem", color: "#c084fc", fontWeight: 700 }}>🔍 Recalled Memories ({recalledMemories.length})</h3>
                  {recalledMemories.length > 0 ? (
                    <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                      {recalledMemories.map((m, i) => (
                        <div key={i} style={{ background: "rgba(10,15,30,0.8)", border: "1px solid rgba(168,85,247,0.2)", borderRadius: "8px", padding: "0.6rem", fontSize: "0.8rem" }}>
                          <div style={{ color: "#c084fc", fontWeight: 700 }}>[{m.memory_tier.toUpperCase()}] {m.key}</div>
                          <div style={{ color: "#e2e8f0", marginTop: "0.2rem" }}>{m.value}</div>
                          <div style={{ color: "#64748b", fontSize: "0.72rem", marginTop: "0.2rem" }}>Access count: {m.access_count} | Confidence: {m.confidence}</div>
                        </div>
                      ))}
                    </div>
                  ) : <div style={{ color: "#475569", fontSize: "0.85rem" }}>Store or recall memories using the left panel.</div>}
                </div>
              </div>
            )}

            {/* TAB 5: EXPORT */}
            {activeTab === "export" && (
              <div style={{ background: "rgba(15,23,42,0.9)", border: "1px solid rgba(6,182,212,0.25)", borderRadius: "14px", padding: "1.5rem", maxWidth: "600px" }}>
                <h3 style={{ margin: "0 0 1rem", color: "#22d3ee", fontWeight: 700 }}>📤 Export Analytics Data</h3>
                <div style={{ display: "flex", gap: "1rem", alignItems: "center", marginBottom: "1rem" }}>
                  <select value={exportFormat} onChange={e => setExportFormat(e.target.value)} style={{ background: "rgba(10,15,30,0.8)", border: "1px solid rgba(6,182,212,0.3)", color: "#e2e8f0", padding: "0.5rem", borderRadius: "6px", fontSize: "0.85rem" }}>
                    <option value="csv">CSV Format</option>
                    <option value="json">JSON Format</option>
                  </select>
                  <button onClick={handleExport} style={{ padding: "0.55rem 1.2rem", borderRadius: "8px", border: "none", background: "linear-gradient(135deg, #06b6d4, #3b82f6)", color: "#fff", fontWeight: 700, fontSize: "0.88rem", cursor: "pointer" }}>Generate Export</button>
                </div>

                {exportDoc && (
                  <div style={{ background: "rgba(10,15,30,0.8)", border: "1px solid rgba(52,211,153,0.3)", borderRadius: "8px", padding: "1rem", fontSize: "0.82rem" }}>
                    <div style={{ color: "#34d399", fontWeight: 700 }}>✅ Export File Ready</div>
                    <div style={{ color: "#94a3b8", marginTop: "0.3rem" }}>Rows: {exportDoc.row_count} | Format: {exportDoc.format.toUpperCase()}</div>
                    <div style={{ color: "#22d3ee", marginTop: "0.3rem", fontFamily: "monospace" }}>Download URL: {exportDoc.download_url}</div>
                  </div>
                )}
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
};

export default KnowledgeAnalyticsDashboardPage;
