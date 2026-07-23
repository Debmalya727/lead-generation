import React, { useState } from "react";

export interface VoiceEvent {
  event_id: string;
  session_id: string;
  event_type: string;
  timestamp: string;
  payload?: any;
}

interface DebugConsolePanelProps {
  logs: VoiceEvent[];
}

export const DebugConsolePanel: React.FC<DebugConsolePanelProps> = ({ logs }) => {
  const [filter, setFilter] = useState("ALL");

  const filteredLogs = logs.filter(
    l => filter === "ALL" || l.event_type.toLowerCase().includes(filter.toLowerCase())
  );

  return (
    <div style={{ background: "rgba(15,23,42,0.85)", border: "1px solid rgba(99,102,241,0.2)", borderRadius: "14px", padding: "1.25rem", display: "flex", flexDirection: "column", gap: "0.75rem", flex: 1, minHeight: "320px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <h3 style={{ margin: 0, fontSize: "1.05rem", fontWeight: 700, color: "#a5b4fc" }}>📜 Live Voice Event Stream Log</h3>
          <span style={{ color: "#64748b", fontSize: "0.78rem" }}>Real-time event bus emission telemetry</span>
        </div>
        <select value={filter} onChange={e => setFilter(e.target.value)} style={{ padding: "0.3rem 0.6rem", borderRadius: "6px", background: "#0a0f1e", border: "1px solid rgba(99,102,241,0.3)", color: "#fff", fontSize: "0.78rem" }}>
          <option value="ALL">All Events</option>
          <option value="VoiceConnected">VoiceConnected</option>
          <option value="SpeechStarted">SpeechStarted</option>
          <option value="SpeechStopped">SpeechStopped</option>
          <option value="Interruption">Interruption</option>
          <option value="AudioChunkReceived">AudioChunkReceived</option>
        </select>
      </div>

      <div style={{ flex: 1, background: "rgba(10,15,30,0.9)", border: "1px solid rgba(99,102,241,0.15)", borderRadius: "10px", padding: "0.85rem", overflowY: "auto", fontFamily: "monospace", fontSize: "0.78rem", display: "flex", flexDirection: "column", gap: "0.35rem", maxHeight: "360px" }}>
        {filteredLogs.length === 0 ? (
          <div style={{ color: "#64748b" }}>No voice events logged yet.</div>
        ) : (
          filteredLogs.map(evt => (
            <div key={evt.event_id} style={{ display: "flex", gap: "0.75rem", borderBottom: "1px solid rgba(255,255,255,0.04)", paddingBottom: "0.25rem" }}>
              <span style={{ color: "#64748b" }}>{new Date(evt.timestamp).toLocaleTimeString()}</span>
              <span style={{ color: evt.event_type === "Interruption" ? "#f87171" : "#34d399", fontWeight: 600 }}>{evt.event_type}</span>
              <span style={{ color: "#a5b4fc" }}>{evt.session_id}</span>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
