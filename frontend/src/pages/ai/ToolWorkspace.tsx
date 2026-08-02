import React, { useEffect, useState } from "react";
import { aiApi } from "../../api/ai";
import { NotificationBell } from "../../components/NotificationBell";

export const ToolWorkspace: React.FC = () => {
  const [tools, setTools] = useState<any[]>([]);
  const [selectedTool, setSelectedTool] = useState<any>(null);
  const [metrics, setMetrics] = useState<any>(null);
  const [logs, setLogs] = useState<any[]>([]);
  const [schemaMode, setSchemaMode] = useState<"native" | "openai" | "gemini">("native");
  const [activeSchema, setActiveSchema] = useState<any>(null);

  // Filter State
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [selectedCategory, setSelectedCategory] = useState<string>("");

  // Sandbox Test Runner State
  const [testArgs, setTestArgs] = useState<string>("{}");
  const [userScopes, setUserScopes] = useState<string>("*");
  const [executing, setExecuting] = useState<boolean>(false);
  const [testResult, setTestResult] = useState<any>(null);

  const fetchToolsAndMetrics = async () => {
    try {
      const [toolsData, metricsData, logsData] = await Promise.all([
        aiApi.getTools(selectedCategory || undefined),
        aiApi.getToolMetrics(),
        aiApi.getToolLogs(50),
      ]);
      setTools(toolsData);
      setMetrics(metricsData);
      setLogs(logsData);
      if (toolsData.length > 0 && !selectedTool) {
        selectTool(toolsData[0]);
      }
    } catch (err: any) {
      console.error("Failed to fetch tool platform data:", err);
    }
  };

  useEffect(() => {
    fetchToolsAndMetrics();
    const interval = setInterval(fetchToolsAndMetrics, 5000);
    return () => clearInterval(interval);
  }, [selectedCategory]);

  const selectTool = (tool: any) => {
    setSelectedTool(tool);
    setTestResult(null);
    setSchemaMode("native");
    setActiveSchema(tool.parameters_schema);

    // Pre-populate sample JSON args
    const sampleArgs: Record<string, any> = {};
    const props = tool.parameters_schema?.properties || {};
    Object.keys(props).forEach((k) => {
      const type = props[k].type;
      if (type === "string") sampleArgs[k] = `sample_${k}`;
      else if (type === "integer" || type === "number") sampleArgs[k] = 10;
      else if (type === "boolean") sampleArgs[k] = true;
      else if (type === "array") sampleArgs[k] = ["item_1"];
      else sampleArgs[k] = {};
    });
    setTestArgs(JSON.stringify(sampleArgs, null, 2));
    setUserScopes(tool.permission_scope || "*");
  };

  const handleFetchSchema = async (mode: "native" | "openai" | "gemini") => {
    setSchemaMode(mode);
    try {
      if (mode === "openai") {
        const schemas = await aiApi.getOpenAIToolSchemas(selectedCategory || undefined);
        const match = schemas.find((s: any) => s.function?.name === selectedTool?.name);
        setActiveSchema(match || schemas);
      } else if (mode === "gemini") {
        const schemas = await aiApi.getGeminiToolSchemas(selectedCategory || undefined);
        const match = schemas.find((s: any) => s.name === selectedTool?.name);
        setActiveSchema(match || schemas);
      } else {
        setActiveSchema(selectedTool?.parameters_schema);
      }
    } catch (err: any) {
      console.error("Failed to fetch tool schema:", err);
    }
  };

  const handleExecuteSandboxedTool = async () => {
    if (!selectedTool) return;
    setExecuting(true);
    setTestResult(null);

    let parsedArgs = {};
    try {
      parsedArgs = JSON.parse(testArgs);
    } catch (e) {
      alert("Invalid JSON in arguments field.");
      setExecuting(false);
      return;
    }

    try {
      const scopeList = userScopes.split(",").map((s) => s.trim()).filter(Boolean);
      const res = await aiApi.executeTool({
        tool_name: selectedTool.name,
        arguments: parsedArgs,
        user_scopes: scopeList,
      });
      setTestResult(res);
      await fetchToolsAndMetrics();
    } catch (err: any) {
      alert(`Sandboxed execution failed: ${err.message}`);
    } finally {
      setExecuting(false);
    }
  };

  return (
    <div style={{ padding: "2rem", color: "#f8fafc", fontFamily: "Inter, sans-serif" }}>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "2rem" }}>
        <div>
          <h1 style={{ fontSize: "1.875rem", fontWeight: 700, margin: 0, color: "#fff" }}>
            🛠️ Enterprise AI Tool Calling Platform
          </h1>
          <p style={{ color: "#94a3b8", fontSize: "0.9rem", marginTop: "0.25rem" }}>
            Centralized Tool Registry, Security Sandbox, Multi-Provider Schemas, Permissions & Audit Logging
          </p>
        </div>
        <NotificationBell />
      </div>

      {/* Metrics Banner */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "1rem", marginBottom: "2rem" }}>
        <div style={{ background: "#1e293b", padding: "1.25rem", borderRadius: "10px", border: "1px solid #334155" }}>
          <span style={{ color: "#94a3b8", fontSize: "0.8rem", textTransform: "uppercase" }}>Registered Tools</span>
          <div style={{ fontSize: "2rem", fontWeight: 700, color: "#38bdf8", marginTop: "0.25rem" }}>
            {metrics ? metrics.registered_tools_count : "..."}
          </div>
          <span style={{ fontSize: "0.75rem", color: "#64748b" }}>Across 9 Enterprise Domains</span>
        </div>

        <div style={{ background: "#1e293b", padding: "1.25rem", borderRadius: "10px", border: "1px solid #334155" }}>
          <span style={{ color: "#94a3b8", fontSize: "0.8rem", textTransform: "uppercase" }}>Total Tool Calls</span>
          <div style={{ fontSize: "2rem", fontWeight: 700, color: "#4ade80", marginTop: "0.25rem" }}>
            {metrics ? metrics.total_execution_calls.toLocaleString() : "..."}
          </div>
          <span style={{ fontSize: "0.75rem", color: "#64748b" }}>Sandboxed Executions</span>
        </div>

        <div style={{ background: "#1e293b", padding: "1.25rem", borderRadius: "10px", border: "1px solid #334155" }}>
          <span style={{ color: "#94a3b8", fontSize: "0.8rem", textTransform: "uppercase" }}>Overall Success Rate</span>
          <div style={{ fontSize: "2rem", fontWeight: 700, color: "#a855f7", marginTop: "0.25rem" }}>
            {metrics ? `${metrics.overall_success_rate_percent}%` : "..."}
          </div>
          <span style={{ fontSize: "0.75rem", color: "#64748b" }}>
            {metrics ? `${metrics.total_errors} Execution Errors` : ""}
          </span>
        </div>

        <div style={{ background: "#1e293b", padding: "1.25rem", borderRadius: "10px", border: "1px solid #334155" }}>
          <span style={{ color: "#94a3b8", fontSize: "0.8rem", textTransform: "uppercase" }}>Security Status</span>
          <div style={{ fontSize: "1.5rem", fontWeight: 700, color: "#10b981", marginTop: "0.5rem" }}>
            🔒 Sandbox Active
          </div>
          <span style={{ fontSize: "0.75rem", color: "#64748b" }}>Direct Execution Blocked</span>
        </div>
      </div>

      {/* Main Workspace Layout */}
      <div style={{ display: "grid", gridTemplateColumns: "340px 1fr", gap: "1.5rem", marginBottom: "2rem" }}>
        {/* Left Column: Tool Catalog Sidebar */}
        <div style={{ background: "#1e293b", padding: "1.25rem", borderRadius: "10px", border: "1px solid #334155" }}>
          <h3 style={{ margin: "0 0 1rem 0", color: "#f1f5f9" }}>📦 Registered Tool Catalog</h3>
          
          <input
            type="text"
            placeholder="Search tools..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{
              width: "100%",
              padding: "0.5rem",
              background: "#0f172a",
              border: "1px solid #334155",
              borderRadius: "6px",
              color: "#fff",
              marginBottom: "0.5rem",
            }}
          />

          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            style={{ width: "100%", padding: "0.5rem", background: "#0f172a", border: "1px solid #334155", borderRadius: "6px", color: "#fff", marginBottom: "1rem" }}
          >
            <option value="">All Categories (9 Domains)</option>
            <option value="crm">CRM</option>
            <option value="knowledge">Knowledge</option>
            <option value="calendar">Calendar</option>
            <option value="email">Email</option>
            <option value="voice">Voice</option>
            <option value="search">Search</option>
            <option value="database">Database</option>
            <option value="analytics">Analytics</option>
            <option value="workflow">Workflow</option>
          </select>

          <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem", maxHeight: "550px", overflowY: "auto" }}>
            {tools
              .filter((t) => !searchQuery || t.name.toLowerCase().includes(searchQuery.toLowerCase()))
              .map((t) => (
                <div
                  key={t.name}
                  onClick={() => selectTool(t)}
                  style={{
                    padding: "0.75rem",
                    borderRadius: "8px",
                    background: selectedTool?.name === t.name ? "#334155" : "#0f172a",
                    border: selectedTool?.name === t.name ? "1px solid #38bdf8" : "1px solid transparent",
                    cursor: "pointer",
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <span style={{ fontWeight: 600, color: "#fff", fontSize: "0.9rem" }}>{t.name}</span>
                    <span style={{ fontSize: "0.7rem", color: "#38bdf8", background: "rgba(56,189,248,0.1)", padding: "0.1rem 0.4rem", borderRadius: "4px" }}>
                      {t.category}
                    </span>
                  </div>
                  <div style={{ fontSize: "0.75rem", color: "#94a3b8", marginTop: "0.25rem", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                    {t.description}
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between", marginTop: "0.4rem", fontSize: "0.7rem", color: "#64748b" }}>
                    <span>Scope: {t.permission_scope}</span>
                    <span>Calls: {t.execution_count}</span>
                  </div>
                </div>
              ))}
          </div>
        </div>

        {/* Right Column: Schema Inspector & Sandbox Execution Tester */}
        <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
          {/* Tool Definition & Multi-Provider Schema Inspector */}
          <div style={{ background: "#1e293b", padding: "1.5rem", borderRadius: "10px", border: "1px solid #334155" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
              <div>
                <h3 style={{ margin: 0, color: "#f1f5f9" }}>🔍 Tool Schema Inspector — {selectedTool?.name}</h3>
                <p style={{ color: "#94a3b8", fontSize: "0.8rem", margin: "0.25rem 0 0 0" }}>{selectedTool?.description}</p>
              </div>
              <div style={{ display: "flex", gap: "0.5rem" }}>
                <button
                  onClick={() => handleFetchSchema("native")}
                  style={{
                    padding: "0.4rem 0.75rem",
                    background: schemaMode === "native" ? "#4f46e5" : "#334155",
                    color: "#fff",
                    border: "none",
                    borderRadius: "4px",
                    cursor: "pointer",
                    fontSize: "0.8rem",
                  }}
                >
                  Native Schema
                </button>
                <button
                  onClick={() => handleFetchSchema("openai")}
                  style={{
                    padding: "0.4rem 0.75rem",
                    background: schemaMode === "openai" ? "#10b981" : "#334155",
                    color: "#fff",
                    border: "none",
                    borderRadius: "4px",
                    cursor: "pointer",
                    fontSize: "0.8rem",
                  }}
                >
                  OpenAI Format
                </button>
                <button
                  onClick={() => handleFetchSchema("gemini")}
                  style={{
                    padding: "0.4rem 0.75rem",
                    background: schemaMode === "gemini" ? "#0284c7" : "#334155",
                    color: "#fff",
                    border: "none",
                    borderRadius: "4px",
                    cursor: "pointer",
                    fontSize: "0.8rem",
                  }}
                >
                  Gemini Format
                </button>
              </div>
            </div>

            <pre style={{ margin: 0, padding: "1rem", background: "#0f172a", borderRadius: "8px", border: "1px solid #334155", color: "#38bdf8", fontSize: "0.8rem", maxHeight: "250px", overflowY: "auto" }}>
              {JSON.stringify(activeSchema, null, 2)}
            </pre>
          </div>

          {/* Sandboxed Execution Test Runner */}
          <div style={{ background: "#1e293b", padding: "1.5rem", borderRadius: "10px", border: "1px solid #334155" }}>
            <h3 style={{ margin: "0 0 1rem 0", color: "#f1f5f9" }}>🛡️ Sandboxed Tool Execution Tester</h3>
            <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: "1rem", marginBottom: "1rem" }}>
              <div>
                <label style={{ display: "block", color: "#94a3b8", fontSize: "0.8rem", marginBottom: "0.25rem" }}>
                  Input Arguments JSON
                </label>
                <textarea
                  rows={5}
                  value={testArgs}
                  onChange={(e) => setTestArgs(e.target.value)}
                  style={{ width: "100%", padding: "0.5rem", background: "#0f172a", border: "1px solid #334155", borderRadius: "6px", color: "#fff", fontFamily: "monospace", fontSize: "0.85rem" }}
                />
              </div>
              <div>
                <label style={{ display: "block", color: "#94a3b8", fontSize: "0.8rem", marginBottom: "0.25rem" }}>
                  Granted Permission Scopes
                </label>
                <input
                  type="text"
                  placeholder="e.g. crm:read, email:send or *"
                  value={userScopes}
                  onChange={(e) => setUserScopes(e.target.value)}
                  style={{ width: "100%", padding: "0.5rem", background: "#0f172a", border: "1px solid #334155", borderRadius: "6px", color: "#fff", marginBottom: "1rem" }}
                />
                <button
                  onClick={handleExecuteSandboxedTool}
                  disabled={executing}
                  style={{ width: "100%", padding: "0.75rem", background: "#10b981", color: "#fff", border: "none", borderRadius: "6px", fontWeight: 700, cursor: "pointer" }}
                >
                  {executing ? "Executing..." : "⚡ Execute via Sandbox"}
                </button>
              </div>
            </div>

            {testResult && (
              <div style={{ padding: "1rem", background: "#0f172a", borderRadius: "8px", border: "1px solid #334155" }}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.5rem" }}>
                  <span style={{ fontWeight: 600, color: testResult.status === "SUCCESS" ? "#4ade80" : "#ef4444" }}>
                    Status: {testResult.status}
                  </span>
                  <span style={{ fontSize: "0.8rem", color: "#94a3b8" }}>Latency: {testResult.duration_ms} ms</span>
                </div>
                <pre style={{ margin: 0, color: "#e2e8f0", fontSize: "0.8rem", whiteSpace: "pre-wrap" }}>
                  {JSON.stringify(testResult.result || testResult.error, null, 2)}
                </pre>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Execution Audit Log Table */}
      <div style={{ background: "#1e293b", padding: "1.5rem", borderRadius: "10px", border: "1px solid #334155" }}>
        <h3 style={{ margin: "0 0 1rem 0", color: "#f1f5f9" }}>📋 Real-Time Execution Audit Logs</h3>
        <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left", fontSize: "0.85rem" }}>
          <thead>
            <tr style={{ borderBottom: "1px solid #334155", color: "#94a3b8" }}>
              <th style={{ padding: "0.75rem" }}>Timestamp</th>
              <th style={{ padding: "0.75rem" }}>Tool Name</th>
              <th style={{ padding: "0.75rem" }}>Status</th>
              <th style={{ padding: "0.75rem" }}>Duration</th>
              <th style={{ padding: "0.75rem" }}>Input Arguments</th>
            </tr>
          </thead>
          <tbody>
            {logs.slice(0, 10).map((log, idx) => (
              <tr key={idx} style={{ borderBottom: "1px solid #0f172a" }}>
                <td style={{ padding: "0.75rem", color: "#64748b" }}>{new Date(log.timestamp).toLocaleTimeString()}</td>
                <td style={{ padding: "0.75rem", color: "#38bdf8", fontWeight: 600 }}>{log.tool_name}</td>
                <td style={{ padding: "0.75rem" }}>
                  <span
                    style={{
                      padding: "0.2rem 0.5rem",
                      borderRadius: "4px",
                      fontSize: "0.75rem",
                      fontWeight: 700,
                      background: log.status === "SUCCESS" ? "rgba(74,222,128,0.1)" : "rgba(239,68,68,0.1)",
                      color: log.status === "SUCCESS" ? "#4ade80" : "#ef4444",
                    }}
                  >
                    {log.status}
                  </span>
                </td>
                <td style={{ padding: "0.75rem", color: "#e2e8f0" }}>{log.duration_ms} ms</td>
                <td style={{ padding: "0.75rem", color: "#94a3b8", fontFamily: "monospace", fontSize: "0.75rem" }}>
                  {JSON.stringify(log.input_args)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default ToolWorkspace;
