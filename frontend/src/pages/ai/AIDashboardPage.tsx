import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../contexts/AuthContext";
import {
  aiApi,
  AIProviderItem,
  AIModelItem,
  AIPromptTemplateItem,
  AICostItem,
  AITokenItem,
} from "../../api/ai";
import { NotificationBell } from "../../components/NotificationBell";

type ActiveTab =
  | "providers" | "models" | "prompts" | "costs" | "tokens" | "streaming"
  | "capabilities" | "policies" | "sessions" | "prompt_registry"
  | "benchmarks" | "guardrails" | "evaluation" | "memory"
  | "pipelines" | "executions" | "provider_health" | "queues";

const tabConfig: { id: ActiveTab; label: string; icon: string; section: string }[] = [
  { id: "providers", label: "Providers", icon: "🔌", section: "Gateway" },
  { id: "models", label: "Models", icon: "🤖", section: "Gateway" },
  { id: "prompts", label: "Templates", icon: "📖", section: "Gateway" },
  { id: "costs", label: "Costs", icon: "💵", section: "Gateway" },
  { id: "tokens", label: "Tokens", icon: "📊", section: "Gateway" },
  { id: "streaming", label: "Streaming", icon: "⚡", section: "Gateway" },
  { id: "capabilities", label: "Capabilities", icon: "🎯", section: "Intelligence" },
  { id: "policies", label: "Policies", icon: "📋", section: "Intelligence" },
  { id: "sessions", label: "Sessions", icon: "🔍", section: "Intelligence" },
  { id: "prompt_registry", label: "Prompt Registry", icon: "🔖", section: "Intelligence" },
  { id: "benchmarks", label: "Benchmarks", icon: "🏆", section: "Evaluation" },
  { id: "guardrails", label: "Guardrails", icon: "🛡️", section: "Evaluation" },
  { id: "evaluation", label: "Evaluation", icon: "⚖️", section: "Evaluation" },
  { id: "memory", label: "Memory", icon: "🧠", section: "Evaluation" },
  { id: "pipelines", label: "Pipeline Templates", icon: "🚀", section: "Orchestration" },
  { id: "executions", label: "Execution Monitor", icon: "📈", section: "Orchestration" },
  { id: "provider_health", label: "Circuit Breaker & Health", icon: "🛡️", section: "Orchestration" },
  { id: "queues", label: "Queue Manager", icon: "📥", section: "Orchestration" },
];

const API_BASE = "/api/v1";

const badge = (label: string, color = "#a5b4fc", bg = "rgba(99,102,241,0.15)") => (
  <span style={{ fontSize: "0.7rem", padding: "0.15rem 0.45rem", borderRadius: "100px", background: bg, color, fontWeight: 700 }}>
    {label}
  </span>
);

const statusBadge = (status: string) => {
  const map: Record<string, [string, string]> = {
    draft: ["#94a3b8", "rgba(148,163,184,0.15)"],
    review: ["#f59e0b", "rgba(245,158,11,0.15)"],
    approved: ["#60a5fa", "rgba(96,165,250,0.15)"],
    production: ["#34d399", "rgba(52,211,153,0.15)"],
    deprecated: ["#f87171", "rgba(248,113,113,0.15)"],
    archived: ["#475569", "rgba(71,85,105,0.15)"],
    completed: ["#34d399", "rgba(52,211,153,0.15)"],
    active: ["#a5b4fc", "rgba(99,102,241,0.15)"],
    failed: ["#f87171", "rgba(248,113,113,0.15)"],
    pending: ["#f59e0b", "rgba(245,158,11,0.15)"],
    CLOSED: ["#34d399", "rgba(52,211,153,0.15)"],
    OPEN: ["#f87171", "rgba(248,113,113,0.15)"],
    HALF_OPEN: ["#f59e0b", "rgba(245,158,11,0.15)"],
  };
  const [color, bg] = map[status] || ["#94a3b8", "rgba(148,163,184,0.15)"];
  return badge(status.toUpperCase(), color, bg);
};

const SectionHeader: React.FC<{ title: string; subtitle: string }> = ({ title, subtitle }) => (
  <div>
    <h2 style={{ margin: 0, fontSize: "1.3rem", fontWeight: 700 }}>{title}</h2>
    <p style={{ color: "#64748b", fontSize: "0.82rem", margin: "0.25rem 0 0 0" }}>{subtitle}</p>
  </div>
);

const Card: React.FC<{ children: React.ReactNode; style?: React.CSSProperties }> = ({ children, style }) => (
  <div style={{ padding: "1.25rem", borderRadius: "12px", border: "1px solid rgba(99,102,241,0.2)", background: "rgba(15,23,42,0.85)", ...style }}>
    {children}
  </div>
);

