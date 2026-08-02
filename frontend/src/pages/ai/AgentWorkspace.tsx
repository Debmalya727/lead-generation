import React, { useEffect, useState } from "react";
import { aiApi } from "../../api/ai";
import { NotificationBell } from "../../components/NotificationBell";

export const AgentWorkspace: React.FC = () => {
  const [agents, setAgents] = useState<any[]>([]);
  const [marketplace, setMarketplace] = useState<any[]>([]);
  const [metrics, setMetrics] = useState<any>(null);
  const [activeTab, setActiveTab] = useState<"executor" | "marketplace" | "team">("executor");

  // Single Agent Execution State
  const [selectedAgentId, setSelectedAgentId] = useState<string>("sdr_agent");
  const [goal, setGoal] = useState<string>("Find qualified B2B leads in CRM and send introductory outreach emails.");
  const [running, setRunning] = useState<boolean>(false);
  const [planResult, setPlanResult] = useState<any>(null);

  // Multi-Agent Team Execution State
  const [teamName, setTeamName] = useState<string>("Growth SDR Team");
  const [selectedTeamAgents, setSelectedTeamAgents] = useState<string[]>(["sdr_agent", "lead_researcher", "outreach_writer"]);
  const [teamGoal, setTeamGoal] = useState<string>("Execute end-to-end Q3 Enterprise Lead Acquisition Campaign.");
  const [teamRunning, setTeamRunning] = useState<boolean>(false);
  const [teamResult, setTeamResult] = useState<any>(null);

  const fetchAgentPlatformData = async () => {
    try {
      const [agentsData, marketData, metricsData] = await Promise.all([
        aiApi.getAgents(),
        aiApi.getMarketplaceAgents(),
        aiApi.getAgentMetrics(),
      ]);
      setAgents(agentsData);
      setMarketplace(marketData);
      setMetrics(metricsData);
    } catch (err: any) {
      console.error("Failed to fetch agent platform data:", err);
    }
  };

  useEffect(() => {
    fetchAgentPlatformData();
    const interval = setInterval(fetchAgentPlatformData, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleInstallMarketplaceAgent = async (templateId: string) => {
    try {
      await aiApi.installMarketplaceAgent(templateId);
      alert(`Successfully installed Agent template '${templateId}'!`);
      await fetchAgentPlatformData();
    } catch (err: any) {
      alert(`Installation failed: ${err.message}`);
    }
  };

  const handleRunAgentGoal = async () => {
    if (!goal.trim()) return;
    setRunning(true);
    setPlanResult(null);

    try {
      const res = await aiApi.runAgent(selectedAgentId, goal);
      setPlanResult(res);
      await fetchAgentPlatformData();
    } catch (err: any) {
      alert(`Agent run failed: ${err.message}`);
    } finally {
      setRunning(false);
    }
  };

  const handleRunTeamGoal = async () => {
    if (!teamGoal.trim() || selectedTeamAgents.length === 0) return;
    setTeamRunning(true);
    setTeamResult(null);

    try {
      const res = await aiApi.runAgentTeam({
        team_name: teamName,
        participating_agent_ids: selectedTeamAgents,
        goal: teamGoal,
      });
      setTeamResult(res);
      await fetchAgentPlatformData();
    } catch (err: any) {
      alert(`Team execution failed: ${err.message}`);
    } finally {
      setTeamRunning(false);
    }
  };

  return (
    <div style={{ padding: "2rem", color: "#f8fafc", fontFamily: "Inter, sans-serif" }}>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "2rem" }}>
        <div>
          <h1 style={{ fontSize: "1.875rem", fontWeight: 700, margin: 0, color: "#fff" }}>
            🤖 Enterprise AI Agent Platform
          </h1>
          <p style={{ color: "#94a3b8", fontSize: "0.9rem", marginTop: "0.25rem" }}>
            Autonomous Goal Planning, Task Decomposition, Self-Reflection, Multi-Agent Collaboration & Marketplace
          </p>
        </div>
        <NotificationBell />
      </div>

      {/* Metrics Banner */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "1rem", marginBottom: "2rem" }}>
        <div style={{ background: "#1e293b", padding: "1.25rem", borderRadius: "10px", border: "1px solid #334155" }}>
          <span style={{ color: "#94a3b8", fontSize: "0.8rem", textTransform: "uppercase" }}>Registered Agents</span>
          <div style={{ fontSize: "2rem", fontWeight: 700, color: "#38bdf8", marginTop: "0.25rem" }}>
            {metrics ? metrics.registered_agents_count : "..."}
          </div>
          <span style={{ fontSize: "0.75rem", color: "#64748b" }}>Active Agent Registry</span>
        </div>

        <div style={{ background: "#1e293b", padding: "1.25rem", borderRadius: "10px", border: "1px solid #334155" }}>
          <span style={{ color: "#94a3b8", fontSize: "0.8rem", textTransform: "uppercase" }}>Marketplace Catalog</span>
          <div style={{ fontSize: "2rem", fontWeight: 700, color: "#a855f7", marginTop: "0.25rem" }}>
            {metrics ? metrics.marketplace_templates_count : "..."}
          </div>
          <span style={{ fontSize: "0.75rem", color: "#64748b" }}>Pre-configured Templates</span>
        </div>

        <div style={{ background: "#1e293b", padding: "1.25rem", borderRadius: "10px", border: "1px solid #334155" }}>
          <span style={{ color: "#94a3b8", fontSize: "0.8rem", textTransform: "uppercase" }}>Total Agent Runs</span>
          <div style={{ fontSize: "2rem", fontWeight: 700, color: "#4ade80", marginTop: "0.25rem" }}>
            {metrics ? metrics.total_agent_runs.toLocaleString() : "..."}
          </div>
          <span style={{ fontSize: "0.75rem", color: "#64748b" }}>Autonomous Task Plans</span>
        </div>

        <div style={{ background: "#1e293b", padding: "1.25rem", borderRadius: "10px", border: "1px solid #334155" }}>
          <span style={{ color: "#94a3b8", fontSize: "0.8rem", textTransform: "uppercase" }}>Overall Success Rate</span>
          <div style={{ fontSize: "2rem", fontWeight: 700, color: "#10b981", marginTop: "0.25rem" }}>
            {metrics ? `${metrics.overall_success_rate_percent}%` : "..."}
          </div>
          <span style={{ fontSize: "0.75rem", color: "#64748b" }}>Verified via Self-Reflection</span>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div style={{ display: "flex", gap: "1rem", marginBottom: "1.5rem", borderBottom: "1px solid #334155", paddingBottom: "0.5rem" }}>
        <button
          onClick={() => setActiveTab("executor")}
          style={{
            padding: "0.5rem 1.25rem",
            background: activeTab === "executor" ? "#4f46e5" : "transparent",
            color: activeTab === "executor" ? "#fff" : "#94a3b8",
            border: "none",
            borderRadius: "6px",
            fontWeight: 600,
            cursor: "pointer",
          }}
        >
          ⚡ Autonomous Agent Runner
        </button>
        <button
          onClick={() => setActiveTab("team")}
          style={{
            padding: "0.5rem 1.25rem",
            background: activeTab === "team" ? "#a855f7" : "transparent",
            color: activeTab === "team" ? "#fff" : "#94a3b8",
            border: "none",
            borderRadius: "6px",
            fontWeight: 600,
            cursor: "pointer",
          }}
        >
          🤝 Multi-Agent Team Collaborator
        </button>
        <button
          onClick={() => setActiveTab("marketplace")}
          style={{
            padding: "0.5rem 1.25rem",
            background: activeTab === "marketplace" ? "#10b981" : "transparent",
            color: activeTab === "marketplace" ? "#fff" : "#94a3b8",
            border: "none",
            borderRadius: "6px",
            fontWeight: 600,
            cursor: "pointer",
          }}
        >
          🛍️ Agent Marketplace ({marketplace.length})
        </button>
      </div>

      {/* Tab 1: Single Autonomous Agent Executor */}
      {activeTab === "executor" && (
        <div style={{ display: "grid", gridTemplateColumns: "320px 1fr", gap: "1.5rem" }}>
          {/* Agent Selection Sidebar */}
          <div style={{ background: "#1e293b", padding: "1.25rem", borderRadius: "10px", border: "1px solid #334155" }}>
            <h3 style={{ margin: "0 0 1rem 0", color: "#f1f5f9" }}>🤖 Select AI Agent Persona</h3>
            <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
              {agents.map((a) => (
                <div
                  key={a.agent_id}
                  onClick={() => setSelectedAgentId(a.agent_id)}
                  style={{
                    padding: "0.85rem",
                    borderRadius: "8px",
                    background: selectedAgentId === a.agent_id ? "#334155" : "#0f172a",
                    border: selectedAgentId === a.agent_id ? "1px solid #38bdf8" : "1px solid transparent",
                    cursor: "pointer",
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <span style={{ fontWeight: 600, color: "#fff", fontSize: "0.9rem" }}>{a.name}</span>
                    <span style={{ fontSize: "0.7rem", color: "#10b981", background: "rgba(16,185,129,0.1)", padding: "0.1rem 0.4rem", borderRadius: "4px" }}>
                      {a.status}
                    </span>
                  </div>
                  <div style={{ fontSize: "0.75rem", color: "#94a3b8", marginTop: "0.25rem" }}>{a.role}</div>
                  <div style={{ fontSize: "0.7rem", color: "#64748b", marginTop: "0.4rem" }}>
                    Tools: {a.assigned_tools?.join(", ") || "None"}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Goal Execution Playground */}
          <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
            <div style={{ background: "#1e293b", padding: "1.5rem", borderRadius: "10px", border: "1px solid #334155" }}>
              <h3 style={{ margin: "0 0 0.5rem 0", color: "#f1f5f9" }}>🎯 Autonomous Goal Prompt</h3>
              <p style={{ color: "#94a3b8", fontSize: "0.8rem", margin: "0 0 1rem 0" }}>
                The agent will autonomously decompose the goal into sub-task steps, execute sandboxed tool calls, and run self-reflection.
              </p>
              <textarea
                rows={3}
                value={goal}
                onChange={(e) => setGoal(e.target.value)}
                style={{ width: "100%", padding: "0.75rem", background: "#0f172a", border: "1px solid #334155", borderRadius: "6px", color: "#fff", fontSize: "0.9rem", marginBottom: "1rem" }}
              />
              <button
                onClick={handleRunAgentGoal}
                disabled={running}
                style={{ width: "100%", padding: "0.75rem", background: "#4f46e5", color: "#fff", border: "none", borderRadius: "6px", fontWeight: 700, cursor: "pointer" }}
              >
                {running ? "Agent Orchestrating (Planning ➔ Executing ➔ Reflecting)..." : "🚀 Execute Autonomous Agent Goal"}
              </button>
            </div>

            {/* Execution Trace Result */}
            {planResult && (
              <div style={{ background: "#1e293b", padding: "1.5rem", borderRadius: "10px", border: "1px solid #334155" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
                  <h3 style={{ margin: 0, color: "#f1f5f9" }}>📋 Execution Plan Trace — {planResult.plan_id}</h3>
                  <span style={{ padding: "0.25rem 0.75rem", borderRadius: "4px", fontWeight: 700, background: planResult.status === "COMPLETED" ? "rgba(74,222,128,0.1)" : "rgba(239,68,68,0.1)", color: planResult.status === "COMPLETED" ? "#4ade80" : "#ef4444" }}>
                    Status: {planResult.status} (Quality Score: {planResult.self_evaluation_score})
                  </span>
                </div>

                <h4 style={{ color: "#38bdf8", marginBottom: "0.5rem" }}>1. Decomposed Sub-Task Steps</h4>
                <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem", marginBottom: "1.5rem" }}>
                  {planResult.sub_tasks?.map((st: any, idx: number) => (
                    <div key={idx} style={{ padding: "0.75rem", background: "#0f172a", borderRadius: "6px", border: "1px solid #334155" }}>
                      <div style={{ display: "flex", justifyContent: "space-between" }}>
                        <span style={{ fontWeight: 600, color: "#fff" }}>Step {st.step}: {st.task}</span>
                        <span style={{ color: "#38bdf8", fontSize: "0.8rem" }}>Tool: {st.tool}</span>
                      </div>
                      <div style={{ fontSize: "0.75rem", color: "#94a3b8", marginTop: "0.25rem" }}>
                        Status: <strong style={{ color: st.status === "SUCCESS" ? "#4ade80" : "#fbbf24" }}>{st.status}</strong>
                      </div>
                    </div>
                  ))}
                </div>

                <h4 style={{ color: "#a855f7", marginBottom: "0.5rem" }}>2. Self-Reflection & Evaluation Logs</h4>
                <div style={{ padding: "1rem", background: "#0f172a", borderRadius: "6px", border: "1px solid #334155" }}>
                  {planResult.reflections?.map((ref: any, idx: number) => (
                    <div key={idx} style={{ fontSize: "0.8rem", color: "#e2e8f0", marginBottom: "0.4rem" }}>
                      • <strong>[{ref.step}]</strong> {ref.reflection_note}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tab 2: Multi-Agent Team Collaborator */}
      {activeTab === "team" && (
        <div style={{ background: "#1e293b", padding: "1.5rem", borderRadius: "10px", border: "1px solid #334155" }}>
          <h3 style={{ margin: "0 0 1rem 0", color: "#f1f5f9" }}>🤝 Multi-Agent Team Collaboration Engine</h3>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem", marginBottom: "1rem" }}>
            <div>
              <label style={{ display: "block", color: "#94a3b8", fontSize: "0.8rem", marginBottom: "0.25rem" }}>Team Name</label>
              <input
                type="text"
                value={teamName}
                onChange={(e) => setTeamName(e.target.value)}
                style={{ width: "100%", padding: "0.5rem", background: "#0f172a", border: "1px solid #334155", borderRadius: "6px", color: "#fff", marginBottom: "1rem" }}
              />
              <label style={{ display: "block", color: "#94a3b8", fontSize: "0.8rem", marginBottom: "0.25rem" }}>Participating Agents</label>
              <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
                {agents.map((a) => (
                  <button
                    key={a.agent_id}
                    onClick={() => {
                      if (selectedTeamAgents.includes(a.agent_id)) {
                        setSelectedTeamAgents(selectedTeamAgents.filter((id) => id !== a.agent_id));
                      } else {
                        setSelectedTeamAgents([...selectedTeamAgents, a.agent_id]);
                      }
                    }}
                    style={{
                      padding: "0.4rem 0.75rem",
                      background: selectedTeamAgents.includes(a.agent_id) ? "#a855f7" : "#0f172a",
                      color: "#fff",
                      border: "1px solid #334155",
                      borderRadius: "6px",
                      fontSize: "0.8rem",
                      cursor: "pointer",
                    }}
                  >
                    {selectedTeamAgents.includes(a.agent_id) ? "✓ " : "+ "}{a.name}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <label style={{ display: "block", color: "#94a3b8", fontSize: "0.8rem", marginBottom: "0.25rem" }}>Collective Team Goal</label>
              <textarea
                rows={4}
                value={teamGoal}
                onChange={(e) => setTeamGoal(e.target.value)}
                style={{ width: "100%", padding: "0.5rem", background: "#0f172a", border: "1px solid #334155", borderRadius: "6px", color: "#fff", fontSize: "0.85rem", marginBottom: "1rem" }}
              />
              <button
                onClick={handleRunTeamGoal}
                disabled={teamRunning}
                style={{ width: "100%", padding: "0.75rem", background: "#a855f7", color: "#fff", border: "none", borderRadius: "6px", fontWeight: 700, cursor: "pointer" }}
              >
                {teamRunning ? "Collaborating & Synthesizing Consensus..." : "👥 Launch Multi-Agent Team Campaign"}
              </button>
            </div>
          </div>

          {teamResult && (
            <div style={{ marginTop: "1.5rem", padding: "1rem", background: "#0f172a", borderRadius: "8px", border: "1px solid #334155" }}>
              <h4 style={{ color: "#a855f7", margin: "0 0 0.5rem 0" }}>Team Consensus: {teamResult.consensus_result?.status}</h4>
              <p style={{ color: "#e2e8f0", fontSize: "0.85rem" }}>{teamResult.consensus_result?.summary}</p>
              <pre style={{ color: "#94a3b8", fontSize: "0.8rem" }}>{JSON.stringify(teamResult.delegations, null, 2)}</pre>
            </div>
          )}
        </div>
      )}

      {/* Tab 3: Agent Marketplace */}
      {activeTab === "marketplace" && (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))", gap: "1.5rem" }}>
          {marketplace.map((tmpl) => (
            <div key={tmpl.agent_id} style={{ background: "#1e293b", padding: "1.5rem", borderRadius: "10px", border: "1px solid #334155", display: "flex", flexDirection: "column", justifyContent: "space-between" }}>
              <div>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <h3 style={{ margin: 0, color: "#fff", fontSize: "1.1rem" }}>{tmpl.name}</h3>
                  <span style={{ fontSize: "0.7rem", color: "#10b981", background: "rgba(16,185,129,0.1)", padding: "0.1rem 0.4rem", borderRadius: "4px" }}>Verified</span>
                </div>
                <div style={{ fontSize: "0.8rem", color: "#38bdf8", marginTop: "0.25rem" }}>{tmpl.role}</div>
                <p style={{ fontSize: "0.85rem", color: "#94a3b8", marginTop: "0.75rem" }}>{tmpl.description}</p>
                <div style={{ fontSize: "0.75rem", color: "#64748b" }}>
                  Assigned Tools: {tmpl.assigned_tools?.join(", ")}
                </div>
              </div>
              <button
                onClick={() => handleInstallMarketplaceAgent(tmpl.agent_id)}
                style={{ marginTop: "1.25rem", padding: "0.6rem", background: "#10b981", color: "#fff", border: "none", borderRadius: "6px", fontWeight: 700, cursor: "pointer" }}
              >
                📥 1-Click Install Agent
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default AgentWorkspace;
