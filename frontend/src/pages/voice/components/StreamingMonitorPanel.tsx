import React from "react";

interface StreamingMonitorPanelProps {
  bandwidthKbps: number;
  frameQueueDepth: number;
  droppedFrames: number;
  bufferHealthPct: number;
}

export const StreamingMonitorPanel: React.FC<StreamingMonitorPanelProps> = ({
  bandwidthKbps,
  frameQueueDepth,
  droppedFrames,
  bufferHealthPct,
}) => {
  return (
    <div style={{ background: "rgba(15,23,42,0.85)", border: "1px solid rgba(99,102,241,0.2)", borderRadius: "14px", padding: "1.25rem", display: "flex", flexDirection: "column", gap: "1rem" }}>
      <h3 style={{ margin: 0, fontSize: "1.05rem", fontWeight: 700, color: "#a5b4fc" }}>📡 Network Streaming Monitor</h3>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "1rem", textAlign: "center" }}>
        <div>
          <div style={{ fontSize: "1.4rem", fontWeight: 800, color: "#60a5fa" }}>{bandwidthKbps} <span style={{ fontSize: "0.8rem", color: "#64748b" }}>Kbps</span></div>
          <span style={{ fontSize: "0.75rem", color: "#64748b" }}>Current Bandwidth</span>
        </div>

        <div>
          <div style={{ fontSize: "1.4rem", fontWeight: 800, color: "#a5b4fc" }}>{frameQueueDepth} <span style={{ fontSize: "0.8rem", color: "#64748b" }}>frames</span></div>
          <span style={{ fontSize: "0.75rem", color: "#64748b" }}>Queue Depth</span>
        </div>

        <div>
          <div style={{ fontSize: "1.4rem", fontWeight: 800, color: droppedFrames === 0 ? "#34d399" : "#f87171" }}>{droppedFrames}</div>
          <span style={{ fontSize: "0.75rem", color: "#64748b" }}>Dropped Frames</span>
        </div>

        <div>
          <div style={{ fontSize: "1.4rem", fontWeight: 800, color: "#34d399" }}>{bufferHealthPct}%</div>
          <span style={{ fontSize: "0.75rem", color: "#64748b" }}>Buffer Health</span>
        </div>
      </div>
    </div>
  );
};