const Table: React.FC<{ headers: string[]; rows: React.ReactNode[][]; emptyMsg?: string }> = ({ headers, rows, emptyMsg }) => (
  <div style={{ background: "rgba(15,23,42,0.8)", border: "1px solid rgba(99,102,241,0.2)", borderRadius: "12px", overflow: "hidden" }}>
    <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.85rem" }}>
      <thead>
        <tr style={{ background: "rgba(99,102,241,0.1)", borderBottom: "1px solid rgba(99,102,241,0.2)" }}>
          {headers.map((h, i) => (
            <th key={i} style={{ textAlign: "left", padding: "0.85rem 1rem", color: "#94a3b8", fontWeight: 600 }}>{h}</th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.length === 0 ? (
          <tr>
            <td colSpan={headers.length} style={{ textAlign: "center", padding: "2rem", color: "#64748b" }}>
              {emptyMsg || "No data available."}
            </td>
          </tr>
        ) : rows.map((row, ri) => (
          <tr key={ri} style={{ borderBottom: "1px solid rgba(99,102,241,0.08)" }}>
            {row.map((cell, ci) => (
              <td key={ci} style={{ padding: "0.85rem 1rem", color: "#cbd5e1" }}>{cell}</td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  </div>
);

export const AIDashboardPage: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const [activeTab, setActiveTab] = useState<ActiveTab>("providers");

  // Phase 12.7A state
  const [providers, setProviders] = useState<AIProviderItem[]>([]);
  const [models, setModels] = useState<AIModelItem[]>([]);
  const [prompts, setPrompts] = useState<AIPromptTemplateItem[]>([]);
  const [costs, setCosts] = useState<AICostItem[]>([]);
  const [tokens, setTokens] = useState<AITokenItem[]>([]);
  const [testPrompt, setTestPrompt] = useState("Explain RAG pipeline architecture in one sentence.");
  const [testProvider, setTestProvider] = useState("gemini");
  const [testModel, setTestModel] = useState("gemini-1.5-flash");
  const [streamOutput, setStreamOutput] = useState("");
  const [streamingActive, setStreamingActive] = useState(false);

  // Phase 12.7B state
  const [capabilities, setCapabilities] = useState<any[]>([]);
  const [policies, setPolicies] = useState<any[]>([]);
  const [sessions, setSessions] = useState<any[]>([]);
  const [promptRegistry, setPromptRegistry] = useState<any[]>([]);
  const [benchmarks, setBenchmarks] = useState<any[]>([]);
  const [guardrailLogs, setGuardrailLogs] = useState<any[]>([]);
  const [evaluations, setEvaluations] = useState<any[]>([]);
  const [memoryRecords, setMemoryRecords] = useState<any[]>([]);
  const [memoryArtifacts, setMemoryArtifacts] = useState<any[]>([]);

  // Phase 12.7C state
  const [pipelineTemplates, setPipelineTemplates] = useState<any[]>([]);
  const [executions, setExecutions] = useState<any[]>([]);
  const [providerHealth, setProviderHealth] = useState<any[]>([]);
  const [queueStatus, setQueueStatus] = useState<any>(null);
  const [runningPipeline, setRunningPipeline] = useState<string | null>(null);
  const [pipelineRunResult, setPipelineRunResult] = useState<any>(null);

  // Capability route test
  const [capPrompt, setCapPrompt] = useState("Analyze this business opportunity and provide a strategic plan.");
  const [capCapability, setCapCapability] = useState("reasoning");
  const [capResult, setCapResult] = useState<any>(null);
  const [capLoading, setCapLoading] = useState(false);

  useEffect(() => {
    fetchData();
  }, [activeTab]);

  const fetchData = async () => {
    try {
      const token = localStorage.getItem("access_token");
      const headers = { Authorization: `Bearer ${token}` };
      const get = (path: string) => fetch(`${API_BASE}${path}`, { headers }).then(r => r.json());

      if (activeTab === "providers") setProviders(await aiApi.getProviders());
      else if (activeTab === "models") setModels(await aiApi.getModels());
      else if (activeTab === "prompts") setPrompts(await aiApi.getPrompts());
      else if (activeTab === "costs") setCosts(await aiApi.getCosts());
      else if (activeTab === "tokens") setTokens(await aiApi.getTokens());
      else if (activeTab === "capabilities") setCapabilities(await get("/ai/capabilities"));
      else if (activeTab === "policies") setPolicies(await get("/ai/policies"));
      else if (activeTab === "sessions") setSessions(await get("/ai/sessions?limit=30"));
      else if (activeTab === "prompt_registry") setPromptRegistry(await get("/ai/prompts/registry"));
      else if (activeTab === "benchmarks") setBenchmarks(await get("/ai/benchmarks"));
      else if (activeTab === "guardrails") setGuardrailLogs(await get("/ai/guardrails/logs?limit=50"));
      else if (activeTab === "evaluation") setEvaluations(await get("/ai/evaluations?limit=20"));
      else if (activeTab === "memory") {
        const [mem, arts] = await Promise.all([get("/ai/memory?limit=20"), get("/ai/memory/artifacts?limit=20")]);
        setMemoryRecords(Array.isArray(mem) ? mem : []);
        setMemoryArtifacts(Array.isArray(arts) ? arts : []);
      } else if (activeTab === "pipelines") {
        setPipelineTemplates(await get("/ai/pipelines"));
      } else if (activeTab === "executions") {
        setExecutions(await get("/ai/executions?limit=30"));
      } else if (activeTab === "provider_health") {
        setProviderHealth(await get("/ai/provider-health"));
      } else if (activeTab === "queues") {
        setQueueStatus(await get("/ai/queues"));
      }
    } catch (e) {
      console.error("Failed to fetch data for tab:", activeTab, e);
    }
  };

  const handleRunPipeline = async (templateId: string) => {
    setRunningPipeline(templateId);
    setPipelineRunResult(null);
    try {
      const token = localStorage.getItem("access_token");
      const res = await fetch(`${API_BASE}/ai/workflows/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          template_id: templateId,
          inputs: { target_company: "Acme Corp", industry: "SaaS", lead_name: "Jane Doe" },
          priority: "Interactive",
        }),
      });
      const data = await res.json();
      setPipelineRunResult(data);
    } catch (e) {
      setPipelineRunResult({ error: String(e) });
    }
    setRunningPipeline(null);
  };

  const handleStreamTest = async () => {
    setStreamOutput("");
    setStreamingActive(true);
    try {
      const token = localStorage.getItem("access_token");
      const response = await fetch(`/api/v1/ai/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ prompt: testPrompt, provider: testProvider, model: testModel, stream: true }),
      });
      if (!response.body) return;
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value);
        for (const line of chunk.split("\n")) {
          if (line.startsWith("data: ")) {
            try {
              const parsed = JSON.parse(line.substring(6));
              if (parsed.chunk) setStreamOutput(prev => prev + parsed.chunk);
            } catch {}
          }
        }
      }
    } catch {}
    finally { setStreamingActive(false); }
  };

  const handleCapabilityRoute = async () => {
    setCapLoading(true);
    setCapResult(null);
    try {
      const token = localStorage.getItem("access_token");
      const response = await fetch(`${API_BASE}/ai/capabilities/route`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ capability: capCapability, prompt: capPrompt }),
      });
      const data = await response.json();
      setCapResult(data);
    } catch (e) {
      setCapResult({ error: String(e) });
    }
    setCapLoading(false);
  };

  const sections = ["Gateway", "Intelligence", "Evaluation", "Orchestration"];

  return (
    <div style={{ minHeight: "100vh", background: "#0a0f1e", color: "#e2e8f0", fontFamily: "'Inter', sans-serif", display: "flex", flexDirection: "column" }}>
      {/* Top Header */}
      <nav style={{ background: "rgba(15,23,42,0.95)", borderBottom: "1px solid rgba(99,102,241,0.2)", padding: "0 2rem", height: "60px", display: "flex", alignItems: "center", justifyContent: "space-between", backdropFilter: "blur(12px)", position: "sticky", top: 0, zIndex: 100 }}>
        <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
          <div style={{ fontSize: "1.4rem", fontWeight: 800, background: "linear-gradient(135deg, #6366f1, #8b5cf6)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
            LeadForgeAI
          </div>
          <div style={{ color: "#64748b", fontSize: "0.85rem" }}>/ Enterprise AI Orchestration Platform</div>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
          <NotificationBell />
          <button onClick={() => navigate("/scheduler")} style={{ background: "none", border: "1px solid rgba(99,102,241,0.3)", color: "#a5b4fc", padding: "0.4rem 1rem", borderRadius: "6px", cursor: "pointer", fontSize: "0.85rem" }}>⏱️ Scheduler</button>
          <button onClick={() => navigate("/plugins")} style={{ background: "none", border: "1px solid rgba(99,102,241,0.3)", color: "#94a3b8", padding: "0.4rem 1rem", borderRadius: "6px", cursor: "pointer", fontSize: "0.85rem" }}>🔌 Plugins</button>
          <button onClick={() => navigate("/chat")} style={{ background: "none", border: "1px solid rgba(99,102,241,0.3)", color: "#94a3b8", padding: "0.4rem 1rem", borderRadius: "6px", cursor: "pointer", fontSize: "0.85rem" }}>💬 Chat CRM</button>
          <span style={{ color: "#64748b", fontSize: "0.85rem" }}>{user?.email}</span>
          <button onClick={logout} style={{ background: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.3)", color: "#f87171", padding: "0.4rem 1rem", borderRadius: "6px", cursor: "pointer", fontSize: "0.85rem" }}>Logout</button>
        </div>
      </nav>

      <div style={{ display: "flex", flex: 1 }}>
        {/* Left Sidebar */}
        <aside style={{ width: "240px", borderRight: "1px solid rgba(99,102,241,0.15)", background: "rgba(15,23,42,0.5)", padding: "1.5rem", display: "flex", flexDirection: "column", gap: "0.25rem", overflowY: "auto" }}>
          {sections.map(section => (
            <div key={section}>
              <div style={{ fontSize: "0.7rem", fontWeight: 700, color: "#475569", textTransform: "uppercase", letterSpacing: "0.08em", margin: "1rem 0 0.4rem 0.5rem" }}>{section}</div>
              {tabConfig.filter(t => t.section === section).map(t => (
                <button
                  key={t.id}
                  onClick={() => setActiveTab(t.id)}
                  style={{
                    textAlign: "left",
                    padding: "0.65rem 1rem",
                    borderRadius: "8px",
                    border: "none",
                    background: activeTab === t.id ? "rgba(99,102,241,0.15)" : "transparent",
                    color: activeTab === t.id ? "#a5b4fc" : "#94a3b8",
                    fontWeight: activeTab === t.id ? 700 : 500,
                    cursor: "pointer",
                    width: "100%",
                    fontSize: "0.85rem",
                    display: "flex",
                    alignItems: "center",
                    gap: "0.6rem",
                    transition: "all 0.15s",
                  }}
                >
                  <span>{t.icon}</span>{t.label}
                </button>
              ))}
            </div>
          ))}
        </aside>

        {/* Main Panel */}
        <main style={{ flex: 1, padding: "2rem", overflowY: "auto" }}>

          {/* ─── PIPELINE TEMPLATES (12.7C) ─── */}
          {activeTab === "pipelines" && (
            <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
              <SectionHeader title="Built-In Pipeline Templates" subtitle="10 pre-engineered multi-step AI DAG execution pipelines." />

              {pipelineRunResult && (
                <Card style={{ border: "1px solid rgba(52,211,153,0.3)", background: "rgba(16,185,129,0.05)" }}>
                  <div style={{ fontSize: "0.9rem", fontWeight: 700, color: "#34d399", marginBottom: "0.5rem" }}>⚡ Pipeline Execution Completed</div>
                  <div style={{ display: "flex", gap: "1.5rem", fontSize: "0.82rem", flexWrap: "wrap" }}>
                    <div>Run ID: <code style={{ color: "#a5b4fc" }}>{pipelineRunResult.run_id}</code></div>
                    <div>Latency: <span style={{ color: "#cbd5e1" }}>{pipelineRunResult.total_latency_ms}ms</span></div>
                    <div>Completed Nodes: <span style={{ color: "#34d399" }}>{pipelineRunResult.completed_nodes?.length}</span></div>
                    <div>Status: {statusBadge(pipelineRunResult.status)}</div>
                  </div>
                </Card>
              )}

              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(340px, 1fr))", gap: "1.25rem" }}>
                {pipelineTemplates.map((p: any) => (
                  <Card key={p.template_id} style={{ display: "flex", flexDirection: "column", justifyContent: "space-between" }}>
                    <div>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "start" }}>
                        <div style={{ fontSize: "1rem", fontWeight: 700, color: "#fff" }}>{p.name}</div>
                        {badge(p.category.toUpperCase(), "#60a5fa", "rgba(96,165,250,0.15)")}
                      </div>
                      <div style={{ fontSize: "0.8rem", color: "#64748b", marginTop: "0.4rem" }}>{p.description}</div>
                      <div style={{ marginTop: "0.75rem", fontSize: "0.78rem", color: "#94a3b8" }}>
                        DAG Nodes ({p.workflow_spec?.nodes?.length}): {p.workflow_spec?.nodes?.map((n: any) => n.node_type).join(" → ")}
                      </div>
                    </div>

                    <button
                      onClick={() => handleRunPipeline(p.template_id)}
                      disabled={runningPipeline === p.template_id}
                      style={{
                        marginTop: "1rem",
                        padding: "0.6rem",
                        borderRadius: "8px",
                        border: "none",
                        background: "linear-gradient(135deg, #6366f1, #8b5cf6)",
                        color: "#fff",
                        fontWeight: 700,
                        cursor: "pointer",
                        width: "100%",
                      }}
                    >
                      {runningPipeline === p.template_id ? "Running Pipeline..." : "⚡ Execute Pipeline"}
                    </button>
                  </Card>
                ))}
              </div>
            </div>
          )}

          {/* ─── EXECUTIONS (12.7C) ─── */}
          {activeTab === "executions" && (
            <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
              <SectionHeader title="Execution Monitor" subtitle="Real-time DAG run execution history, node results, and telemetry." />
              <Table
                headers={["Run ID", "Workflow", "Priority", "Completed Nodes", "Latency", "Tokens", "Cost", "Status"]}
                emptyMsg="No workflow executions recorded yet."
                rows={executions.map((e: any) => [
                  <code style={{ fontSize: "0.72rem", color: "#64748b" }}>{e.run_id?.substring(0, 18)}…</code>,
                  <span style={{ color: "#a5b4fc", fontWeight: 600 }}>{e.workflow_id}</span>,
                  badge(e.priority),
                  <span style={{ color: "#34d399" }}>{e.completed_node_ids?.length || 0} nodes</span>,
                  <span style={{ color: "#cbd5e1" }}>{(e.total_latency_ms || 0).toFixed(1)}ms</span>,
                  <span style={{ color: "#cbd5e1" }}>{(e.total_tokens || 0).toLocaleString()}</span>,
                  <span style={{ color: "#34d399" }}>${(e.total_cost || 0).toFixed(5)}</span>,
                  statusBadge(e.status),
                ])}
              />
            </div>
          )}

          {/* ─── PROVIDER HEALTH (12.7C) ─── */}
          {activeTab === "provider_health" && (
            <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
              <SectionHeader title="Circuit Breaker & Provider Health" subtitle="Real-time circuit states (CLOSED / OPEN / HALF_OPEN) and resilience tracking." />
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: "1rem" }}>
                {providerHealth.map((h: any) => (
                  <Card key={h.provider}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                      <div style={{ fontSize: "1.1rem", fontWeight: 700, textTransform: "uppercase", color: "#a5b4fc" }}>{h.provider}</div>
                      {statusBadge(h.state)}
                    </div>
                    <div style={{ marginTop: "1rem", display: "flex", flexDirection: "column", gap: "0.4rem", fontSize: "0.82rem" }}>
                      <div style={{ display: "flex", justifyContent: "space-between" }}>
                        <span style={{ color: "#64748b" }}>Consecutive Failures</span>
                        <span style={{ color: h.consecutive_failures > 0 ? "#f87171" : "#34d399", fontWeight: 700 }}>{h.consecutive_failures}</span>
                      </div>
                      <div style={{ display: "flex", justifyContent: "space-between" }}>
                        <span style={{ color: "#64748b" }}>Successes / Failures</span>
                        <span style={{ color: "#cbd5e1" }}>{h.total_successes} / {h.total_failures}</span>
                      </div>
                      <div style={{ display: "flex", justifyContent: "space-between" }}>
                        <span style={{ color: "#64748b" }}>Error Rate</span>
                        <span style={{ color: h.error_rate > 0.1 ? "#f87171" : "#34d399" }}>{(h.error_rate * 100).toFixed(1)}%</span>
                      </div>
                    </div>
                  </Card>
                ))}
              </div>
            </div>
          )}

          {/* ─── QUEUES (12.7C) ─── */}
          {activeTab === "queues" && (
            <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
              <SectionHeader title="Priority Queue Manager" subtitle="6 priority levels (Critical, Enterprise, Realtime, Interactive, Background, Low) and Dead Letter Queue." />
              <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "1rem" }}>
                <Card style={{ textAlign: "center" }}>
                  <div style={{ fontSize: "2rem", fontWeight: 800, color: "#a5b4fc" }}>{queueStatus?.in_memory_depth || 0}</div>
                  <div style={{ fontSize: "0.8rem", color: "#64748b", marginTop: "0.25rem" }}>In-Memory Queue Depth</div>
                </Card>
                <Card style={{ textAlign: "center" }}>
                  <div style={{ fontSize: "2rem", fontWeight: 800, color: "#f87171" }}>{queueStatus?.dlq_unresolved_count || 0}</div>
                  <div style={{ fontSize: "0.8rem", color: "#64748b", marginTop: "0.25rem" }}>DLQ Unresolved Items</div>
                </Card>
                <Card style={{ textAlign: "center" }}>
                  <div style={{ fontSize: "2rem", fontWeight: 800, color: "#34d399" }}>6</div>
                  <div style={{ fontSize: "0.8rem", color: "#64748b", marginTop: "0.25rem" }}>Supported Priority Levels</div>
                </Card>
              </div>

              <div>
                <div style={{ fontSize: "0.9rem", fontWeight: 700, color: "#f87171", marginBottom: "0.75rem" }}>☠️ Dead Letter Queue Items</div>
                <Table
                  headers={["DLQ ID", "Original Queue ID", "Workflow Run", "Node ID", "Failure Reason", "Failed At"]}
                  emptyMsg="Dead Letter Queue is empty."
                  rows={(queueStatus?.dlq_items || []).map((d: any) => [
                    <code style={{ fontSize: "0.7rem", color: "#64748b" }}>{d.dlq_id}</code>,
                    <code style={{ fontSize: "0.7rem", color: "#64748b" }}>{d.original_queue_id}</code>,
                    <code style={{ fontSize: "0.7rem", color: "#a5b4fc" }}>{d.workflow_run_id}</code>,
                    <span>{d.node_id}</span>,
                    <span style={{ color: "#f87171" }}>{d.failure_reason}</span>,
                    <span style={{ color: "#64748b", fontSize: "0.75rem" }}>{new Date(d.failed_at).toLocaleString()}</span>,
                  ])}
                />
              </div>
            </div>
          )}

          {/* ─── PROVIDERS ─── */}
          {activeTab === "providers" && (
            <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
              <SectionHeader title="AI Provider Adapters" subtitle="Connection profiles and status for enterprise adapters." />
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: "1rem" }}>
                {providers.map(p => (
                  <Card key={p.provider}>
                    <div style={{ fontSize: "1rem", fontWeight: 700, textTransform: "uppercase", color: "#a5b4fc" }}>{p.provider}</div>
                    <div style={{ display: "flex", justifyContent: "space-between", marginTop: "1rem", alignItems: "center" }}>
                      <span style={{ fontSize: "0.8rem", color: "#64748b" }}>Status</span>
                      {badge(p.status.toUpperCase(), "#34d399", "rgba(16,185,129,0.15)")}
                    </div>
                  </Card>
                ))}
              </div>
            </div>
          )}

          {/* ─── MODELS ─── */}
          {activeTab === "models" && (
            <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
              <SectionHeader title="Supported AI Models" subtitle="Context sizes, pricing metrics, and tool execution support matrix." />
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))", gap: "1.25rem" }}>
                {models.map(m => (
                  <Card key={m.model_id}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                      <div style={{ fontSize: "1rem", fontWeight: 700, color: "#fff" }}>{m.name}</div>
                      {badge(m.provider.toUpperCase())}
                    </div>
                    <div style={{ fontSize: "0.8rem", color: "#94a3b8", marginTop: "0.5rem" }}>ID: {m.model_id}</div>
                    <div style={{ borderTop: "1px solid rgba(99,102,241,0.15)", marginTop: "1rem", paddingTop: "0.75rem", display: "flex", flexDirection: "column", gap: "0.4rem" }}>
                      {[["Context Window", `${m.context_window.toLocaleString()} tokens`, "#cbd5e1"], ["Input Price", `$${m.input_token_price}/1M`, "#34d399"], ["Output Price", `$${m.output_token_price}/1M`, "#34d399"], ["Type", m.is_embedding ? "Embedding" : "Completion", "#f59e0b"]].map(([k, v, c]) => (
                        <div key={String(k)} style={{ display: "flex", justifyContent: "space-between", fontSize: "0.8rem" }}>
                          <span style={{ color: "#64748b" }}>{k}</span>
                          <span style={{ color: String(c), fontWeight: 600 }}>{v}</span>
                        </div>
                      ))}
                    </div>
                  </Card>
                ))}
              </div>
            </div>
          )}

          {/* ─── PROMPTS ─── */}
          {activeTab === "prompts" && (
            <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
              <SectionHeader title="Prompt Templates" subtitle="System prompts and structured templates with placeholder variables." />
              {prompts.map(p => (
                <Card key={p.template_id}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <div>
                      <div style={{ fontSize: "1.05rem", fontWeight: 700, color: "#a5b4fc" }}>{p.name}</div>
                      <div style={{ fontSize: "0.75rem", color: "#64748b" }}>ID: {p.template_id}</div>
                    </div>
                    {badge(p.category.toUpperCase())}
                  </div>
                  <div style={{ marginTop: "0.75rem", fontSize: "0.82rem", background: "rgba(10,15,30,0.6)", padding: "0.75rem 1rem", borderRadius: "8px", border: "1px solid rgba(99,102,241,0.1)", color: "#e2e8f0", whiteSpace: "pre-wrap" }}>
                    {p.user_prompt_template}
                  </div>
                  <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap", marginTop: "0.5rem" }}>
                    {p.variables?.map((v: string) => (
                      <span key={v} style={{ fontSize: "0.7rem", padding: "0.15rem 0.45rem", borderRadius: "4px", background: "rgba(99,102,241,0.12)", color: "#a5b4fc", border: "1px solid rgba(99,102,241,0.2)" }}>{"{" + v + "}"}</span>
                    ))}
                  </div>
                </Card>
              ))}
            </div>
          )}

          {/* ─── COSTS ─── */}
          {activeTab === "costs" && (
            <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
              <SectionHeader title="Dollar Cost Attribution" subtitle="Cumulative LLM dollars spent per user, agent, and pipeline workflow." />
              <Table
                headers={["Identifier Type", "Resource ID", "Estimated Cost", "Last Updated"]}
                emptyMsg="No cost records tracked yet."
                rows={costs.map(c => [
                  <span style={{ color: "#a5b4fc", fontWeight: 600 }}>{c.identifier_type}</span>,
                  <span style={{ fontFamily: "monospace" }}>{c.identifier_id}</span>,
                  <span style={{ color: "#34d399", fontWeight: 700 }}>${c.estimated_cost.toFixed(5)} {c.currency}</span>,
                  <span style={{ color: "#64748b" }}>{new Date(c.updated_at).toLocaleString()}</span>,
                ])}
              />
            </div>
          )}

          {/* ─── TOKENS ─── */}
          {activeTab === "tokens" && (
            <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
              <SectionHeader title="Token Volume Analytics" subtitle="Cumulative tokens processed (Prompt, Completion, Embeddings)." />
              <Table
                headers={["Resource", "Prompt", "Completion", "Embedding", "Total"]}
                emptyMsg="No token usage tracked yet."
                rows={tokens.map(t => [
                  <span>{badge(t.identifier_type.toUpperCase())} <span style={{ fontFamily: "monospace", fontSize: "0.82rem" }}>{t.identifier_id}</span></span>,
                  t.prompt_tokens.toLocaleString(),
                  t.completion_tokens.toLocaleString(),
                  t.embedding_tokens.toLocaleString(),
                  <span style={{ color: "#a5b4fc", fontWeight: 700 }}>{t.total_tokens.toLocaleString()}</span>,
                ])}
              />
            </div>
          )}

          {/* ─── STREAMING ─── */}
          {activeTab === "streaming" && (
            <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
              <SectionHeader title="Real-Time Streaming Monitor" subtitle="Test gateway streaming latency and SSE token ingestion." />
              <div style={{ display: "flex", gap: "1.5rem" }}>
                <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: "0.75rem" }}>
                  <div style={{ display: "flex", gap: "1rem" }}>
                    {[["Provider", testProvider, setTestProvider, ["gemini", "openai", "claude", "ollama"]], ["Model", testModel, setTestModel, ["gemini-1.5-flash", "gpt-4o-mini", "claude-3-5-sonnet", "llama3"]]].map(([label, val, setter, opts]: any) => (
                      <div key={label} style={{ flex: 1 }}>
                        <label style={{ fontSize: "0.78rem", color: "#64748b", display: "block", marginBottom: "0.25rem" }}>{label}</label>
                        <select value={val} onChange={e => setter(e.target.value)} style={{ width: "100%", padding: "0.5rem", borderRadius: "6px", background: "#0a0f1e", border: "1px solid rgba(99,102,241,0.3)", color: "#fff" }}>
                          {opts.map((o: string) => <option key={o} value={o}>{o}</option>)}
                        </select>
                      </div>
                    ))}
                  </div>
                  <div>
                    <label style={{ fontSize: "0.78rem", color: "#64748b", display: "block", marginBottom: "0.25rem" }}>Prompt</label>
                    <textarea value={testPrompt} onChange={e => setTestPrompt(e.target.value)} rows={3} style={{ width: "100%", padding: "0.75rem", borderRadius: "8px", background: "#0a0f1e", border: "1px solid rgba(99,102,241,0.3)", color: "#fff", resize: "none", fontSize: "0.85rem", boxSizing: "border-box" }} />
                  </div>
                  <button onClick={handleStreamTest} disabled={streamingActive} style={{ width: "100%", padding: "0.75rem", borderRadius: "8px", border: "none", background: "linear-gradient(135deg, #6366f1, #8b5cf6)", color: "#fff", fontWeight: 700, cursor: "pointer" }}>
                    {streamingActive ? "⚡ Streaming..." : "Test Stream Connection"}
                  </button>
                </div>
                <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                  <span style={{ fontSize: "0.78rem", color: "#64748b" }}>Live SSE Stream Output:</span>
                  <div style={{ flex: 1, minHeight: "220px", background: "rgba(10,15,30,0.8)", border: "1px solid rgba(99,102,241,0.15)", borderRadius: "10px", padding: "1rem", color: "#cbd5e1", fontSize: "0.88rem", overflowY: "auto", whiteSpace: "pre-wrap", fontFamily: "monospace" }}>
                    {streamOutput || "Stream content will appear here..."}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* ─── CAPABILITIES ─── */}
          {activeTab === "capabilities" && (
            <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
              <SectionHeader title="AI Capability Registry" subtitle="12 named capabilities mapped to default providers and models via Policy Engine." />
              <Card>
                <div style={{ fontSize: "0.9rem", fontWeight: 700, color: "#a5b4fc", marginBottom: "0.75rem" }}>🎯 Test Capability Routing</div>
                <div style={{ display: "flex", gap: "1rem", marginBottom: "0.75rem" }}>
                  <div style={{ flex: 1 }}>
                    <label style={{ fontSize: "0.75rem", color: "#64748b", display: "block", marginBottom: "0.25rem" }}>Capability</label>
                    <select value={capCapability} onChange={e => setCapCapability(e.target.value)} style={{ width: "100%", padding: "0.5rem", borderRadius: "6px", background: "#0a0f1e", border: "1px solid rgba(99,102,241,0.3)", color: "#fff" }}>
                      {capabilities.map((c: any) => <option key={c.capability_id} value={c.capability_id}>{c.capability_id}</option>)}
                    </select>
                  </div>
                  <div style={{ flex: 2 }}>
                    <label style={{ fontSize: "0.75rem", color: "#64748b", display: "block", marginBottom: "0.25rem" }}>Test Prompt</label>
                    <input value={capPrompt} onChange={e => setCapPrompt(e.target.value)} style={{ width: "100%", padding: "0.5rem", borderRadius: "6px", background: "#0a0f1e", border: "1px solid rgba(99,102,241,0.3)", color: "#fff", boxSizing: "border-box" }} />
                  </div>
                </div>
                <button onClick={handleCapabilityRoute} disabled={capLoading} style={{ padding: "0.6rem 1.5rem", borderRadius: "8px", border: "none", background: "linear-gradient(135deg, #6366f1, #8b5cf6)", color: "#fff", fontWeight: 700, cursor: "pointer" }}>
                  {capLoading ? "Routing..." : "Route via Policy Engine"}
                </button>
                {capResult && (
                  <div style={{ marginTop: "1rem", background: "rgba(10,15,30,0.7)", padding: "1rem", borderRadius: "8px", border: "1px solid rgba(99,102,241,0.15)", fontSize: "0.82rem" }}>
                    <div style={{ display: "flex", gap: "1.5rem", flexWrap: "wrap" }}>
                      {[["Capability", capResult.capability], ["Provider", capResult.provider_used || capResult.provider], ["Model", capResult.model_used || capResult.model], ["Policy", capResult.policy_name || capResult.resolved_from]].map(([k, v]) => (
                        <div key={k}>
                          <div style={{ color: "#64748b", fontSize: "0.72rem" }}>{k}</div>
                          <div style={{ color: "#a5b4fc", fontWeight: 600 }}>{v || "—"}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </Card>

              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: "1rem" }}>
                {capabilities.map((c: any) => (
                  <Card key={c.capability_id}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "start" }}>
                      <div style={{ fontSize: "0.95rem", fontWeight: 700, color: "#fff" }}>{c.name}</div>
                      <code style={{ fontSize: "0.7rem", color: "#64748b", background: "rgba(99,102,241,0.1)", padding: "0.1rem 0.35rem", borderRadius: "4px" }}>{c.capability_id}</code>
                    </div>
                    <div style={{ fontSize: "0.8rem", color: "#64748b", marginTop: "0.4rem" }}>{c.description}</div>
                    <div style={{ marginTop: "0.75rem", display: "flex", gap: "0.5rem" }}>
                      {badge(c.default_provider.toUpperCase(), "#60a5fa", "rgba(96,165,250,0.15)")}
                      <code style={{ fontSize: "0.72rem", color: "#94a3b8" }}>{c.default_model}</code>
                    </div>
                  </Card>
                ))}
              </div>
            </div>
          )}

          {/* ─── POLICIES ─── */}
          {activeTab === "policies" && (
            <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
              <SectionHeader title="AI Policy Engine" subtitle="Declarative rules mapping capabilities to providers and models with priority ordering." />
              <Table
                headers={["Policy ID", "Capability", "Provider", "Model", "Priority", "Org", "Status"]}
                emptyMsg="No policies defined yet."
                rows={policies.map((p: any) => [
                  <code style={{ fontSize: "0.75rem", color: "#64748b" }}>{p.policy_id}</code>,
                  badge(p.capability, "#a5b4fc"),
                  badge(p.provider.toUpperCase(), "#60a5fa", "rgba(96,165,250,0.15)"),
                  <code style={{ fontSize: "0.75rem" }}>{p.model}</code>,
                  <span style={{ color: "#f59e0b", fontWeight: 700 }}>{p.priority}</span>,
                  p.org_id ? <code style={{ fontSize: "0.75rem" }}>{p.org_id}</code> : <span style={{ color: "#475569" }}>Global</span>,
                  badge(p.is_active ? "ACTIVE" : "INACTIVE", p.is_active ? "#34d399" : "#f87171", p.is_active ? "rgba(52,211,153,0.15)" : "rgba(248,113,113,0.15)"),
                ])}
              />
            </div>
          )}

          {/* ─── SESSIONS ─── */}
          {activeTab === "sessions" && (
            <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
              <SectionHeader title="AI Session Tracker" subtitle="Per-request AI sessions with telemetry, guardrail results, and policy routing." />
              <Table
                headers={["Session ID", "Capability", "Provider/Model", "Tokens", "Cost", "Status", "Guardrail"]}
                emptyMsg="No sessions recorded yet."
                rows={sessions.map((s: any) => [
                  <code style={{ fontSize: "0.72rem", color: "#64748b" }}>{s.session_id?.substring(0, 20)}…</code>,
                  s.capability ? badge(s.capability) : <span style={{ color: "#475569" }}>—</span>,
                  <span>{s.provider}<span style={{ color: "#475569" }}>/</span>{s.model}</span>,
                  <span style={{ color: "#a5b4fc" }}>{(s.total_tokens || 0).toLocaleString()}</span>,
                  <span style={{ color: "#34d399" }}>${(s.estimated_cost || 0).toFixed(5)}</span>,
                  statusBadge(s.status),
                  s.guardrail_passed == null ? <span style={{ color: "#475569" }}>—</span>
                    : s.guardrail_passed ? badge("PASS", "#34d399", "rgba(52,211,153,0.15)")
                    : badge("FAIL", "#f87171", "rgba(248,113,113,0.15)"),
                ])}
              />
            </div>
          )}

          {/* ─── PROMPT REGISTRY ─── */}
          {activeTab === "prompt_registry" && (
            <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
              <SectionHeader title="Prompt Registry" subtitle="Lifecycle-managed prompts: Draft → Review → Approved → Production → Deprecated → Archived." />
              <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
                {promptRegistry.map((p: any) => (
                  <Card key={p.registry_id}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                      <div>
                        <div style={{ fontSize: "1rem", fontWeight: 700, color: "#fff" }}>{p.name}</div>
                        <div style={{ fontSize: "0.72rem", color: "#64748b" }}>ID: {p.registry_id} · v{p.version}</div>
                      </div>
                      <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
                        {badge(p.category.toUpperCase())}
                        {statusBadge(p.status)}
                      </div>
                    </div>
                    <div style={{ marginTop: "0.75rem", fontSize: "0.82rem", background: "rgba(10,15,30,0.6)", padding: "0.75rem 1rem", borderRadius: "8px", color: "#cbd5e1" }}>
                      {p.user_prompt_template}
                    </div>
                  </Card>
                ))}
              </div>
            </div>
          )}

          {/* ─── BENCHMARKS ─── */}
          {activeTab === "benchmarks" && (
            <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
              <SectionHeader title="Model Benchmark Registry" subtitle="Define benchmark suites and run cross-provider performance comparisons." />
              {benchmarks.map((b: any) => (
                <Card key={b.benchmark_id}>
                  <div style={{ fontSize: "1rem", fontWeight: 700, color: "#fff" }}>{b.name}</div>
                  <div style={{ fontSize: "0.8rem", color: "#94a3b8", marginTop: "0.5rem" }}>Target Models: {b.target_models?.join(", ")}</div>
                </Card>
              ))}
            </div>
          )}

          {/* ─── GUARDRAILS ─── */}
          {activeTab === "guardrails" && (
            <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
              <SectionHeader title="AI Guardrail Logs" subtitle="Real-time validation results: PII detection, hallucination scoring, schema and length checks." />
              <Table
                headers={["Log ID", "PII", "Profanity", "Length", "Hallucin.", "Confidence", "Result"]}
                emptyMsg="No guardrail logs yet."
                rows={guardrailLogs.map((g: any) => [
                  <code style={{ fontSize: "0.7rem", color: "#64748b" }}>{g.log_id}</code>,
                  g.pii_detected ? badge("YES", "#f87171", "rgba(248,113,113,0.15)") : badge("NO", "#34d399", "rgba(52,211,153,0.15)"),
                  g.profanity_detected ? badge("YES", "#f87171", "rgba(248,113,113,0.15)") : badge("NO", "#34d399", "rgba(52,211,153,0.15)"),
                  g.length_valid == null ? "—" : g.length_valid ? badge("OK", "#34d399", "rgba(52,211,153,0.15)") : badge("FAIL", "#f87171", "rgba(248,113,113,0.15)"),
                  <span style={{ color: g.hallucination_score > 0.3 ? "#f87171" : "#34d399" }}>{(g.hallucination_score || 0).toFixed(2)}</span>,
                  <span style={{ color: "#a5b4fc" }}>{(g.confidence_score || 0).toFixed(2)}</span>,
                  g.passed ? badge("PASS", "#34d399", "rgba(52,211,153,0.15)") : badge("FAIL", "#f87171", "rgba(248,113,113,0.15)"),
                ])}
              />
            </div>
          )}

          {/* ─── EVALUATION ─── */}
          {activeTab === "evaluation" && (
            <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
              <SectionHeader title="AI Evaluation Framework" subtitle="Cross-provider prompt comparison with normalized scoring and ranked leaderboards." />
              {evaluations.map((e: any) => (
                <Card key={e.run_id}>
                  <div style={{ fontSize: "1rem", fontWeight: 700, color: "#fff" }}>{e.name}</div>
                  <div style={{ fontSize: "0.8rem", color: "#94a3b8" }}>{e.test_prompt}</div>
                </Card>
              ))}
            </div>
          )}

          {/* ─── MEMORY ─── */}
          {activeTab === "memory" && (
            <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
              <SectionHeader title="AI Memory Manager" subtitle="Prompt hash records, embedding references, cache links, and workflow artifacts." />
              <Table
                headers={["Memory ID", "Prompt Hash", "Embeddings", "Cache Keys", "Created"]}
                emptyMsg="No memory records yet."
                rows={memoryRecords.map((m: any) => [
                  <code style={{ fontSize: "0.7rem", color: "#64748b" }}>{m.memory_id}</code>,
                  <code style={{ fontSize: "0.7rem", color: "#64748b" }}>{m.prompt_hash?.substring(0, 16)}…</code>,
                  <span style={{ color: "#a5b4fc" }}>{m.embedding_ids?.length || 0}</span>,
                  <span style={{ color: "#a5b4fc" }}>{m.cache_keys?.length || 0}</span>,
                  <span style={{ color: "#64748b", fontSize: "0.75rem" }}>{new Date(m.created_at).toLocaleString()}</span>,
                ])}
              />
            </div>
          )}

        </main>
      </div>
    </div>
  );
};

export default AIDashboardPage;
