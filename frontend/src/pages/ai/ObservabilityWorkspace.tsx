import React, { useEffect, useState } from "react";
import { aiApi } from "../../api/ai";
import { NotificationBell } from "../../components/NotificationBell";

export const ObservabilityWorkspace: React.FC = () => {
  const [overview, setOverview] = useState<any>(null);
  const [traces, setTraces] = useState<any[]>([]);
  const [alerts, setAlerts] = useState<any[]>([]);
  const [prometheusText, setPrometheusText] = useState<string>("");
  const [showPrometheus, setShowPrometheus] = useState<boolean>(false);

  // Manual Alert Trigger State
  const [alertType, setAlertType] = useState<string>("LATENCY_ANOMALY");
  const [severity, setSeverity] = useState<string>("WARNING");
  const [alertMessage, setAlertMessage] = useState<string>("High latency spike detected on AI Gateway provider route.");
  const [dispatching, setDispatching] = useState<boolean>(false);

  const fetchObservabilityData = async () => {
    try {
      const [overviewData, tracesData, alertsData] = await Promise.all([
        aiApi.getObservabilityOverview(),
        aiApi.getDistributedTraces(50),
        aiApi.getObservabilityAlerts(50),
      ]);
      setOverview(overviewData);
      setTraces(tracesData);
      setAlerts(alertsData);
    } catch (err: any) {
      console.error("Failed to fetch observability data:", err);
    }
  };

  const handleFetchPrometheus = async () => {
    try {
      const text = await aiApi.getPrometheusMetrics();
      setPrometheusText(text);
      setShowPrometheus(true);
    } catch (err: any) {
      alert(`Failed to fetch Prometheus metrics: ${err.message}`);
    }
  };

  const handleTriggerAlert = async () => {
    if (!alertMessage.trim()) return;
    setDispatching(true);
    try {
      await aiApi.triggerObservabilityAlert({
        alert_type: alertType,
        severity: severity,
        source_component: "Observability Workspace UI",
        message: alertMessage,
      });
      alert("Alert successfully dispatched!");
      await fetchObservabilityData();
    } catch (err: any) {
      alert(`Alert dispatch failed: ${err.message}`);
    } finally {
      setDispatching(false);
    }
  };

  useEffect(() => {
    fetchObservabilityData();
    const interval = setInterval(fetchObservabilityData, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div style={{ padding: "2rem", color: "#f8fafc", fontFamily: "Inter, sans-serif" }}>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "2rem" }}>
        <div>
          <h1 style={{ fontSize: "1.875rem", fontWeight: 700, margin: 0, color: "#fff" }}>
            📊 Enterprise AI Observability & Telemetry
          </h1>
          <p style={{ color: "#94a3b8", fontSize: "0.9rem", marginTop: "0.25rem" }}>
            OpenTelemetry Distributed Tracing, Prometheus Exporter, Statistical Anomaly Detection & SLA Alerting
          </p>
        </div>
        <div style={{ display: "flex", gap: "1rem", alignItems: "center" }}>
          <button
            onClick={handleFetchPrometheus}
            style={{ padding: "0.5rem 1rem", background: "#f59e0b", color: "#000", border: "none", borderRadius: "6px", fontWeight: 700, cursor: "pointer" }}
          >
            🔥 Prometheus /metrics Exporter
          </button>
          <NotificationBell />
        </div>
      </div>

      {/* Metrics Overview Banner */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "1rem", marginBottom: "2rem" }}>
        <div style={{ background: "#1e293b", padding: "1.25rem", borderRadius: "10px", border: "1px solid #334155" }}>
          <span style={{ color: "#94a3b8", fontSize: "0.8rem", textTransform: "uppercase" }}>SLA Compliance Score</span>
          <div style={{ fontSize: "2rem", fontWeight: 700, color: "#10b981", marginTop: "0.25rem" }}>
            {overview ? `${overview.sla_compliance_score_percent}%` : "..."}
          </div>
          <span style={{ fontSize: "0.75rem", color: "#64748b" }}>Target: {overview?.sla_target_uptime_percent}% Uptime</span>
        </div>

        <div style={{ background: "#1e293b", padding: "1.25rem", borderRadius: "10px", border: "1px solid #334155" }}>
          <span style={{ color: "#94a3b8", fontSize: "0.8rem", textTransform: "uppercase" }}>P95 Request Latency</span>
          <div style={{ fontSize: "2rem", fontWeight: 700, color: "#38bdf8", marginTop: "0.25rem" }}>
            {overview ? `${overview.p95_latency_ms} ms` : "..."}
          </div>
          <span style={{ fontSize: "0.75rem", color: "#64748b" }}>Target: &lt; {overview?.p95_latency_target_ms} ms</span>
        </div>

        <div style={{ background: "#1e293b", padding: "1.25rem", borderRadius: "10px", border: "1px solid #334155" }}>
          <span style={{ color: "#94a3b8", fontSize: "0.8rem", textTransform: "uppercase" }}>Total HTTP Requests</span>
          <div style={{ fontSize: "2rem", fontWeight: 700, color: "#a855f7", marginTop: "0.25rem" }}>
            {overview ? overview.total_http_requests.toLocaleString() : "..."}
          </div>
          <span style={{ fontSize: "0.75rem", color: "#64748b" }}>Errors: {overview?.total_http_errors}</span>
        </div>

        <div style={{ background: "#1e293b", padding: "1.25rem", borderRadius: "10px", border: "1px solid #334155" }}>
          <span style={{ color: "#94a3b8", fontSize: "0.8rem", textTransform: "uppercase" }}>Active Alerts</span>
          <div style={{ fontSize: "2rem", fontWeight: 700, color: overview?.active_alerts_count > 0 ? "#ef4444" : "#4ade80", marginTop: "0.25rem" }}>
            {overview ? overview.active_alerts_count : "..."}
          </div>
          <span style={{ fontSize: "0.75rem", color: "#64748b" }}>Anomalies & SLA Breaches</span>
        </div>
      </div>

      {/* Prometheus Modal / Drawer */}
      {showPrometheus && (
        <div style={{ background: "#0f172a", border: "1px solid #f59e0b", padding: "1.5rem", borderRadius: "10px", marginBottom: "2rem" }}>
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "1rem" }}>
            <h3 style={{ margin: 0, color: "#f59e0b" }}>🔥 Prometheus Metrics Format (/metrics)</h3>
            <button onClick={() => setShowPrometheus(false)} style={{ background: "transparent", color: "#94a3b8", border: "none", cursor: "pointer" }}>✕ Close</button>
          </div>
          <pre style={{ margin: 0, color: "#38bdf8", fontSize: "0.8rem", fontFamily: "monospace", maxHeight: "250px", overflowY: "auto" }}>
            {prometheusText}
          </pre>
        </div>
      )}

      {/* Distributed Tracing & Alerts Grid */}
      <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: "1.5rem", marginBottom: "2rem" }}>
        {/* OpenTelemetry Distributed Tracing Inspector */}
        <div style={{ background: "#1e293b", padding: "1.5rem", borderRadius: "10px", border: "1px solid #334155" }}>
          <h3 style={{ margin: "0 0 1rem 0", color: "#f1f5f9" }}>🌐 OpenTelemetry Distributed Request Traces</h3>
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left", fontSize: "0.85rem" }}>
              <thead>
                <tr style={{ borderBottom: "1px solid #334155", color: "#94a3b8" }}>
                  <th style={{ padding: "0.75rem" }}>Timestamp</th>
                  <th style={{ padding: "0.75rem" }}>Correlation ID</th>
                  <th style={{ padding: "0.75rem" }}>Endpoint</th>
                  <th style={{ padding: "0.75rem" }}>Latency</th>
                  <th style={{ padding: "0.75rem" }}>Status</th>
                </tr>
              </thead>
              <tbody>
                {traces.slice(0, 10).map((t, idx) => (
                  <tr key={idx} style={{ borderBottom: "1px solid #0f172a" }}>
                    <td style={{ padding: "0.75rem", color: "#64748b" }}>{new Date(t.timestamp).toLocaleTimeString()}</td>
                    <td style={{ padding: "0.75rem", color: "#38bdf8", fontFamily: "monospace" }}>{t.correlation_id}</td>
                    <td style={{ padding: "0.75rem", color: "#fff" }}>{t.endpoint}</td>
                    <td style={{ padding: "0.75rem", color: "#e2e8f0" }}>{t.duration_ms} ms</td>
                    <td style={{ padding: "0.75rem" }}>
                      <span style={{ padding: "0.1rem 0.4rem", borderRadius: "4px", fontWeight: 700, background: t.status_code < 400 ? "rgba(74,222,128,0.1)" : "rgba(239,68,68,0.1)", color: t.status_code < 400 ? "#4ade80" : "#ef4444" }}>
                        {t.status_code}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Alerting & Anomaly Dispatcher */}
        <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
          {/* Manual Alert Trigger */}
          <div style={{ background: "#1e293b", padding: "1.25rem", borderRadius: "10px", border: "1px solid #334155" }}>
            <h3 style={{ margin: "0 0 0.75rem 0", color: "#f1f5f9" }}>🚨 Dispatch Telemetry Alert</h3>
            <div style={{ display: "flex", gap: "0.5rem", marginBottom: "0.75rem" }}>
              <select
                value={alertType}
                onChange={(e) => setAlertType(e.target.value)}
                style={{ flex: 1, padding: "0.4rem", background: "#0f172a", border: "1px solid #334155", borderRadius: "4px", color: "#fff" }}
              >
                <option value="LATENCY_ANOMALY">LATENCY_ANOMALY</option>
                <option value="ERROR_SPIKE">ERROR_SPIKE</option>
                <option value="BUDGET_OVERRUN">BUDGET_OVERRUN</option>
                <option value="SLA_BREACH">SLA_BREACH</option>
              </select>
              <select
                value={severity}
                onChange={(e) => setSeverity(e.target.value)}
                style={{ flex: 1, padding: "0.4rem", background: "#0f172a", border: "1px solid #334155", borderRadius: "4px", color: "#fff" }}
              >
                <option value="INFO">INFO</option>
                <option value="WARNING">WARNING</option>
                <option value="CRITICAL">CRITICAL</option>
              </select>
            </div>
            <textarea
              rows={2}
              value={alertMessage}
              onChange={(e) => setAlertMessage(e.target.value)}
              style={{ width: "100%", padding: "0.5rem", background: "#0f172a", border: "1px solid #334155", borderRadius: "6px", color: "#fff", fontSize: "0.85rem", marginBottom: "0.75rem" }}
            />
            <button
              onClick={handleTriggerAlert}
              disabled={dispatching}
              style={{ width: "100%", padding: "0.6rem", background: "#ef4444", color: "#fff", border: "none", borderRadius: "6px", fontWeight: 700, cursor: "pointer" }}
            >
              {dispatching ? "Dispatching..." : "📡 Dispatch Alert Event"}
            </button>
          </div>

          {/* Active Alerts List */}
          <div style={{ background: "#1e293b", padding: "1.25rem", borderRadius: "10px", border: "1px solid #334155", flex: 1 }}>
            <h3 style={{ margin: "0 0 0.75rem 0", color: "#f1f5f9" }}>🔔 Recent Telemetry Alerts</h3>
            <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem", maxHeight: "280px", overflowY: "auto" }}>
              {alerts.map((a, idx) => (
                <div key={idx} style={{ padding: "0.6rem", background: "#0f172a", borderRadius: "6px", borderLeft: `4px solid ${a.severity === "CRITICAL" ? "#ef4444" : "#f59e0b"}` }}>
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.75rem" }}>
                    <span style={{ fontWeight: 700, color: "#fff" }}>[{a.severity}] {a.alert_type}</span>
                    <span style={{ color: "#64748b" }}>{new Date(a.created_at).toLocaleTimeString()}</span>
                  </div>
                  <div style={{ fontSize: "0.75rem", color: "#94a3b8", marginTop: "0.25rem" }}>{a.message}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ObservabilityWorkspace;
