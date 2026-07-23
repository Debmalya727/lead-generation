import React from "react";

interface AIThinkingIndicatorProps {
  isThinking: boolean;
  activeAgent: string;
  reasoningStep: string;
}

export const AIThinkingIndicator: React.FC<AIThinkingIndicatorProps> = ({
  isThinking,
  activeAgent,
  reasoningStep,
}) => {
  if (!isThinking) return null;

  return (
    <div
      style={{
        background: "rgba(139,92,246,0.15)",
        border: "1px solid rgba(139,92,246,0.4)",
        borderRadius: "10px",
        padding: "0.75rem 1.25rem",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        animation: "pulse 2s infinite ease-in-out",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
        <span style={{ fontSize: "1.2rem" }}>🧠</span>
        <div>
          <div style={{ fontSize: "0.85rem", fontWeight: 700, color: "#c084fc" }}>
            AI Agent Thinking ({activeAgent})
          </div>
          <div style={{ fontSize: "0.75rem", color: "#94a3b8" }}>{reasoningStep}</div>
        </div>
      </div>
      <span style={{ fontSize: "0.7rem", padding: "0.2rem 0.5rem", borderRadius: "100px", background: "rgba(192,132,252,0.2)", color: "#c084fc", fontWeight: 700 }}>
        REASONING...
      </span>
    </div>
  );
};
