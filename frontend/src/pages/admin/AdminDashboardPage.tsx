import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../contexts/AuthContext";
import {
  platformApi,
  HealthStatus,
  SystemMetrics,
  FeatureFlag,
  AuditLog,
  RequestTrace,
} from "../../api/platform";

type AdminTab = "health" | "metrics" | "flags" | "audit" | "traces";

export const AdminDashboardPage: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const [activeTab, setActiveTab] = useState<AdminTab>("health");
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
  const [flags, setFlags] = useState<FeatureFlag[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
  const [traces, setTraces] = useState<RequestTrace[]>([]);

  useEffect(() => {
    loadData();
  }, [activeTab]);

  const loadData = async () => {
    try {
      if (activeTab === "health") {
        const data = await platformApi.getHealth();
        setHealth(data);
      } else if (activeTab === "metrics") {
        const data = await platformApi.getMetrics();
        setMetrics(data);
      } else if (activeTab === "flags") {
        const data = await platformApi.listFeatureFlags();
        setFlags(data);
      } else if (activeTab === "audit") {
        const data = await platformApi.listAuditLogs({ limit: 50 });
        setAuditLogs(data.items);
      } else if (activeTab === "traces") {
        const data = await platformApi.listTraces({ limit: 50 });
        setTraces(data.items);
      }
    } catch {}
  };

  const handleToggleFlag = async (flag: FeatureFlag) => {
    try {
      const updated = await platformApi.setFeatureFlag({
        flag_key: flag.flag_key,
        is_enabled: !flag.is_enabled,
        name: flag.name,
      });
      setFlags(prev => prev.map(f => f.flag_key === flag.flag_key ? { ...f, is_enabled: updated.is_enabled } : f));
    } catch {}
  };

  return (
    <div style={{ minHeight: "100vh", background: "#0a0f1e", color: "#e2e8f0", fontFamily: "'Inter', sans-serif", display: "flex", flexDirection: "column" }}>
      {/* Header */}
      <nav style={{ background: "rgba(15,23,42,0.95)", borderBottom: "1px solid rgba(99,102,241,0.2)", padding: "0 2rem", height: "60px", display: "flex", alignItems: "center", justifyContent: "space-between", backdropFilter: "blur(12px)", position: "sticky", top: 0, zIndex: 100 }}>
        <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
          <div style={{ fontSize: "1.4rem", fontWeight: 800, background: "linear-gradient(135deg, #6366f1, #8b5cf6)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
            LeadForgeAI
          </div>
          <div style={{ color: "#64748b", fontSize: "0.85rem" }}>/ Enterprise Admin Dashboard</div>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
          <button onClick={() => navigate("/chat")} style={{ background: "none", border: "1px solid rgba(99,102,241,0.3)", color: "#a5b4fc", padding: "0.4rem 1rem", borderRadius: "6px", cursor: "pointer", fontSize: "0.85rem" }}>💬 Chat CRM</button>
          <button onClick={() => navigate("/workflows")} style={{ background: "none", border: "1px solid rgba(99,102,241,0.3)", color: "#94a3b8", padding: "0.4rem 1rem", borderRadius: "6px", cursor: "pointer", fontSize: "0.85rem" }}>⚡ Workflows</button>
          <span style={{ color: "#64748b", fontSize: "0.85rem" }}>{user?.email}</span>
          <button onClick={logout} style={{ background: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.3)", color: "#f87171", padding: "0.4rem 1rem", borderRadius: "6px", cursor: "pointer", fontSize: "0.85rem" }}>Logout</button>
        </div>
      </nav>

      {/* Main Container */}
      <div style={{ flex: 1, padding: "2rem", display: "flex", flexDirection: "column", gap: "1.5rem" }}>
        {/* Navigation Tabs */}
        <div style={{ display: "flex", gap: "0.5rem", borderBottom: "1px solid rgba(99,102,241,0.15)", paddingBottom: "0.5rem" }}>
          {[
            { id: "health", label: "🛡️ System Health & Services" },
            { id: "metrics", label: "📊 Telemetry & Metrics" },
            { id: "flags", label: "⛳ Feature Flags Manager" },
            { id: "audit", label: `📜 Audit Logs (${auditLogs.length})` },
            { id: "traces", label: `🔍 Distributed Traces (${traces.length})` },
          ].map(t => (
            <button key={t.id} onClick={() => setActiveTab(t.id as AdminTab)} style={{ padding: "0.6rem 1.2rem", borderRadius: "8px", border: activeTab === t.id ? "1px solid rgba(99,102,241,0.5)" : "1px solid transparent", background: activeTab === t.id ? "rgba(99,102,241,0.15)" : "transparent", color: activeTab === t.id ? "#a5b4fc" : "#64748b", fontWeight: activeTab === t.id ? 700 : 400, fontSize: "0.85rem", cursor: "pointer" }}>
              {t.label}
            </button>
          ))}
        </div>

        {/* Tab 1: System Health */}
        {activeTab === "health" && (
          <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "1rem" }}>
              {health?.services && Object.entries(health.services).map(([svc, status]) => (
                <div key={svc} style={{ padding: "1.25rem", borderRadius: "10px", border: "1px solid rgba(99,102,241,0.2)", background: "rgba(15,23,42,0.8)", display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                  <div style={{ fontSize: "0.75rem", color: "#64748b", textTransform: "uppercase" }}>{svc.replace("_", " ")}</div>
                  <div style={{ fontSize: "1.1rem", fontWeight: 700, color: status === "healthy" || status === "ready" || status === "active" ? "#34d399" : "#f87171" }}>
                    ● {status.toUpperCase()}
                  </div>
                </div>
              ))}
            </div>
            {health && (
              <div style={{ padding: "1.25rem", borderRadius: "10px", border: "1px solid rgba(99,102,241,0.2)", background: "rgba(15,23,42,0.8)" }}>
                <div style={{ fontSize: "0.85rem", fontWeight: 700, color: "#e2e8f0", marginBottom: "0.5rem" }}>Overall System Health: <span style={{ color: "#34d399" }}>{health.status.toUpperCase()}</span></div>
                <div style={{ fontSize: "0.75rem", color: "#64748b" }}>API Latency: {health.latency_ms}ms | Timestamp: {new Date(health.timestamp * 1000).toLocaleString()}</div>
              </div>
            )}
          </div>
        )}

        {/* Tab 2: Metrics */}
        {activeTab === "metrics" && metrics && (
          <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "1rem" }}>
            <div style={{ padding: "1.25rem", borderRadius: "10px", border: "1px solid rgba(99,102,241,0.2)", background: "rgba(15,23,42,0.8)" }}>
              <div style={{ fontSize: "0.75rem", color: "#64748b" }}>Avg Workflow Duration</div>
              <div style={{ fontSize: "1.5rem", fontWeight: 800, color: "#6366f1", marginTop: "0.4rem" }}>{metrics.workflow_duration_ms_avg.toFixed(1)} ms</div>
            </div>
            <div style={{ padding: "1.25rem", borderRadius: "10px", border: "1px solid rgba(99,102,241,0.2)", background: "rgba(15,23,42,0.8)" }}>
              <div style={{ fontSize: "0.75rem", color: "#64748b" }}>Workflow Executions</div>
              <div style={{ fontSize: "1.5rem", fontWeight: 800, color: "#34d399", marginTop: "0.4rem" }}>{metrics.workflow_success_count} Success / {metrics.workflow_failure_count} Fail</div>
            </div>
            <div style={{ padding: "1.25rem", borderRadius: "10px", border: "1px solid rgba(99,102,241,0.2)", background: "rgba(15,23,42,0.8)" }}>
              <div style={{ fontSize: "0.75rem", color: "#64748b" }}>Avg Tool Duration</div>
              <div style={{ fontSize: "1.5rem", fontWeight: 800, color: "#8b5cf6", marginTop: "0.4rem" }}>{metrics.tool_duration_ms_avg.toFixed(1)} ms</div>
            </div>
            <div style={{ padding: "1.25rem", borderRadius: "10px", border: "1px solid rgba(99,102,241,0.2)", background: "rgba(15,23,42,0.8)" }}>
              <div style={{ fontSize: "0.75rem", color: "#64748b" }}>Planning Time</div>
              <div style={{ fontSize: "1.5rem", fontWeight: 800, color: "#38bdf8", marginTop: "0.4rem" }}>{metrics.average_planning_time_ms.toFixed(1)} ms</div>
            </div>
            <div style={{ padding: "1.25rem", borderRadius: "10px", border: "1px solid rgba(99,102,241,0.2)", background: "rgba(15,23,42,0.8)" }}>
              <div style={{ fontSize: "0.75rem", color: "#64748b" }}>Memory Usage</div>
              <div style={{ fontSize: "1.5rem", fontWeight: 800, color: "#e2e8f0", marginTop: "0.4rem" }}>{metrics.memory_usage_mb} MB</div>
            </div>
            <div style={{ padding: "1.25rem", borderRadius: "10px", border: "1px solid rgba(99,102,241,0.2)", background: "rgba(15,23,42,0.8)" }}>
              <div style={{ fontSize: "0.75rem", color: "#64748b" }}>CPU Utilization</div>
              <div style={{ fontSize: "1.5rem", fontWeight: 800, color: "#e2e8f0", marginTop: "0.4rem" }}>{metrics.cpu_utilization_pct}%</div>
            </div>
          </div>
        )}

        {/* Tab 3: Feature Flags */}
        {activeTab === "flags" && (
          <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
            {flags.map(flag => (
              <div key={flag.flag_key} style={{ padding: "1.25rem", borderRadius: "10px", border: "1px solid rgba(99,102,241,0.2)", background: "rgba(15,23,42,0.8)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <div>
                  <div style={{ fontSize: "0.95rem", fontWeight: 700, color: "#e2e8f0" }}>{flag.name} <code style={{ fontSize: "0.75rem", color: "#6366f1" }}>({flag.flag_key})</code></div>
                  <div style={{ fontSize: "0.75rem", color: "#64748b", marginTop: "0.25rem" }}>{flag.description}</div>
                </div>
                <button onClick={() => handleToggleFlag(flag)} style={{ padding: "0.45rem 1rem", borderRadius: "100px", border: "none", background: flag.is_enabled ? "rgba(16,185,129,0.2)" : "rgba(100,116,139,0.2)", color: flag.is_enabled ? "#34d399" : "#64748b", fontWeight: 700, fontSize: "0.8rem", cursor: "pointer" }}>
                  {flag.is_enabled ? "ENABLED ✅" : "DISABLED ❌"}
                </button>
              </div>
            ))}
          </div>
        )}

        {/* Tab 4: Audit Logs */}
        {activeTab === "audit" && (
          <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
            {auditLogs.map(log => (
              <div key={log.audit_id} style={{ padding: "0.85rem 1rem", borderRadius: "8px", border: "1px solid rgba(99,102,241,0.15)", background: "rgba(15,23,42,0.6)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <div>
                  <div style={{ fontSize: "0.8rem", fontWeight: 700, color: "#a5b4fc" }}>Event: {log.event_type}</div>
                  <div style={{ fontSize: "0.72rem", color: "#64748b" }}>Actor: {log.actor_id} | Correlation: <code style={{ color: "#94a3b8" }}>{log.correlation_id || "N/A"}</code></div>
                </div>
                <span style={{ fontSize: "0.7rem", padding: "0.2rem 0.5rem", borderRadius: "4px", background: log.status === "success" ? "rgba(16,185,129,0.12)" : "rgba(239,68,68,0.12)", color: log.status === "success" ? "#34d399" : "#f87171", fontWeight: 600 }}>{log.status}</span>
              </div>
            ))}
          </div>
        )}

        {/* Tab 5: Distributed Traces */}
        {activeTab === "traces" && (
          <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
            {traces.map(tr => (
              <div key={tr.span_id} style={{ padding: "0.85rem 1rem", borderRadius: "8px", border: "1px solid rgba(99,102,241,0.15)", background: "rgba(15,23,42,0.6)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <div>
                  <div style={{ fontSize: "0.8rem", fontWeight: 700, color: "#e2e8f0" }}>{tr.name}</div>
                  <div style={{ fontSize: "0.72rem", color: "#64748b" }}>Component: <span style={{ color: "#a5b4fc" }}>{tr.component}</span> | Trace ID: <code style={{ color: "#94a3b8" }}>{tr.trace_id}</code></div>
                </div>
                <span style={{ fontSize: "0.75rem", fontWeight: 700, color: "#34d399" }}>{tr.duration_ms.toFixed(1)} ms</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default AdminDashboardPage;
