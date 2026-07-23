import React, { useEffect, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../contexts/AuthContext";
import { NotificationBell } from "../../components/NotificationBell";

// ─── Type Definitions ─────────────────────────────────────────────────────────
interface AnalyticsKPIs {
  avg_e2e_latency_ms: number;
  avg_ai_latency_ms: number;
  avg_stt_latency_ms: number;
  avg_tts_latency_ms: number;
  avg_packet_loss_pct: number;
  avg_speech_confidence: number;
  avg_silence_pct: number;
  total_interruptions: number;
  total_cost_usd: number;
  total_tokens: number;
  total_events: number;
  total_sessions: number;
}

interface AnalyticsEvent {
  event_id: string;
  session_id: string;
  timestamp: string;
  provider: string;
  e2e_latency_ms: number;
  ai_latency_ms: number;
  stt_latency_ms: number;
  tts_latency_ms: number;
  packet_loss_pct: number;
  speech_confidence: number;
  silence_percentage: number;
  interruption_count: number;
  emotion: string;
  sentiment: string;
  sentiment_score: number;
  total_cost_usd: number;
  total_tokens: number;
}

interface AnalyticsAlert {
  alert_id: string;
  alert_rule_id: string;
  session_id: string;
  severity: string;
  metric_name: string;
  metric_value: number;
  threshold_value: number;
  message: string;
  acknowledged: boolean;
  triggered_at: string;
}

interface AlertRule {
  rule_id: string;
  metric: string;
  operator: string;
  threshold: number;
  severity: string;
  message: string;
}

interface ProviderPerf {
  perf_id: string;
  provider_id: string;
  provider_type: string;
  avg_latency_ms: number;
  p95_latency_ms: number;
  avg_confidence: number;
  error_rate_pct: number;
  avg_cost_per_turn: number;
  total_requests: number;
  uptime_pct: number;
}

interface DailyRollup {
  date_key: string;
  total_sessions: number;
  total_duration_seconds: number;
  avg_ai_latency_ms: number;
  total_cost_usd: number;
  avg_speech_confidence: number;
}

interface DashboardData {
  kpis: AnalyticsKPIs;
  sentiment_distribution: Record<string, number>;
  emotion_distribution: Record<string, number>;
  provider_distribution: Record<string, number>;
  latency_trend: Array<{ turn: number; e2e_latency_ms: number; ai_latency_ms: number }>;
  sessions: any[];
  daily_rollups: DailyRollup[];
  active_alerts: AnalyticsAlert[];
  alert_severity_counts: Record<string, number>;
}

// ─── Helper Components ────────────────────────────────────────────────────────
const badge = (label: string, color = "#a5b4fc", bg = "rgba(99,102,241,0.15)") => (
  <span style={{ fontSize: "0.7rem", padding: "0.15rem 0.5rem", borderRadius: "100px", background: bg, color, fontWeight: 700 }}>
    {label}
  </span>
);

const severityColor = (s: string) =>
  s === "critical" ? "#f87171" : s === "warning" ? "#fbbf24" : "#60a5fa";

const sentimentColor = (s: string) =>
  s === "positive" ? "#34d399" : s === "negative" || s.startsWith("objection") ? "#f87171" : "#94a3b8";

// Simple inline mini bar chart
const MiniBarChart: React.FC<{ data: Record<string, number>; colorMap?: Record<string, string> }> = ({ data, colorMap = {} }) => {
  const max = Math.max(...Object.values(data), 1);
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "0.35rem" }}>
      {Object.entries(data).map(([key, val]) => (
        <div key={key} style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <span style={{ width: "90px", fontSize: "0.75rem", color: "#94a3b8", textTransform: "capitalize", flexShrink: 0 }}>{key}</span>
          <div style={{ flex: 1, background: "rgba(255,255,255,0.05)", borderRadius: "4px", height: "10px", overflow: "hidden" }}>
            <div style={{ width: `${(val / max) * 100}%`, height: "100%", background: colorMap[key] || "#6366f1", borderRadius: "4px", transition: "width 0.5s ease" }} />
          </div>
          <span style={{ fontSize: "0.75rem", color: "#e2e8f0", fontWeight: 700, width: "28px", textAlign: "right" }}>{val}</span>
        </div>
      ))}
    </div>
  );
};

// Mini latency spark line (CSS-only using linear-gradient)
const SparkLine: React.FC<{ data: number[]; color?: string }> = ({ data, color = "#6366f1" }) => {
  const max = Math.max(...data, 1);
  const pts = data.slice(-20);
  return (
    <div style={{ display: "flex", alignItems: "flex-end", gap: "2px", height: "40px" }}>
      {pts.map((v, i) => (
        <div
          key={i}
          style={{
            flex: 1,
            height: `${Math.max(4, (v / max) * 40)}px`,
            background: `${color}`,
            borderRadius: "2px 2px 0 0",
            opacity: 0.6 + (i / pts.length) * 0.4,
            transition: "height 0.3s ease",
          }}
        />
      ))}
    </div>
  );
};

