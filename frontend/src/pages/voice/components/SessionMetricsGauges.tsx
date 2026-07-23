import React from "react";

interface SessionMetricsGaugesProps {
  latencyMs: number;
  jitterMs: number;
  packetLoss: number;
  audioLevelDb: number;
  e2eSpeechToSpeechMs: number;
}

export const SessionMetricsGauges: React.FC<SessionMetricsGaugesProps> = ({
  latencyMs,
  jitterMs,
  packetLoss,
  audioLevelDb,
  e2eSpeechToSpeechMs,
}) => {
  return (
    <div style={{ display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: "1rem" }}>
      <div style={{ padding: "1rem", background: "rgba(15,23,42,0.85)", border: "1px solid rgba(99,102,241,0.2)", borderRadius: "12px", textAlign: "center" }}>
        <div style={{ fontSize: "1.6rem", fontWeight: 800, color: "#34d399" }}>
          {latencyMs.toFixed(1)} <span style={{ fontSize: "0.8rem", color: "#64748b" }}>ms</span>
        </div>
        <div style={{ fontSize: "0.75rem", color: "#64748b", marginTop: "0.2rem" }}>WebSocket RTT</div>
      </div>

      <div style={{ padding: "1rem", background: "rgba(15,23,42,0.85)", border: "1px solid rgba(99,102,241,0.2)", borderRadius: "12px", textAlign: "center" }}>
        <div style={{ fontSize: "1.6rem", fontWeight: 800, color: "#a5b4fc" }}>
          {jitterMs.toFixed(1)} <span style={{ fontSize: "0.8rem", color: "#64748b" }}>ms</span>
        </div>
        <div style={{ fontSize: "0.75rem", color: "#64748b", marginTop: "0.2rem" }}>Jitter Buffer</div>
      </div>

      <div style={{ padding: "1rem", background: "rgba(15,23,42,0.85)", border: "1px solid rgba(99,102,241,0.2)", borderRadius: "12px", textAlign: "center" }}>
        <div style={{ fontSize: "1.6rem", fontWeight: 800, color: "#60a5fa" }}>
          {packetLoss.toFixed(2)} <span style={{ fontSize: "0.8rem", color: "#64748b" }}>%</span>
        </div>
        <div style={{ fontSize: "0.75rem", color: "#64748b", marginTop: "0.2rem" }}>Packet Loss</div>
      </div>

      <div style={{ padding: "1rem", background: "rgba(15,23,42,0.85)", border: "1px solid rgba(99,102,241,0.2)", borderRadius: "12px", textAlign: "center" }}>
        <div style={{ fontSize: "1.6rem", fontWeight: 800, color: "#f59e0b" }}>
          {audioLevelDb.toFixed(1)} <span style={{ fontSize: "0.8rem", color: "#64748b" }}>dB</span>
        </div>
        <div style={{ fontSize: "0.75rem", color: "#64748b", marginTop: "0.2rem" }}>Audio Level (dBFS)</div>
      </div>

      <div style={{ padding: "1rem", background: "rgba(15,23,42,0.85)", border: "1px solid rgba(16,185,129,0.3)", borderRadius: "12px", textAlign: "center" }}>
        <div style={{ fontSize: "1.6rem", fontWeight: 800, color: "#10b981" }}>
          {e2eSpeechToSpeechMs.toFixed(1)} <span style={{ fontSize: "0.8rem", color: "#64748b" }}>ms</span>
        </div>
        <div style={{ fontSize: "0.75rem", color: "#64748b", marginTop: "0.2rem" }}>Speech-to-Speech E2E</div>
      </div>
    </div>
  );
};
