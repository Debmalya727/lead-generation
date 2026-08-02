import React, { useEffect, useState } from "react";
import { aiApi } from "../../api/ai";
import { NotificationBell } from "../../components/NotificationBell";

export const CacheDashboard: React.FC = () => {
  const [stats, setStats] = useState<any>(null);
  const [purging, setPurging] = useState<boolean>(false);
  const [warming, setWarming] = useState<boolean>(false);
  const [purgeResult, setPurgeResult] = useState<string | null>(null);

  // Cache Warming Form State
  const [warmPrompt, setWarmPrompt] = useState<string>("");
  const [warmResponse, setWarmResponse] = useState<string>("");

  const fetchStats = async () => {
    try {
      const data = await aiApi.getCacheStats();
      setStats(data);
    } catch (err: any) {
      console.error("Failed to fetch cache stats:", err);
    }
  };

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleClearCache = async (scope: string) => {
    setPurging(true);
    setPurgeResult(null);
    try {
      const res = await aiApi.clearCache(scope);
      setPurgeResult(`Purged ${res.cleared_count} keys from scope '${scope}'`);
      await fetchStats();
    } catch (err: any) {
      setPurgeResult(`Purge failed: ${err.message}`);
    } finally {
      setPurging(false);
    }
  };

  const handleWarmCache = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!warmPrompt || !warmResponse) return;
    setWarming(true);
    try {
      await aiApi.warmCache([{ prompt: warmPrompt, response: warmResponse }]);
      setWarmPrompt("");
      setWarmResponse("");
      await fetchStats();
    } catch (err: any) {
      alert(`Warming failed: ${err.message}`);
    } finally {
      setWarming(false);
    }
  };

  const handleExportCache = async () => {
    try {
      const data = await aiApi.exportCache();
      const jsonStr = JSON.stringify(data, null, 2);
      const blob = new Blob([jsonStr], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `cache_snapshot_${new Date().toISOString().slice(0, 10)}.json`;
      a.click();
    } catch (err: any) {
      alert(`Export failed: ${err.message}`);
    }
  };

  return (
    <div style={{ padding: "2rem", color: "#f8fafc", fontFamily: "Inter, sans-serif" }}>
      {/* Top Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "2rem" }}>
        <div>
          <h1 style={{ fontSize: "1.875rem", fontWeight: 700, margin: 0, color: "#fff" }}>
            ⚡ Enterprise AI Cache Platform
          </h1>
          <p style={{ color: "#94a3b8", fontSize: "0.9rem", marginTop: "0.25rem" }}>
            Real-time Prompt, Semantic, Response, Embedding, and Context Cache Telemetry
          </p>
        </div>
        <div style={{ display: "flex", gap: "0.75rem", alignItems: "center" }}>
          <button
            onClick={fetchStats}
            style={{
              padding: "0.5rem 1rem",
              background: "#334155",
              color: "#fff",
              border: "1px solid #475569",
              borderRadius: "6px",
              cursor: "pointer",
            }}
          >
            🔄 Refresh
          </button>
          <button
            onClick={handleExportCache}
            style={{
              padding: "0.5rem 1rem",
              background: "#4f46e5",
              color: "#fff",
              border: "none",
              borderRadius: "6px",
              cursor: "pointer",
              fontWeight: 600,
            }}
          >
            📥 Export Snapshot
          </button>
          <NotificationBell />
        </div>
      </div>

      {/* Main Metric Cards */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "1rem", marginBottom: "2rem" }}>
        <div style={{ background: "#1e293b", padding: "1.25rem", borderRadius: "10px", border: "1px solid #334155" }}>
          <span style={{ color: "#94a3b8", fontSize: "0.8rem", textTransform: "uppercase" }}>Hit Ratio</span>
          <div style={{ fontSize: "2rem", fontWeight: 700, color: "#38bdf8", marginTop: "0.25rem" }}>
            {stats ? `${stats.hit_ratio_percent}%` : "..."}
          </div>
          <span style={{ fontSize: "0.75rem", color: "#64748b" }}>
            {stats ? `${stats.hits} Hits / ${stats.total_requests} Requests` : ""}
          </span>
        </div>

        <div style={{ background: "#1e293b", padding: "1.25rem", borderRadius: "10px", border: "1px solid #334155" }}>
          <span style={{ color: "#94a3b8", fontSize: "0.8rem", textTransform: "uppercase" }}>Saved USD Cost</span>
          <div style={{ fontSize: "2rem", fontWeight: 700, color: "#4ade80", marginTop: "0.25rem" }}>
            {stats ? `$${stats.saved_cost_usd}` : "..."}
          </div>
          <span style={{ fontSize: "0.75rem", color: "#64748b" }}>Accumulated Savings</span>
        </div>

        <div style={{ background: "#1e293b", padding: "1.25rem", borderRadius: "10px", border: "1px solid #334155" }}>
          <span style={{ color: "#94a3b8", fontSize: "0.8rem", textTransform: "uppercase" }}>Saved Tokens</span>
          <div style={{ fontSize: "2rem", fontWeight: 700, color: "#a855f7", marginTop: "0.25rem" }}>
            {stats ? stats.saved_tokens.toLocaleString() : "..."}
          </div>
          <span style={{ fontSize: "0.75rem", color: "#64748b" }}>Tokens Avoided</span>
        </div>

        <div style={{ background: "#1e293b", padding: "1.25rem", borderRadius: "10px", border: "1px solid #334155" }}>
          <span style={{ color: "#94a3b8", fontSize: "0.8rem", textTransform: "uppercase" }}>Saved Latency</span>
          <div style={{ fontSize: "2rem", fontWeight: 700, color: "#fbbf24", marginTop: "0.25rem" }}>
            {stats ? `${stats.saved_latency_seconds}s` : "..."}
          </div>
          <span style={{ fontSize: "0.75rem", color: "#64748b" }}>Total Processing Time Saved</span>
        </div>

        <div style={{ background: "#1e293b", padding: "1.25rem", borderRadius: "10px", border: "1px solid #334155" }}>
          <span style={{ color: "#94a3b8", fontSize: "0.8rem", textTransform: "uppercase" }}>Memory Consumed</span>
          <div style={{ fontSize: "2rem", fontWeight: 700, color: "#f43f5e", marginTop: "0.25rem" }}>
            {stats ? `${stats.memory_consumed_mb} MB` : "..."}
          </div>
          <span style={{ fontSize: "0.75rem", color: "#64748b" }}>
            {stats ? `${stats.lru_memory_keys} LRU Keys` : ""}
          </span>
        </div>
      </div>

      {/* Multi-Tier Distribution & Purge Panel */}
      <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: "1.5rem", marginBottom: "2rem" }}>
        {/* Cache Breakdown */}
        <div style={{ background: "#1e293b", padding: "1.5rem", borderRadius: "10px", border: "1px solid #334155" }}>
          <h3 style={{ margin: "0 0 1rem 0", color: "#f1f5f9" }}>📊 Cache Hit Distribution by Layer</h3>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))", gap: "1rem" }}>
            <div style={{ background: "#0f172a", padding: "1rem", borderRadius: "8px", textAlign: "center" }}>
              <div style={{ fontSize: "1.25rem", fontWeight: 700, color: "#38bdf8" }}>{stats?.prompt_hits || 0}</div>
              <div style={{ fontSize: "0.75rem", color: "#94a3b8", marginTop: "0.25rem" }}>Prompt Hits</div>
            </div>
            <div style={{ background: "#0f172a", padding: "1rem", borderRadius: "8px", textAlign: "center" }}>
              <div style={{ fontSize: "1.25rem", fontWeight: 700, color: "#818cf8" }}>{stats?.semantic_hits || 0}</div>
              <div style={{ fontSize: "0.75rem", color: "#94a3b8", marginTop: "0.25rem" }}>Semantic Hits</div>
            </div>
            <div style={{ background: "#0f172a", padding: "1rem", borderRadius: "8px", textAlign: "center" }}>
              <div style={{ fontSize: "1.25rem", fontWeight: 700, color: "#4ade80" }}>{stats?.response_hits || 0}</div>
              <div style={{ fontSize: "0.75rem", color: "#94a3b8", marginTop: "0.25rem" }}>Response Hits</div>
            </div>
            <div style={{ background: "#0f172a", padding: "1rem", borderRadius: "8px", textAlign: "center" }}>
              <div style={{ fontSize: "1.25rem", fontWeight: 700, color: "#c084fc" }}>{stats?.embedding_hits || 0}</div>
              <div style={{ fontSize: "0.75rem", color: "#94a3b8", marginTop: "0.25rem" }}>Embedding Hits</div>
            </div>
            <div style={{ background: "#0f172a", padding: "1rem", borderRadius: "8px", textAlign: "center" }}>
              <div style={{ fontSize: "1.25rem", fontWeight: 700, color: "#facc15" }}>{stats?.context_hits || 0}</div>
              <div style={{ fontSize: "0.75rem", color: "#94a3b8", marginTop: "0.25rem" }}>Context Hits</div>
            </div>
          </div>
        </div>

        {/* Cache Invalidation & Purge */}
        <div style={{ background: "#1e293b", padding: "1.5rem", borderRadius: "10px", border: "1px solid #334155" }}>
          <h3 style={{ margin: "0 0 1rem 0", color: "#f1f5f9" }}>🧹 Cache Invalidation Controls</h3>
          <p style={{ color: "#94a3b8", fontSize: "0.8rem", marginBottom: "1rem" }}>
            Purge cache entries by specific scope or flush entire Redis/LRU store.
          </p>
          <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
            <button
              onClick={() => handleClearCache("all")}
              disabled={purging}
              style={{
                padding: "0.6rem",
                background: "#ef4444",
                color: "#fff",
                border: "none",
                borderRadius: "6px",
                cursor: "pointer",
                fontWeight: 600,
              }}
            >
              🔥 Purge All Caches
            </button>
            <button
              onClick={() => handleClearCache("response")}
              disabled={purging}
              style={{
                padding: "0.5rem",
                background: "#334155",
                color: "#e2e8f0",
                border: "1px solid #475569",
                borderRadius: "6px",
                cursor: "pointer",
              }}
            >
              Purge Response Cache
            </button>
            <button
              onClick={() => handleClearCache("embedding")}
              disabled={purging}
              style={{
                padding: "0.5rem",
                background: "#334155",
                color: "#e2e8f0",
                border: "1px solid #475569",
                borderRadius: "6px",
                cursor: "pointer",
              }}
            >
              Purge Embedding Cache
            </button>
            <button
              onClick={() => handleClearCache("context")}
              disabled={purging}
              style={{
                padding: "0.5rem",
                background: "#334155",
                color: "#e2e8f0",
                border: "1px solid #475569",
                borderRadius: "6px",
                cursor: "pointer",
              }}
            >
              Purge RAG Context Cache
            </button>
          </div>
          {purgeResult && (
            <div style={{ marginTop: "1rem", padding: "0.5rem", background: "#0f172a", borderRadius: "6px", color: "#38bdf8", fontSize: "0.8rem" }}>
              {purgeResult}
            </div>
          )}
        </div>
      </div>

      {/* Cache Warming Section */}
      <div style={{ background: "#1e293b", padding: "1.5rem", borderRadius: "10px", border: "1px solid #334155" }}>
        <h3 style={{ margin: "0 0 1rem 0", color: "#f1f5f9" }}>🔥 Cache Warming Interface</h3>
        <form onSubmit={handleWarmCache} style={{ display: "grid", gridTemplateColumns: "1fr 1fr auto", gap: "1rem", alignItems: "end" }}>
          <div>
            <label style={{ display: "block", color: "#94a3b8", fontSize: "0.8rem", marginBottom: "0.25rem" }}>
              Prompt Template to Warm
            </label>
            <input
              type="text"
              placeholder="e.g. Summarize company background"
              value={warmPrompt}
              onChange={(e) => setWarmPrompt(e.target.value)}
              style={{
                width: "100%",
                padding: "0.6rem",
                background: "#0f172a",
                border: "1px solid #334155",
                borderRadius: "6px",
                color: "#fff",
              }}
            />
          </div>
          <div>
            <label style={{ display: "block", color: "#94a3b8", fontSize: "0.8rem", marginBottom: "0.25rem" }}>
              Pre-loaded Response Output
            </label>
            <input
              type="text"
              placeholder="e.g. LeadForgeAI enterprise AI platform"
              value={warmResponse}
              onChange={(e) => setWarmResponse(e.target.value)}
              style={{
                width: "100%",
                padding: "0.6rem",
                background: "#0f172a",
                border: "1px solid #334155",
                borderRadius: "6px",
                color: "#fff",
              }}
            />
          </div>
          <button
            type="submit"
            disabled={warming}
            style={{
              padding: "0.6rem 1.25rem",
              background: "#10b981",
              color: "#fff",
              border: "none",
              borderRadius: "6px",
              fontWeight: 600,
              cursor: "pointer",
            }}
          >
            {warming ? "Warming..." : "Warm Cache"}
          </button>
        </form>
      </div>
    </div>
  );
};

export default CacheDashboard;