const KPICard: React.FC<{ label: string; value: string; sub?: string; color?: string; trend?: number[] }> = ({
  label, value, sub, color = "#a5b4fc", trend,
}) => (
  <div style={{ background: "rgba(15,23,42,0.9)", border: `1px solid ${color}33`, borderRadius: "14px", padding: "1.25rem", display: "flex", flexDirection: "column", gap: "0.4rem" }}>
    <div style={{ fontSize: "0.75rem", color: "#64748b", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.06em" }}>{label}</div>
    <div style={{ fontSize: "1.8rem", fontWeight: 800, color, lineHeight: 1 }}>{value}</div>
    {sub && <div style={{ fontSize: "0.72rem", color: "#475569" }}>{sub}</div>}
    {trend && trend.length > 3 && (
      <div style={{ marginTop: "0.25rem" }}>
        <SparkLine data={trend} color={color} />
      </div>
    )}
  </div>
);

// ─── Main Page ────────────────────────────────────────────────────────────────
const VoiceAnalyticsDashboardPage: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const [activeTab, setActiveTab] = useState<"overview" | "events" | "alerts" | "providers" | "export">("overview");
  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [events, setEvents] = useState<AnalyticsEvent[]>([]);
  const [alerts, setAlerts] = useState<AnalyticsAlert[]>([]);
  const [alertRules, setAlertRules] = useState<AlertRule[]>([]);
  const [providerPerf, setProviderPerf] = useState<ProviderPerf[]>([]);
  const [dailyRollups, setDailyRollups] = useState<DailyRollup[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // Filter state
  const [filterProvider, setFilterProvider] = useState("");
  const [filterSentiment, setFilterSentiment] = useState("");
  const [filterSeverity, setFilterSeverity] = useState("");
  const [providerType, setProviderType] = useState("stt");

  // Export state
  const [exportFormat, setExportFormat] = useState("csv");
  const [exportResult, setExportResult] = useState<any>(null);
  const [isExporting, setIsExporting] = useState(false);

  // Ingest test event
  const [isIngesting, setIsIngesting] = useState(false);
  const [ingestSessionId] = useState(`demo_sess_${Date.now()}`);

  const token = () => localStorage.getItem("access_token");
  const headers = () => ({ Authorization: `Bearer ${token()}`, "Content-Type": "application/json" });

  const fetchDashboard = useCallback(async () => {
    try {
      const res = await fetch("/api/v1/voice/analytics/dashboard", { headers: { Authorization: `Bearer ${token()}` } });
      const data = await res.json();
      setDashboard(data);
    } catch {}
  }, []);

  const fetchEvents = useCallback(async () => {
    try {
      const params = new URLSearchParams();
      if (filterProvider) params.set("provider", filterProvider);
      if (filterSentiment) params.set("sentiment", filterSentiment);
      params.set("limit", "100");
      const res = await fetch(`/api/v1/voice/analytics/events?${params}`, { headers: { Authorization: `Bearer ${token()}` } });
      const data = await res.json();
      setEvents(Array.isArray(data) ? data : []);
    } catch {}
  }, [filterProvider, filterSentiment]);

  const fetchAlerts = useCallback(async () => {
    try {
      const params = new URLSearchParams();
      if (filterSeverity) params.set("severity", filterSeverity);
      const [alertsRes, rulesRes] = await Promise.all([
        fetch(`/api/v1/voice/analytics/alerts?${params}`, { headers: { Authorization: `Bearer ${token()}` } }),
        fetch("/api/v1/voice/analytics/alerts/rules", { headers: { Authorization: `Bearer ${token()}` } }),
      ]);
      const alertsData = await alertsRes.json();
      const rulesData = await rulesRes.json();
      setAlerts(Array.isArray(alertsData) ? alertsData : []);
      setAlertRules(Array.isArray(rulesData) ? rulesData : []);
    } catch {}
  }, [filterSeverity]);

  const fetchProviderPerf = useCallback(async () => {
    try {
      const res = await fetch(`/api/v1/voice/analytics/provider/performance?provider_type=${providerType}&refresh=true`, { headers: { Authorization: `Bearer ${token()}` } });
      const data = await res.json();
      setProviderPerf(Array.isArray(data) ? data : []);
    } catch {}
  }, [providerType]);

  const fetchDailyRollups = useCallback(async () => {
    try {
      const res = await fetch("/api/v1/voice/analytics/daily?limit=7", { headers: { Authorization: `Bearer ${token()}` } });
      const data = await res.json();
      setDailyRollups(Array.isArray(data) ? data : []);
    } catch {}
  }, []);

  const loadAll = useCallback(async () => {
    setIsLoading(true);
    await Promise.all([fetchDashboard(), fetchEvents(), fetchAlerts(), fetchProviderPerf(), fetchDailyRollups()]);
    setIsLoading(false);
  }, [fetchDashboard, fetchEvents, fetchAlerts, fetchProviderPerf, fetchDailyRollups]);

  useEffect(() => { loadAll(); }, []);
  useEffect(() => { fetchEvents(); }, [filterProvider, filterSentiment]);
  useEffect(() => { fetchAlerts(); }, [filterSeverity]);
  useEffect(() => { fetchProviderPerf(); }, [providerType]);

  const handleIngestDemo = async () => {
    setIsIngesting(true);
    try {
      await fetch("/api/v1/voice/analytics/event", {
        method: "POST",
        headers: headers(),
        body: JSON.stringify({
          session_id: ingestSessionId,
          user_id: user?.id || "demo_user",
          provider: "whisper",
          tts_provider: "elevenlabs",
          speaking_time_ms: 3200 + Math.random() * 2000,
          silence_time_ms: 800 + Math.random() * 500,
          interruption_count: Math.random() > 0.7 ? 1 : 0,
          response_latency_ms: 120 + Math.random() * 80,
          stt_latency_ms: 85 + Math.random() * 60,
          ai_latency_ms: 450 + Math.random() * 300,
          tts_latency_ms: 110 + Math.random() * 50,
          packet_loss_pct: Math.random() * 1.5,
          jitter_ms: 2 + Math.random() * 3,
          speech_confidence: 0.85 + Math.random() * 0.12,
          audio_level_db: -28 + Math.random() * 8,
          emotion: ["neutral", "happy", "excited", "frustrated"][Math.floor(Math.random() * 4)],
          sentiment: ["positive", "neutral", "negative"][Math.floor(Math.random() * 3)],
          sentiment_score: 0.4 + Math.random() * 0.5,
          stt_cost_usd: 0.0008,
          tts_cost_usd: 0.0012,
          ai_cost_usd: 0.003,
          input_tokens: 120 + Math.floor(Math.random() * 80),
          output_tokens: 180 + Math.floor(Math.random() * 120),
          turn_index: events.length,
          transcript_length: 80 + Math.floor(Math.random() * 120),
        }),
      });
      await loadAll();
    } catch {}
    setIsIngesting(false);
  };

  const handleAckAlert = async (alertId: string) => {
    try {
      await fetch(`/api/v1/voice/analytics/alerts/${alertId}/ack`, { method: "POST", headers: headers() });
      await fetchAlerts();
    } catch {}
  };

  const handleResolveAll = async () => {
    try {
      await fetch("/api/v1/voice/analytics/alerts/resolve-all", { method: "POST", headers: headers() });
      await fetchAlerts();
    } catch {}
  };

  const handleExport = async () => {
    setIsExporting(true);
    try {
      const res = await fetch("/api/v1/voice/analytics/export", {
        method: "POST",
        headers: headers(),
        body: JSON.stringify({ export_format: exportFormat, limit: 500 }),
      });
      const data = await res.json();
      setExportResult(data);
    } catch {}
    setIsExporting(false);
  };

  const handleDailyRollup = async () => {
    try {
      await fetch("/api/v1/voice/analytics/daily/rollup", {
        method: "POST",
        headers: headers(),
        body: JSON.stringify({}),
      });
      await fetchDailyRollups();
      await fetchDashboard();
    } catch {}
  };

  const kpis = dashboard?.kpis;
  const latencyTrend = (dashboard?.latency_trend || []).map(t => t.e2e_latency_ms);
  const aiTrend = (dashboard?.latency_trend || []).map(t => t.ai_latency_ms);

  return (
    <div style={{ minHeight: "100vh", background: "#0a0f1e", color: "#e2e8f0", fontFamily: "'Inter', sans-serif", display: "flex", flexDirection: "column" }}>

      {/* Nav */}
      <nav style={{ background: "rgba(15,23,42,0.97)", borderBottom: "1px solid rgba(16,185,129,0.2)", padding: "0 2rem", height: "60px", display: "flex", alignItems: "center", justifyContent: "space-between", backdropFilter: "blur(12px)", position: "sticky", top: 0, zIndex: 100 }}>
        <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
          <div style={{ fontSize: "1.4rem", fontWeight: 800, background: "linear-gradient(135deg, #10b981, #34d399)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
            LeadForgeAI
          </div>
          <div style={{ color: "#64748b", fontSize: "0.85rem" }}>/ Voice Analytics</div>
          {badge("Phase 13.10", "#34d399", "rgba(52,211,153,0.12)")}
        </div>

        {/* Tab Switcher */}
        <div style={{ display: "flex", gap: "0.35rem" }}>
          {(["overview", "events", "alerts", "providers", "export"] as const).map(tab => (
            <button key={tab} onClick={() => setActiveTab(tab)} style={{
              padding: "0.4rem 0.85rem", borderRadius: "6px", fontSize: "0.8rem", fontWeight: 600, cursor: "pointer",
              border: activeTab === tab ? "1px solid #10b981" : "1px solid transparent",
              background: activeTab === tab ? "rgba(16,185,129,0.15)" : "none",
              color: activeTab === tab ? "#34d399" : "#94a3b8",
            }}>
              {tab === "overview" ? "📊 Overview" : tab === "events" ? "⚡ Events" : tab === "alerts" ? "🔔 Alerts" : tab === "providers" ? "🔗 Providers" : "📤 Export"}
            </button>
          ))}
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
          <button onClick={handleIngestDemo} disabled={isIngesting} style={{ padding: "0.4rem 0.9rem", borderRadius: "6px", border: "1px solid rgba(16,185,129,0.4)", background: "rgba(16,185,129,0.1)", color: "#34d399", fontWeight: 700, fontSize: "0.8rem", cursor: "pointer" }}>
            {isIngesting ? "⏳" : "➕"} Ingest Demo
          </button>
          <button onClick={loadAll} style={{ padding: "0.4rem 0.75rem", borderRadius: "6px", border: "1px solid rgba(99,102,241,0.3)", background: "none", color: "#a5b4fc", fontSize: "0.8rem", cursor: "pointer" }}>↻ Refresh</button>
          <NotificationBell />
          <button onClick={() => navigate("/voice")} style={{ background: "none", border: "1px solid rgba(99,102,241,0.3)", color: "#a5b4fc", padding: "0.4rem 1rem", borderRadius: "6px", cursor: "pointer", fontSize: "0.85rem" }}>🎙️ Voice</button>
          <button onClick={logout} style={{ background: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.3)", color: "#f87171", padding: "0.4rem 1rem", borderRadius: "6px", cursor: "pointer", fontSize: "0.85rem" }}>Logout</button>
        </div>
      </nav>

      <main style={{ flex: 1, padding: "2rem", display: "flex", flexDirection: "column", gap: "1.5rem", maxWidth: "1600px", margin: "0 auto", width: "100%", boxSizing: "border-box" }}>

        {isLoading && (
          <div style={{ textAlign: "center", padding: "4rem", color: "#64748b" }}>⏳ Loading Voice Analytics...</div>
        )}

        {/* ── OVERVIEW TAB ─────────────────────────────────────────────────── */}
        {!isLoading && activeTab === "overview" && (
          <>
            {/* Page header */}
            <div style={{ background: "linear-gradient(135deg, rgba(16,185,129,0.12), rgba(52,211,153,0.06))", border: "1px solid rgba(16,185,129,0.25)", borderRadius: "16px", padding: "1.5rem 2rem", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div>
                <h1 style={{ margin: 0, fontSize: "1.6rem", fontWeight: 800, background: "linear-gradient(135deg, #10b981, #34d399)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
                  📊 Voice Analytics Dashboard
                </h1>
                <p style={{ margin: "0.3rem 0 0", color: "#94a3b8", fontSize: "0.9rem" }}>
                  Real-time observability for speaking time · latency · sentiment · cost · provider performance
                </p>
              </div>
              <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
                {badge(`${kpis?.total_sessions ?? 0} Sessions`, "#a5b4fc")}
                {badge(`${kpis?.total_events ?? 0} Events`, "#34d399")}
                {badge(`$${kpis?.total_cost_usd?.toFixed(4) ?? "0.0000"}`, "#fbbf24", "rgba(251,191,36,0.12)")}
                {dashboard?.alert_severity_counts?.critical ? badge(`${dashboard.alert_severity_counts.critical} Critical`, "#f87171", "rgba(248,113,113,0.12)") : null}
              </div>
            </div>

            {/* KPI Cards Row 1 */}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "1rem" }}>
              <KPICard label="Avg E2E Latency" value={`${kpis?.avg_e2e_latency_ms?.toFixed(0) ?? "—"}ms`} sub="Full pipeline" color="#34d399" trend={latencyTrend} />
              <KPICard label="Avg AI Latency" value={`${kpis?.avg_ai_latency_ms?.toFixed(0) ?? "—"}ms`} sub="LLM response time" color="#a5b4fc" trend={aiTrend} />
              <KPICard label="Avg STT Latency" value={`${kpis?.avg_stt_latency_ms?.toFixed(0) ?? "—"}ms`} sub="Speech recognition" color="#60a5fa" />
              <KPICard label="Avg TTS Latency" value={`${kpis?.avg_tts_latency_ms?.toFixed(0) ?? "—"}ms`} sub="Speech synthesis" color="#f472b6" />
            </div>

            {/* KPI Cards Row 2 */}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "1rem" }}>
              <KPICard label="Packet Loss" value={`${kpis?.avg_packet_loss_pct?.toFixed(2) ?? "0.00"}%`} sub="Network quality" color={kpis && kpis.avg_packet_loss_pct > 3 ? "#f87171" : "#34d399"} />
              <KPICard label="Speech Confidence" value={`${((kpis?.avg_speech_confidence ?? 0) * 100).toFixed(1)}%`} sub="STT accuracy" color="#fbbf24" />
              <KPICard label="Silence %" value={`${kpis?.avg_silence_pct?.toFixed(1) ?? "0.0"}%`} sub="Avg per session" color="#94a3b8" />
              <KPICard label="Interruptions" value={`${kpis?.total_interruptions ?? 0}`} sub="Total across all sessions" color="#fb923c" />
            </div>

            {/* Row 3: Cost + Tokens + Alerts */}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "1rem" }}>
              <KPICard label="Total Cost" value={`$${kpis?.total_cost_usd?.toFixed(4) ?? "0.0000"}`} sub="STT + AI + TTS combined" color="#fbbf24" />
              <KPICard label="Total Tokens" value={`${(kpis?.total_tokens ?? 0).toLocaleString()}`} sub="Cumulative AI tokens" color="#a5b4fc" />
              <div style={{ background: "rgba(15,23,42,0.9)", border: "1px solid rgba(248,113,113,0.2)", borderRadius: "14px", padding: "1.25rem" }}>
                <div style={{ fontSize: "0.75rem", color: "#64748b", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: "0.75rem" }}>Active Alerts</div>
                <div style={{ display: "flex", gap: "1rem" }}>
                  {["critical", "warning", "info"].map(sev => (
                    <div key={sev} style={{ textAlign: "center" }}>
                      <div style={{ fontSize: "1.6rem", fontWeight: 800, color: severityColor(sev) }}>
                        {dashboard?.alert_severity_counts?.[sev] ?? 0}
                      </div>
                      <div style={{ fontSize: "0.72rem", color: "#475569", textTransform: "capitalize" }}>{sev}</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Row 4: Charts — Sentiment + Emotion + Provider */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "1.5rem" }}>
              <div style={{ background: "rgba(15,23,42,0.9)", border: "1px solid rgba(99,102,241,0.2)", borderRadius: "14px", padding: "1.5rem" }}>
                <h3 style={{ margin: "0 0 1rem", fontSize: "0.95rem", fontWeight: 700, color: "#a5b4fc" }}>💬 Sentiment Distribution</h3>
                {dashboard?.sentiment_distribution && Object.keys(dashboard.sentiment_distribution).length > 0 ? (
                  <MiniBarChart data={dashboard.sentiment_distribution} colorMap={{ positive: "#34d399", neutral: "#64748b", negative: "#f87171", objection_price: "#fb923c" }} />
                ) : <div style={{ color: "#475569", fontSize: "0.85rem" }}>No data yet. Ingest a demo event.</div>}
              </div>

              <div style={{ background: "rgba(15,23,42,0.9)", border: "1px solid rgba(99,102,241,0.2)", borderRadius: "14px", padding: "1.5rem" }}>
                <h3 style={{ margin: "0 0 1rem", fontSize: "0.95rem", fontWeight: 700, color: "#f472b6" }}>🎭 Emotion Trends</h3>
                {dashboard?.emotion_distribution && Object.keys(dashboard.emotion_distribution).length > 0 ? (
                  <MiniBarChart data={dashboard.emotion_distribution} colorMap={{ happy: "#34d399", neutral: "#64748b", frustrated: "#f87171", excited: "#fbbf24", sad: "#60a5fa" }} />
                ) : <div style={{ color: "#475569", fontSize: "0.85rem" }}>No data yet.</div>}
              </div>

              <div style={{ background: "rgba(15,23,42,0.9)", border: "1px solid rgba(99,102,241,0.2)", borderRadius: "14px", padding: "1.5rem" }}>
                <h3 style={{ margin: "0 0 1rem", fontSize: "0.95rem", fontWeight: 700, color: "#fbbf24" }}>🔗 Provider Usage</h3>
                {dashboard?.provider_distribution && Object.keys(dashboard.provider_distribution).length > 0 ? (
                  <MiniBarChart data={dashboard.provider_distribution} colorMap={{ whisper: "#6366f1", deepgram: "#f472b6", google: "#fbbf24", azure: "#60a5fa", assemblyai: "#34d399" }} />
                ) : <div style={{ color: "#475569", fontSize: "0.85rem" }}>No data yet.</div>}
              </div>
            </div>

            {/* Row 5: Latency Spark + Daily Trend */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.5rem" }}>
              <div style={{ background: "rgba(15,23,42,0.9)", border: "1px solid rgba(16,185,129,0.2)", borderRadius: "14px", padding: "1.5rem" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.75rem" }}>
                  <h3 style={{ margin: 0, fontSize: "0.95rem", fontWeight: 700, color: "#34d399" }}>📈 E2E Latency Trend</h3>
                  <span style={{ fontSize: "0.75rem", color: "#64748b" }}>Last {latencyTrend.length} turns</span>
                </div>
                {latencyTrend.length > 0 ? (
                  <SparkLine data={latencyTrend} color="#34d399" />
                ) : <div style={{ color: "#475569", fontSize: "0.85rem", textAlign: "center", padding: "1rem" }}>Ingest events to see trend</div>}
                <div style={{ display: "flex", gap: "1rem", marginTop: "0.75rem" }}>
                  <div style={{ fontSize: "0.75rem", color: "#64748b" }}>Min: <span style={{ color: "#34d399" }}>{latencyTrend.length ? Math.min(...latencyTrend).toFixed(0) : "—"}ms</span></div>
                  <div style={{ fontSize: "0.75rem", color: "#64748b" }}>Max: <span style={{ color: "#f87171" }}>{latencyTrend.length ? Math.max(...latencyTrend).toFixed(0) : "—"}ms</span></div>
                  <div style={{ fontSize: "0.75rem", color: "#64748b" }}>Avg: <span style={{ color: "#a5b4fc" }}>{kpis?.avg_e2e_latency_ms.toFixed(0) ?? "—"}ms</span></div>
                </div>
              </div>

              <div style={{ background: "rgba(15,23,42,0.9)", border: "1px solid rgba(251,191,36,0.2)", borderRadius: "14px", padding: "1.5rem" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.75rem" }}>
                  <h3 style={{ margin: 0, fontSize: "0.95rem", fontWeight: 700, color: "#fbbf24" }}>📅 Daily Cost Trend</h3>
                  <button onClick={handleDailyRollup} style={{ fontSize: "0.75rem", background: "rgba(251,191,36,0.1)", border: "1px solid rgba(251,191,36,0.3)", color: "#fbbf24", padding: "0.25rem 0.6rem", borderRadius: "6px", cursor: "pointer" }}>Run Rollup</button>
                </div>
                {dailyRollups.length > 0 ? (
                  <div style={{ display: "flex", flexDirection: "column", gap: "0.4rem" }}>
                    {dailyRollups.map(d => (
                      <div key={d.date_key} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", background: "rgba(255,255,255,0.03)", borderRadius: "6px", padding: "0.4rem 0.75rem" }}>
                        <span style={{ color: "#94a3b8", fontSize: "0.8rem" }}>{d.date_key}</span>
                        <div style={{ display: "flex", gap: "1rem" }}>
                          <span style={{ fontSize: "0.78rem", color: "#64748b" }}>{d.total_sessions}s</span>
                          <span style={{ fontSize: "0.78rem", color: "#fbbf24", fontWeight: 700 }}>${d.total_cost_usd.toFixed(4)}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : <div style={{ color: "#475569", fontSize: "0.85rem", textAlign: "center", padding: "1rem" }}>No daily rollups yet. Click "Run Rollup".</div>}
              </div>
            </div>
          </>
        )}

        {/* ── EVENTS TAB ───────────────────────────────────────────────────── */}
        {!isLoading && activeTab === "events" && (
          <>
            <div style={{ background: "rgba(15,23,42,0.9)", border: "1px solid rgba(16,185,129,0.2)", borderRadius: "14px", padding: "1.5rem" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem", flexWrap: "wrap", gap: "0.75rem" }}>
                <h2 style={{ margin: 0, fontSize: "1.15rem", fontWeight: 700, color: "#34d399" }}>⚡ Analytics Events ({events.length})</h2>
                <div style={{ display: "flex", gap: "0.6rem", flexWrap: "wrap" }}>
                  <select value={filterProvider} onChange={e => setFilterProvider(e.target.value)} style={{ background: "rgba(10,15,30,0.8)", border: "1px solid rgba(16,185,129,0.25)", color: "#e2e8f0", padding: "0.4rem 0.6rem", borderRadius: "6px", fontSize: "0.82rem" }}>
                    <option value="">All Providers</option>
                    {["whisper", "deepgram", "google", "azure", "assemblyai", "faster_whisper"].map(p => <option key={p} value={p}>{p}</option>)}
                  </select>
                  <select value={filterSentiment} onChange={e => setFilterSentiment(e.target.value)} style={{ background: "rgba(10,15,30,0.8)", border: "1px solid rgba(16,185,129,0.25)", color: "#e2e8f0", padding: "0.4rem 0.6rem", borderRadius: "6px", fontSize: "0.82rem" }}>
                    <option value="">All Sentiments</option>
                    {["positive", "neutral", "negative", "objection_price"].map(s => <option key={s} value={s}>{s}</option>)}
                  </select>
                  <button onClick={fetchEvents} style={{ padding: "0.4rem 0.75rem", borderRadius: "6px", border: "1px solid rgba(16,185,129,0.3)", background: "rgba(16,185,129,0.1)", color: "#34d399", fontSize: "0.8rem", cursor: "pointer" }}>Filter</button>
                </div>
              </div>

              {events.length === 0 ? (
                <div style={{ textAlign: "center", padding: "3rem", color: "#475569" }}>No events found. Ingest a demo event from the top nav.</div>
              ) : (
                <div style={{ overflowX: "auto" }}>
                  <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.8rem" }}>
                    <thead>
                      <tr style={{ borderBottom: "1px solid rgba(255,255,255,0.08)" }}>
                        {["Time", "Session", "Provider", "E2E", "AI", "STT", "Packet Loss", "Confidence", "Silence%", "Interrupts", "Emotion", "Sentiment", "Cost", "Tokens"].map(h => (
                          <th key={h} style={{ padding: "0.5rem 0.6rem", textAlign: "left", color: "#475569", fontWeight: 700, fontSize: "0.72rem", textTransform: "uppercase", whiteSpace: "nowrap" }}>{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {events.map((ev, i) => (
                        <tr key={ev.event_id || i} style={{ borderBottom: "1px solid rgba(255,255,255,0.04)" }}>
                          <td style={{ padding: "0.45rem 0.6rem", color: "#64748b", fontSize: "0.72rem", whiteSpace: "nowrap" }}>{new Date(ev.timestamp).toLocaleTimeString()}</td>
                          <td style={{ padding: "0.45rem 0.6rem", color: "#a5b4fc", fontFamily: "monospace", fontSize: "0.72rem" }}>{(ev.session_id || "").substring(0, 12)}…</td>
                          <td style={{ padding: "0.45rem 0.6rem", color: "#e2e8f0" }}>{ev.provider}</td>
                          <td style={{ padding: "0.45rem 0.6rem", color: ev.e2e_latency_ms > 1500 ? "#f87171" : "#34d399", fontWeight: 700 }}>{ev.e2e_latency_ms?.toFixed(0)}ms</td>
                          <td style={{ padding: "0.45rem 0.6rem", color: ev.ai_latency_ms > 1200 ? "#fbbf24" : "#a5b4fc" }}>{ev.ai_latency_ms?.toFixed(0)}ms</td>
                          <td style={{ padding: "0.45rem 0.6rem", color: "#60a5fa" }}>{ev.stt_latency_ms?.toFixed(0)}ms</td>
                          <td style={{ padding: "0.45rem 0.6rem", color: ev.packet_loss_pct > 3 ? "#f87171" : "#34d399" }}>{ev.packet_loss_pct?.toFixed(2)}%</td>
                          <td style={{ padding: "0.45rem 0.6rem", color: ev.speech_confidence < 0.7 ? "#fbbf24" : "#34d399" }}>{(ev.speech_confidence * 100)?.toFixed(1)}%</td>
                          <td style={{ padding: "0.45rem 0.6rem", color: ev.silence_percentage > 50 ? "#fbbf24" : "#94a3b8" }}>{ev.silence_percentage?.toFixed(1)}%</td>
                          <td style={{ padding: "0.45rem 0.6rem", color: ev.interruption_count > 0 ? "#fb923c" : "#64748b", fontWeight: ev.interruption_count > 0 ? 700 : 400 }}>{ev.interruption_count}</td>
                          <td style={{ padding: "0.45rem 0.6rem" }}>{badge(ev.emotion, ev.emotion === "happy" || ev.emotion === "excited" ? "#34d399" : ev.emotion === "frustrated" ? "#f87171" : "#94a3b8")}</td>
                          <td style={{ padding: "0.45rem 0.6rem" }}>{badge(ev.sentiment, sentimentColor(ev.sentiment))}</td>
                          <td style={{ padding: "0.45rem 0.6rem", color: "#fbbf24", fontFamily: "monospace" }}>${ev.total_cost_usd?.toFixed(4)}</td>
                          <td style={{ padding: "0.45rem 0.6rem", color: "#94a3b8" }}>{ev.total_tokens?.toLocaleString()}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </>
        )}

        {/* ── ALERTS TAB ───────────────────────────────────────────────────── */}
        {!isLoading && activeTab === "alerts" && (
          <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.5rem" }}>

              {/* Active Alerts */}
              <div style={{ background: "rgba(15,23,42,0.9)", border: "1px solid rgba(248,113,113,0.2)", borderRadius: "14px", padding: "1.5rem" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
                  <h3 style={{ margin: 0, color: "#f87171", fontWeight: 700 }}>🔔 Active Alerts ({alerts.length})</h3>
                  <div style={{ display: "flex", gap: "0.5rem" }}>
                    <select value={filterSeverity} onChange={e => setFilterSeverity(e.target.value)} style={{ background: "rgba(10,15,30,0.8)", border: "1px solid rgba(248,113,113,0.25)", color: "#e2e8f0", padding: "0.35rem 0.5rem", borderRadius: "6px", fontSize: "0.8rem" }}>
                      <option value="">All</option>
                      <option value="critical">Critical</option>
                      <option value="warning">Warning</option>
                      <option value="info">Info</option>
                    </select>
                    <button onClick={handleResolveAll} style={{ padding: "0.35rem 0.75rem", borderRadius: "6px", border: "1px solid rgba(248,113,113,0.3)", background: "rgba(248,113,113,0.1)", color: "#f87171", fontSize: "0.8rem", cursor: "pointer" }}>Resolve All</button>
                  </div>
                </div>
                {alerts.length === 0 ? (
                  <div style={{ color: "#475569", textAlign: "center", padding: "2rem" }}>✅ No active alerts</div>
                ) : (
                  <div style={{ display: "flex", flexDirection: "column", gap: "0.6rem", maxHeight: "400px", overflowY: "auto" }}>
                    {alerts.map(a => (
                      <div key={a.alert_id} style={{ background: "rgba(10,15,30,0.8)", border: `1px solid ${severityColor(a.severity)}33`, borderRadius: "8px", padding: "0.75rem" }}>
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                          <div>
                            {badge(a.severity.toUpperCase(), severityColor(a.severity))}
                            <div style={{ color: "#e2e8f0", fontSize: "0.85rem", marginTop: "0.3rem", fontWeight: 600 }}>{a.message}</div>
                            <div style={{ color: "#64748b", fontSize: "0.75rem", marginTop: "0.2rem" }}>
                              {a.metric_name}: <span style={{ color: severityColor(a.severity) }}>{a.metric_value.toFixed(2)}</span> &gt; {a.threshold_value}
                            </div>
                          </div>
                          <button onClick={() => handleAckAlert(a.alert_id)} style={{ fontSize: "0.72rem", background: "rgba(52,211,153,0.1)", border: "1px solid rgba(52,211,153,0.3)", color: "#34d399", padding: "0.2rem 0.5rem", borderRadius: "4px", cursor: "pointer" }}>✓ Ack</button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Alert Rules */}
              <div style={{ background: "rgba(15,23,42,0.9)", border: "1px solid rgba(251,191,36,0.2)", borderRadius: "14px", padding: "1.5rem" }}>
                <h3 style={{ margin: "0 0 1rem", color: "#fbbf24", fontWeight: 700 }}>⚙️ Alert Rules ({alertRules.length})</h3>
                <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                  {alertRules.map(r => (
                    <div key={r.rule_id} style={{ background: "rgba(10,15,30,0.8)", border: `1px solid ${severityColor(r.severity)}22`, borderRadius: "8px", padding: "0.6rem 0.75rem", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                      <div>
                        <div style={{ color: "#e2e8f0", fontSize: "0.82rem", fontWeight: 600 }}>{r.metric}</div>
                        <div style={{ color: "#64748b", fontSize: "0.72rem" }}>{r.operator.toUpperCase()} {r.threshold} → {r.message}</div>
                      </div>
                      {badge(r.severity, severityColor(r.severity))}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ── PROVIDERS TAB ────────────────────────────────────────────────── */}
        {!isLoading && activeTab === "providers" && (
          <div style={{ background: "rgba(15,23,42,0.9)", border: "1px solid rgba(99,102,241,0.2)", borderRadius: "14px", padding: "1.5rem" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem", flexWrap: "wrap", gap: "0.75rem" }}>
              <h2 style={{ margin: 0, color: "#a5b4fc", fontWeight: 700 }}>🔗 Provider Performance Comparison</h2>
              <div style={{ display: "flex", gap: "0.5rem" }}>
                {["stt", "tts", "telephony"].map(pt => (
                  <button key={pt} onClick={() => setProviderType(pt)} style={{ padding: "0.4rem 0.85rem", borderRadius: "6px", border: providerType === pt ? "1px solid #6366f1" : "1px solid transparent", background: providerType === pt ? "rgba(99,102,241,0.2)" : "rgba(255,255,255,0.04)", color: providerType === pt ? "#a5b4fc" : "#94a3b8", fontWeight: 600, fontSize: "0.8rem", cursor: "pointer", textTransform: "uppercase" }}>{pt}</button>
                ))}
              </div>
            </div>

            {providerPerf.length === 0 ? (
              <div style={{ textAlign: "center", padding: "3rem", color: "#475569" }}>Loading provider benchmarks…</div>
            ) : (
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.82rem" }}>
                <thead>
                  <tr style={{ borderBottom: "1px solid rgba(255,255,255,0.08)" }}>
                    {["Provider", "Avg Latency", "P95 Latency", "Confidence", "Error Rate", "Cost/Turn", "Requests", "Uptime"].map(h => (
                      <th key={h} style={{ padding: "0.5rem 0.75rem", textAlign: "left", color: "#475569", fontWeight: 700, fontSize: "0.75rem", textTransform: "uppercase" }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {providerPerf.map((p, i) => (
                    <tr key={p.perf_id || i} style={{ borderBottom: "1px solid rgba(255,255,255,0.04)" }}>
                      <td style={{ padding: "0.55rem 0.75rem", color: "#e2e8f0", fontWeight: 700 }}>{p.provider_id}</td>
                      <td style={{ padding: "0.55rem 0.75rem", color: p.avg_latency_ms < 200 ? "#34d399" : p.avg_latency_ms < 400 ? "#fbbf24" : "#f87171", fontWeight: 600 }}>{p.avg_latency_ms?.toFixed(1)}ms</td>
                      <td style={{ padding: "0.55rem 0.75rem", color: "#94a3b8" }}>{p.p95_latency_ms?.toFixed(1)}ms</td>
                      <td style={{ padding: "0.55rem 0.75rem", color: "#a5b4fc" }}>{((p.avg_confidence || 0) * 100).toFixed(1)}%</td>
                      <td style={{ padding: "0.55rem 0.75rem", color: p.error_rate_pct > 2 ? "#f87171" : "#34d399" }}>{p.error_rate_pct?.toFixed(2)}%</td>
                      <td style={{ padding: "0.55rem 0.75rem", color: "#fbbf24", fontFamily: "monospace" }}>${p.avg_cost_per_turn?.toFixed(6)}</td>
                      <td style={{ padding: "0.55rem 0.75rem", color: "#64748b" }}>{p.total_requests?.toLocaleString()}</td>
                      <td style={{ padding: "0.55rem 0.75rem", color: p.uptime_pct > 99 ? "#34d399" : "#fbbf24", fontWeight: 600 }}>{p.uptime_pct?.toFixed(1)}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}

        {/* ── EXPORT TAB ───────────────────────────────────────────────────── */}
        {!isLoading && activeTab === "export" && (
          <div style={{ display: "grid", gridTemplateColumns: "350px 1fr", gap: "1.5rem" }}>
            <div style={{ background: "rgba(15,23,42,0.9)", border: "1px solid rgba(99,102,241,0.2)", borderRadius: "14px", padding: "1.5rem", display: "flex", flexDirection: "column", gap: "1rem" }}>
              <h2 style={{ margin: 0, color: "#a5b4fc", fontWeight: 700 }}>📤 Export Analytics</h2>
              <div>
                <label style={{ fontSize: "0.8rem", color: "#94a3b8", fontWeight: 600, display: "block", marginBottom: "0.4rem" }}>Format</label>
                <div style={{ display: "flex", gap: "0.5rem" }}>
                  {["csv", "json"].map(fmt => (
                    <button key={fmt} onClick={() => setExportFormat(fmt)} style={{ flex: 1, padding: "0.5rem", borderRadius: "6px", border: exportFormat === fmt ? "1px solid #6366f1" : "1px solid transparent", background: exportFormat === fmt ? "rgba(99,102,241,0.15)" : "rgba(255,255,255,0.04)", color: exportFormat === fmt ? "#a5b4fc" : "#94a3b8", fontWeight: 600, fontSize: "0.85rem", cursor: "pointer", textTransform: "uppercase" }}>{fmt}</button>
                  ))}
                </div>
              </div>
              <div style={{ fontSize: "0.8rem", color: "#64748b" }}>Exports up to 500 most recent analytics events. Includes all metrics: latency, sentiment, emotion, cost, tokens, and provider data.</div>
              <button onClick={handleExport} disabled={isExporting} style={{ padding: "0.7rem", borderRadius: "8px", border: "none", background: isExporting ? "rgba(100,100,100,0.5)" : "linear-gradient(135deg, #6366f1, #8b5cf6)", color: "#fff", fontWeight: 700, fontSize: "0.9rem", cursor: isExporting ? "default" : "pointer" }}>
                {isExporting ? "⏳ Generating..." : "📤 Generate Export"}
              </button>
            </div>

            <div style={{ background: "rgba(15,23,42,0.9)", border: "1px solid rgba(16,185,129,0.2)", borderRadius: "14px", padding: "1.5rem" }}>
              {!exportResult ? (
                <div style={{ textAlign: "center", padding: "4rem", color: "#475569" }}>Select format and click "Generate Export" to download analytics data.</div>
              ) : (
                <>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
                    <h3 style={{ margin: 0, color: "#34d399", fontWeight: 700 }}>✅ Export Ready</h3>
                    <div style={{ display: "flex", gap: "0.5rem" }}>
                      {badge(`${exportResult.row_count} rows`, "#34d399", "rgba(52,211,153,0.12)")}
                      {badge(exportResult.format.toUpperCase(), "#a5b4fc")}
                    </div>
                  </div>
                  <div style={{ color: "#64748b", fontSize: "0.8rem", marginBottom: "0.75rem" }}>Export ID: <span style={{ color: "#a5b4fc", fontFamily: "monospace" }}>{exportResult.export_id}</span></div>
                  <div style={{ background: "rgba(10,15,30,0.8)", border: "1px solid rgba(52,211,153,0.15)", borderRadius: "8px", padding: "0.75rem", maxHeight: "400px", overflowY: "auto" }}>
                    <div style={{ fontSize: "0.75rem", color: "#64748b", fontWeight: 700, marginBottom: "0.5rem" }}>Preview (first 5 rows):</div>
                    {(exportResult.data || []).slice(0, 5).map((row: any, i: number) => (
                      <div key={i} style={{ background: "rgba(255,255,255,0.03)", borderRadius: "6px", padding: "0.4rem 0.6rem", marginBottom: "0.3rem", fontSize: "0.72rem", fontFamily: "monospace", color: "#94a3b8" }}>
                        {JSON.stringify(row)}
                      </div>
                    ))}
                  </div>
                </>
              )}
            </div>
          </div>
        )}

      </main>
    </div>
  );
};

export default VoiceAnalyticsDashboardPage;
