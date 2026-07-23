import React from "react";

export interface TranscriptTurn {
  id: string;
  speaker: "user" | "assistant";
  text: string;
  confidence?: number;
  language?: string;
  latency_ms?: number;
  timestamp: string;
  isPartial?: boolean;
}

interface LiveTranscriptFeedProps {
  turns: TranscriptTurn[];
  onClear: () => void;
}

export const LiveTranscriptFeed: React.FC<LiveTranscriptFeedProps> = ({ turns, onClear }) => {
  return (
    <div style={{ background: "rgba(15,23,42,0.85)", border: "1px solid rgba(99,102,241,0.2)", borderRadius: "14px", padding: "1.25rem", display: "flex", flexDirection: "column", gap: "0.75rem", flex: 1, minHeight: "320px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <h3 style={{ margin: 0, fontSize: "1.05rem", fontWeight: 700, color: "#a5b4fc" }}>💬 Live Transcript & Conversation Feed</h3>
          <span style={{ color: "#64748b", fontSize: "0.78rem" }}>Real-time partial ASR transcripts & streaming LLM assistant responses</span>
        </div>
        <button onClick={onClear} style={{ background: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.3)", color: "#f87171", padding: "0.25rem 0.65rem", borderRadius: "6px", fontSize: "0.75rem", cursor: "pointer" }}>
          Clear Feed
        </button>
      </div>

      <div style={{ flex: 1, background: "rgba(10,15,30,0.9)", border: "1px solid rgba(99,102,241,0.15)", borderRadius: "10px", padding: "1rem", overflowY: "auto", display: "flex", flexDirection: "column", gap: "0.85rem", maxHeight: "360px" }}>
        {turns.length === 0 ? (
          <div style={{ color: "#64748b", fontSize: "0.85rem", textAlign: "center", marginTop: "2rem" }}>
            No speech transcript logged yet. Click "Start Voice Session" or "Talk to Assistant".
          </div>
        ) : (
          turns.map(t => (
            <div key={t.id} style={{ display: "flex", flexDirection: "column", gap: "0.3rem", alignSelf: t.speaker === "user" ? "flex-end" : "flex-start", maxWidth: "85%" }}>
              <div style={{ display: "flex", gap: "0.5rem", alignItems: "center", justifyContent: t.speaker === "user" ? "flex-end" : "flex-start" }}>
                <span style={{ fontSize: "0.75rem", fontWeight: 700, color: t.speaker === "user" ? "#60a5fa" : "#34d399" }}>
                  {t.speaker === "user" ? "👤 User Speech" : "🤖 LeadForgeAI Assistant"}
                </span>
                {t.confidence && (
                  <span style={{ fontSize: "0.68rem", background: "rgba(52,211,153,0.15)", color: "#34d399", padding: "0.1rem 0.4rem", borderRadius: "100px", fontWeight: 600 }}>
                    {(t.confidence * 100).toFixed(0)}% Conf
                  </span>
                )}
                {t.language && (
                  <span style={{ fontSize: "0.68rem", background: "rgba(96,165,250,0.15)", color: "#60a5fa", padding: "0.1rem 0.4rem", borderRadius: "100px", fontWeight: 600 }}>
                    {t.language}
                  </span>
                )}
                <span style={{ fontSize: "0.7rem", color: "#64748b" }}>{t.timestamp}</span>
              </div>
              <div
                style={{
                  padding: "0.75rem 1rem",
                  borderRadius: "10px",
                  background: t.speaker === "user" ? "rgba(99,102,241,0.2)" : "rgba(15,23,42,0.9)",
                  border: t.speaker === "user" ? "1px solid rgba(99,102,241,0.3)" : "1px solid rgba(52,211,153,0.3)",
                  color: "#fff",
                  fontSize: "0.9rem",
                  lineHeight: "1.4",
                  fontStyle: t.isPartial ? "italic" : "normal",
                }}
              >
                "{t.text}"
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
