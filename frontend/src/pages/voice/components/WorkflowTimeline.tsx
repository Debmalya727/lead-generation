import React from "react";

interface WorkflowStep {
  name: string;
  status: "completed" | "active" | "pending";
  latency_ms?: number;
}

interface WorkflowTimelineProps {
  steps: WorkflowStep[];
}

export const WorkflowTimeline: React.FC<WorkflowTimelineProps> = ({ steps }) => {
  return (
    <div style={{ background: "rgba(15,23,42,0.85)", border: "1px solid rgba(99,102,241,0.2)", borderRadius: "14px", padding: "1.25rem" }}>
      <h3 style={{ margin: "0 0 1rem 0", fontSize: "1.05rem", fontWeight: 700, color: "#a5b4fc" }}>🗺️ Voice Workflow Pipeline Execution Timeline</h3>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", position: "relative" }}>
        {steps.map((step, idx) => (
          <React.Fragment key={idx}>
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "0.4rem", zIndex: 2 }}>
              <div
                style={{
                  width: "28px",
                  height: "28px",
                  borderRadius: "50%",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  background:
                    step.status === "completed"
                      ? "#34d399"
                      : step.status === "active"
                      ? "#6366f1"
                      : "rgba(100,116,139,0.3)",
                  color: "#0a0f1e",
                  fontWeight: 800,
                  fontSize: "0.75rem",
                  boxShadow: step.status === "active" ? "0 0 12px #6366f1" : "none",
                }}
              >
                {step.status === "completed" ? "✓" : idx + 1}
              </div>
              <span style={{ fontSize: "0.75rem", fontWeight: 600, color: step.status === "pending" ? "#64748b" : "#fff" }}>
                {step.name}
              </span>
              {step.latency_ms !== undefined && (
                <span style={{ fontSize: "0.68rem", color: "#34d399" }}>{step.latency_ms}ms</span>
              )}
            </div>
            {idx < steps.length - 1 && (
              <div
                style={{
                  flex: 1,
                  height: "2px",
                  background:
                    steps[idx + 1].status !== "pending"
                      ? "#34d399"
                      : "rgba(100,116,139,0.2)",
                  margin: "0 0.5rem",
                  marginTop: "-1rem",
                }}
              />
            )}
          </React.Fragment>
        ))}
      </div>
    </div>
  );
};
