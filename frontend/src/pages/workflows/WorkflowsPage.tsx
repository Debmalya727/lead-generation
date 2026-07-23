import React, { useEffect, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../contexts/AuthContext";
import {
  workflowsApi,
  WorkflowExecutionItem,
  WorkflowStepItem,
  WorkflowCheckpointItem,
  ToolItem,
} from "../../api/workflows";

const TEMPLATE_OPTIONS = [
  { id: "sales_discovery", name: "Sales Discovery Workflow", category: "sales_discovery" },
  { id: "lead_qualification", name: "Lead Qualification & ICP Audit", category: "lead_qualification" },
  { id: "sales_intelligence", name: "Comprehensive Sales Intelligence", category: "sales_intelligence" },
  { id: "company_research", name: "Deep Company Research Pipeline", category: "research" },
  { id: "outreach_campaign", name: "Cold Outreach Campaign Pipeline", category: "outreach" },
  { id: "executive_report_gen", name: "Executive Sales Report Generation", category: "executive_report" },
];

const statusColor = (s: string) => {
  switch (s) {
    case "completed": return "#10b981";
    case "running": return "#6366f1";
    case "failed": return "#ef4444";
    case "pending": return "#64748b";
    case "paused": return "#f59e0b";
    case "cancelled": return "#475569";
    default: return "#64748b";
  }
};

const statusBg = (s: string) => {
  switch (s) {
    case "completed": return "rgba(16,185,129,0.12)";
    case "running": return "rgba(99,102,241,0.18)";
    case "failed": return "rgba(239,68,68,0.12)";
    case "pending": return "rgba(100,116,139,0.1)";
    case "paused": return "rgba(245,158,11,0.15)";
    case "cancelled": return "rgba(71,85,105,0.2)";
    default: return "rgba(100,116,139,0.1)";
  }
};

type TabType = "executions" | "templates" | "tools" | "checkpoints";

export const WorkflowsPage: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  // Form state
  const [selectedTemplate, setSelectedTemplate] = useState("sales_discovery");
  const [companyName, setCompanyName] = useState("");
  const [leadId, setLeadId] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Data state
  const [executions, setExecutions] = useState<WorkflowExecutionItem[]>([]);
  const [selectedExecution, setSelectedExecution] = useState<WorkflowExecutionItem | null>(null);
  const [steps, setSteps] = useState<WorkflowStepItem[]>([]);
  const [checkpoints, setCheckpoints] = useState<WorkflowCheckpointItem[]>([]);
  const [tools, setTools] = useState<ToolItem[]>([]);
  const [activeTab, setActiveTab] = useState<TabType>("executions");
  const [testingTool, setTestingTool] = useState<ToolItem | null>(null);
  const [toolInputs, setToolInputs] = useState<string>("{\n  \"company_name\": \"Acme Corp\"\n}");
  const [toolResult, setToolResult] = useState<any>(null);

  useEffect(() => {
    fetchExecutions();
    workflowsApi.listTools().then(setTools).catch(() => {});
  }, []);

  const fetchExecutions = async () => {
    try {
      const data = await workflowsApi.listWorkflows({ limit: 20 });
      setExecutions(data.items);
    } catch {}
  };

  const fetchExecutionDetails = useCallback(async (id: string) => {
    try {
      const [exec, stData, chkData] = await Promise.all([
        workflowsApi.getWorkflowExecution(id),
        workflowsApi.getWorkflowSteps(id),
        workflowsApi.getWorkflowCheckpoints(id),
      ]);
      setSelectedExecution(exec);
      setSteps(stData);
      setCheckpoints(chkData);
    } catch {}
  }, []);

  const handleSelectExecution = (exec: WorkflowExecutionItem) => {
    setSelectedExecution(exec);
    fetchExecutionDetails(exec.execution_id);
  };

  const handleRunWorkflow = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!companyName.trim()) return;
    setSubmitting(true);
    setErrorMsg(null);
    try {
      const res = await workflowsApi.runWorkflow({
        workflow_id: selectedTemplate,
        company_name: companyName.trim(),
        lead_id: leadId.trim() || undefined,
      });
      setExecutions(prev => [res, ...prev]);
      setSelectedExecution(res);
      fetchExecutionDetails(res.execution_id);
      setCompanyName("");
    } catch (err: any) {
      setErrorMsg(err?.response?.data?.detail || "Failed to run workflow.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleExecuteTool = async () => {
    if (!testingTool) return;
    try {
      const parsed = JSON.parse(toolInputs);
      const res = await workflowsApi.executeTool(testingTool.tool_id, { inputs: parsed });
      setToolResult(res);
    } catch (e: any) {
      setToolResult({ error: e.message });
    }
  };

  const handleCancel = async () => {
    if (!selectedExecution) return;
    try {
      await workflowsApi.cancelWorkflow(selectedExecution.execution_id);
      fetchExecutionDetails(selectedExecution.execution_id);
    } catch {}
  };

  const handleResume = async () => {
    if (!selectedExecution) return;
    try {
      await workflowsApi.resumeWorkflow(selectedExecution.execution_id);
      fetchExecutionDetails(selectedExecution.execution_id);
    } catch {}
  };

  return (
    <div style={{ minHeight: "100vh", background: "#0a0f1e", color: "#e2e8f0", fontFamily: "'Inter', sans-serif", display: "flex", flexDirection: "column" }}>
      {/* Top Navigation Bar */}
      <nav style={{ background: "rgba(15,23,42,0.95)", borderBottom: "1px solid rgba(99,102,241,0.2)", padding: "0 2rem", height: "64px", display: "flex", alignItems: "center", justifyContent: "space-between", backdropFilter: "blur(12px)", position: "sticky", top: 0, zIndex: 100 }}>
        <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
          <div style={{ fontSize: "1.4rem", fontWeight: 800, background: "linear-gradient(135deg, #6366f1, #8b5cf6)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
            LeadForgeAI
          </div>
          <div style={{ color: "#64748b", fontSize: "0.85rem" }}>/ Workflow & Tool Engine</div>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
          <button onClick={() => navigate("/agents")} style={{ background: "none", border: "1px solid rgba(99,102,241,0.3)", color: "#94a3b8", padding: "0.4rem 1rem", borderRadius: "6px", cursor: "pointer", fontSize: "0.85rem" }}>🤖 Agents</button>
          <span style={{ color: "#64748b", fontSize: "0.85rem" }}>{user?.email}</span>
          <button onClick={logout} style={{ background: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.3)", color: "#f87171", padding: "0.4rem 1rem", borderRadius: "6px", cursor: "pointer", fontSize: "0.85rem" }}>Logout</button>
        </div>
      </nav>

      <div style={{ display: "grid", gridTemplateColumns: "320px 1fr", flex: 1, minHeight: 0 }}>
        {/* Left Sidebar Form */}
        <aside style={{ background: "rgba(15,23,42,0.8)", borderRight: "1px solid rgba(99,102,241,0.15)", display: "flex", flexDirection: "column", overflow: "hidden" }}>
          <div style={{ padding: "1.25rem", borderBottom: "1px solid rgba(99,102,241,0.15)" }}>
            <div style={{ fontSize: "0.8rem", fontWeight: 700, color: "#6366f1", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: "0.75rem" }}>Run Workflow</div>
            <form onSubmit={handleRunWorkflow} style={{ display: "flex", flexDirection: "column", gap: "0.6rem" }}>
              <select value={selectedTemplate} onChange={e => setSelectedTemplate(e.target.value)} style={{ padding: "0.55rem 0.75rem", borderRadius: "6px", border: "1px solid rgba(99,102,241,0.25)", background: "rgba(30,41,59,0.8)", color: "#e2e8f0", fontSize: "0.8rem", outline: "none" }}>
                {TEMPLATE_OPTIONS.map(tmpl => (
                  <option key={tmpl.id} value={tmpl.id}>{tmpl.name}</option>
                ))}
              </select>
              <input value={companyName} onChange={e => setCompanyName(e.target.value)} placeholder="Target company name *" style={{ padding: "0.55rem 0.75rem", borderRadius: "6px", border: "1px solid rgba(99,102,241,0.25)", background: "rgba(30,41,59,0.6)", color: "#e2e8f0", fontSize: "0.8rem", outline: "none" }} />
              <input value={leadId} onChange={e => setLeadId(e.target.value)} placeholder="Lead ID (optional)" style={{ padding: "0.55rem 0.75rem", borderRadius: "6px", border: "1px solid rgba(99,102,241,0.25)", background: "rgba(30,41,59,0.6)", color: "#e2e8f0", fontSize: "0.8rem", outline: "none" }} />
              {errorMsg && <div style={{ color: "#f87171", fontSize: "0.75rem", padding: "0.5rem", background: "rgba(239,68,68,0.1)", borderRadius: "6px" }}>{errorMsg}</div>}
              <button type="submit" disabled={submitting || !companyName.trim()} style={{ padding: "0.6rem", borderRadius: "8px", border: "none", background: submitting ? "rgba(99,102,241,0.4)" : "linear-gradient(135deg, #6366f1, #8b5cf6)", color: "#fff", fontWeight: 700, fontSize: "0.85rem", cursor: submitting ? "not-allowed" : "pointer" }}>
                {submitting ? "⏳ Launching…" : "⚡ Execute Workflow"}
              </button>
            </form>
          </div>

          <div style={{ flex: 1, overflowY: "auto", padding: "0.75rem" }}>
            <div style={{ fontSize: "0.75rem", color: "#64748b", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: "0.5rem" }}>Executions ({executions.length})</div>
            {executions.map(exec => (
              <div key={exec.execution_id} onClick={() => handleSelectExecution(exec)} style={{ padding: "0.75rem", borderRadius: "8px", marginBottom: "0.4rem", cursor: "pointer", border: `1px solid ${selectedExecution?.execution_id === exec.execution_id ? "rgba(99,102,241,0.5)" : "rgba(99,102,241,0.12)"}`, background: selectedExecution?.execution_id === exec.execution_id ? "rgba(99,102,241,0.1)" : "rgba(30,41,59,0.4)" }}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.25rem" }}>
                  <span style={{ fontSize: "0.75rem", color: "#94a3b8", fontFamily: "monospace" }}>{exec.execution_id.slice(0, 16)}</span>
                  <span style={{ fontSize: "0.68rem", padding: "0.15rem 0.5rem", borderRadius: "4px", background: statusBg(exec.status), color: statusColor(exec.status), fontWeight: 600 }}>{exec.status}</span>
                </div>
                <div style={{ fontSize: "0.8rem", color: "#e2e8f0", fontWeight: 600 }}>{exec.company_name || exec.workflow_id}</div>
                <div style={{ fontSize: "0.7rem", color: "#64748b" }}>Workflow: {exec.workflow_id}</div>
              </div>
            ))}
          </div>
        </aside>

        {/* Main Panel */}
        <main style={{ overflowY: "auto", display: "flex", flexDirection: "column" }}>
          {!selectedExecution ? (
            <div style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: "1.5rem", padding: "4rem" }}>
              <div style={{ fontSize: "3.5rem" }}>⚡</div>
              <div style={{ fontSize: "1.5rem", fontWeight: 800, color: "#e2e8f0" }}>Autonomous Workflow & Tool Engine</div>
              <div style={{ color: "#64748b", textAlign: "center", maxWidth: "520px", lineHeight: 1.7 }}>
                Select a workflow template from the sidebar to execute tool orchestration, policy checks, state checkpointing, and execution recovery.
              </div>
            </div>
          ) : (
            <div style={{ flex: 1, display: "flex", flexDirection: "column" }}>
              {/* Header */}
              <div style={{ padding: "1.25rem 1.5rem", borderBottom: "1px solid rgba(99,102,241,0.15)", background: "rgba(15,23,42,0.6)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <div>
                  <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginBottom: "0.3rem" }}>
                    <span style={{ fontSize: "0.75rem", fontFamily: "monospace", color: "#6366f1", background: "rgba(99,102,241,0.12)", padding: "0.2rem 0.5rem", borderRadius: "4px" }}>{selectedExecution.execution_id}</span>
                    <span style={{ fontSize: '0.78rem', padding: "0.2rem 0.65rem", borderRadius: "100px", background: statusBg(selectedExecution.status), color: statusColor(selectedExecution.status), fontWeight: 700 }}>{selectedExecution.status}</span>
                  </div>
                  <div style={{ fontSize: "1rem", fontWeight: 700, color: "#e2e8f0" }}>Company: {selectedExecution.company_name}</div>
                </div>
                <div style={{ display: "flex", gap: "0.5rem" }}>
                  {["running", "pending"].includes(selectedExecution.status) && (
                    <button onClick={handleCancel} style={{ padding: "0.4rem 0.8rem", borderRadius: "6px", border: "1px solid rgba(239,68,68,0.3)", background: "rgba(239,68,68,0.1)", color: "#f87171", fontSize: "0.78rem", cursor: "pointer" }}>Cancel</button>
                  )}
                  {["paused", "failed"].includes(selectedExecution.status) && (
                    <button onClick={handleResume} style={{ padding: "0.4rem 0.8rem", borderRadius: "6px", border: "1px solid rgba(99,102,241,0.3)", background: "rgba(99,102,241,0.1)", color: "#a5b4fc", fontSize: "0.78rem", cursor: "pointer" }}>Resume Checkpoint</button>
                  )}
                </div>
              </div>

              {/* Navigation Tabs */}
              <div style={{ display: "flex", borderBottom: "1px solid rgba(99,102,241,0.15)", background: "rgba(15,23,42,0.4)" }}>
                {[
                  { id: "executions", label: `⚡ Execution Steps (${steps.length})` },
                  { id: "checkpoints", label: `💾 Checkpoints (${checkpoints.length})` },
                  { id: "templates", label: "📐 Templates" },
                  { id: "tools", label: `📦 Tools (${tools.length})` },
                ].map(t => (
                  <button key={t.id} onClick={() => setActiveTab(t.id as TabType)} style={{ padding: "0.75rem 1.25rem", background: "none", border: "none", borderBottom: `2px solid ${activeTab === t.id ? "#6366f1" : "transparent"}`, color: activeTab === t.id ? "#a5b4fc" : "#64748b", fontWeight: activeTab === t.id ? 700 : 400, fontSize: "0.82rem", cursor: "pointer" }}>
                    {t.label}
                  </button>
                ))}
              </div>

              {/* Tab Contents */}
              <div style={{ flex: 1, overflowY: "auto", padding: "1.5rem" }}>
                {activeTab === "executions" && (
                  <div>
                    <div style={{ fontSize: "0.8rem", color: "#64748b", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: "1rem" }}>Workflow Step Pipeline</div>
                    <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
                      {steps.map((st, i) => (
                        <div key={st.step_execution_id} style={{ padding: "1rem", borderRadius: "10px", border: `1px solid ${statusColor(st.status)}30`, background: "rgba(15,23,42,0.7)" }}>
                          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.4rem" }}>
                            <div style={{ fontSize: "0.85rem", fontWeight: 700, color: "#e2e8f0" }}>{i + 1}. {st.name}</div>
                            <span style={{ fontSize: "0.7rem", padding: "0.2rem 0.5rem", borderRadius: "4px", background: statusBg(st.status), color: statusColor(st.status), fontWeight: 700 }}>{st.status}</span>
                          </div>
                          <div style={{ fontSize: "0.72rem", color: "#64748b", marginBottom: "0.5rem" }}>Target Tool: <code style={{ color: "#a5b4fc" }}>{st.target}</code> | Runtime: {st.execution_time_seconds.toFixed(2)}s</div>
                          {st.error_message && <div style={{ fontSize: "0.75rem", color: "#f87171", background: "rgba(239,68,68,0.1)", padding: "0.5rem", borderRadius: "6px", marginBottom: "0.5rem" }}>{st.error_message}</div>}
                          {Object.keys(st.outputs || {}).length > 0 && (
                            <pre style={{ margin: 0, fontSize: "0.7rem", color: "#cbd5e1", background: "rgba(10,15,30,0.6)", padding: "0.5rem", borderRadius: "6px", maxHeight: "120px", overflowY: "auto" }}>{JSON.stringify(st.outputs, null, 2)}</pre>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {activeTab === "checkpoints" && (
                  <div>
                    <div style={{ fontSize: "0.8rem", color: "#64748b", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: "1rem" }}>Execution Checkpoints & Crash Recovery Snapshots</div>
                    <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
                      {checkpoints.map(chk => (
                        <div key={chk.checkpoint_id} style={{ padding: "1rem", borderRadius: "10px", border: "1px solid rgba(99,102,241,0.2)", background: "rgba(15,23,42,0.7)" }}>
                          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.3rem" }}>
                            <span style={{ fontSize: "0.8rem", fontWeight: 700, color: "#34d399" }}>Checkpoint: {chk.checkpoint_id}</span>
                            <span style={{ fontSize: "0.7rem", color: "#64748b" }}>Step: {chk.step_id}</span>
                          </div>
                          <div style={{ fontSize: "0.72rem", color: "#94a3b8", marginBottom: "0.4rem" }}>Reason: {chk.reason} | Completed Steps: {chk.completed_step_ids.join(", ")}</div>
                          <pre style={{ margin: 0, fontSize: "0.68rem", color: "#94a3b8", background: "rgba(10,15,30,0.6)", padding: "0.5rem", borderRadius: "6px", maxHeight: "100px", overflowY: "auto" }}>{JSON.stringify(chk.state_snapshot, null, 2)}</pre>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {activeTab === "templates" && (
                  <div>
                    <div style={{ fontSize: "0.8rem", color: "#64748b", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: "1rem" }}>Prebuilt Workflow Templates</div>
                    <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: "1rem" }}>
                      {TEMPLATE_OPTIONS.map(tmpl => (
                        <div key={tmpl.id} style={{ padding: "1rem", borderRadius: "10px", border: "1px solid rgba(99,102,241,0.2)", background: "rgba(15,23,42,0.7)" }}>
                          <div style={{ fontSize: "0.9rem", fontWeight: 700, color: "#e2e8f0", marginBottom: "0.3rem" }}>{tmpl.name}</div>
                          <div style={{ fontSize: "0.72rem", color: "#6366f1", marginBottom: "0.5rem" }}>Category: {tmpl.category}</div>
                          <button onClick={() => { setSelectedTemplate(tmpl.id); window.scrollTo(0,0); }} style={{ padding: "0.35rem 0.75rem", borderRadius: "6px", border: "1px solid rgba(99,102,241,0.3)", background: "rgba(99,102,241,0.12)", color: "#a5b4fc", fontSize: "0.75rem", cursor: "pointer" }}>Use Template</button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {activeTab === "tools" && (
                  <div>
                    <div style={{ fontSize: "0.8rem", color: "#64748b", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: "1rem" }}>Tool Registry & Direct Test Console</div>
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.5rem" }}>
                      {/* Tool List */}
                      <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
                        {tools.map(t => (
                          <div key={t.tool_id} onClick={() => setTestingTool(t)} style={{ padding: "0.85rem", borderRadius: "8px", border: `1px solid ${testingTool?.tool_id === t.tool_id ? "#6366f1" : "rgba(99,102,241,0.18)"}`, background: testingTool?.tool_id === t.tool_id ? "rgba(99,102,241,0.15)" : "rgba(15,23,42,0.7)", cursor: "pointer" }}>
                            <div style={{ fontSize: "0.85rem", fontWeight: 700, color: "#e2e8f0" }}>{t.name}</div>
                            <div style={{ fontSize: "0.72rem", color: "#64748b" }}>ID: {t.tool_id} | Category: {t.category}</div>
                            <div style={{ fontSize: "0.75rem", color: "#94a3b8", marginTop: "0.3rem" }}>{t.description}</div>
                          </div>
                        ))}
                      </div>

                      {/* Console */}
                      <div style={{ padding: "1rem", borderRadius: "10px", border: "1px solid rgba(99,102,241,0.2)", background: "rgba(15,23,42,0.8)", display: "flex", flexDirection: "column", gap: "0.75rem" }}>
                        <div style={{ fontSize: "0.85rem", fontWeight: 700, color: "#a5b4fc" }}>
                          {testingTool ? `Test Console: ${testingTool.name}` : "Select a tool to test"}
                        </div>
                        {testingTool && (
                          <>
                            <textarea value={toolInputs} onChange={e => setToolInputs(e.target.value)} rows={6} style={{ fontFamily: "monospace", fontSize: "0.75rem", padding: "0.5rem", background: "rgba(10,15,30,0.8)", color: "#e2e8f0", border: "1px solid rgba(99,102,241,0.3)", borderRadius: "6px" }} />
                            <button onClick={handleExecuteTool} style={{ padding: "0.5rem", borderRadius: "6px", background: "linear-gradient(135deg, #6366f1, #8b5cf6)", color: "#fff", border: "none", fontWeight: 700, fontSize: "0.8rem", cursor: "pointer" }}>▶ Execute Tool</button>
                            {toolResult && (
                              <pre style={{ fontSize: "0.7rem", background: "rgba(10,15,30,0.9)", color: "#34d399", padding: "0.5rem", borderRadius: "6px", maxHeight: "160px", overflowY: "auto" }}>{JSON.stringify(toolResult, null, 2)}</pre>
                            )}
                          </>
                        )}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
};

export default WorkflowsPage;
