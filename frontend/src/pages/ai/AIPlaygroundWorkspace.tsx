import React, { useEffect, useState } from "react";
import { aiApi } from "../../api/ai";
import { NotificationBell } from "../../components/NotificationBell";

export const AIPlaygroundWorkspace: React.FC = () => {
  // Mode State
  const [isCompareMode, setIsCompareMode] = useState<boolean>(true);

  // Hyperparameters
  const [systemPrompt, setSystemPrompt] = useState<string>("You are an expert Enterprise AI assistant.");
  const [promptText, setPromptText] = useState<string>("Formulate a 3-step outbound sales sequence for B2B SaaS target accounts.");
  const [temperature, setTemperature] = useState<number>(0.7);
  const [topP, setTopP] = useState<number>(0.9);
  const [maxTokens, setMaxTokens] = useState<number>(1024);
  const [jsonMode, setJsonMode] = useState<boolean>(false);

  // Selected Providers/Models
  const [provider1, setProvider1] = useState<string>("gemini");
  const model1 = "gemini-1.5-flash";

  const [provider2, setProvider2] = useState<string>("groq");
  const model2 = "llama3-70b-8192";

  const [provider3, setProvider3] = useState<string>("mistral");
  const model3 = "mistral-large-latest";

  // Execution Results & Sessions
  const [runs, setRuns] = useState<any[]>([]);
  const [executing, setExecuting] = useState<boolean>(false);
  const [sessions, setSessions] = useState<any[]>([]);
  const [sessionTitle, setSessionTitle] = useState<string>("B2B SaaS Sales Sequence Test");

  const fetchSessions = async () => {
    try {
      const data = await aiApi.getPlaygroundSessions(50);
      setSessions(data);
    } catch (err: any) {
      console.error("Failed to fetch playground sessions:", err);
    }
  };

  useEffect(() => {
    fetchSessions();
  }, []);

  const handleExecute = async () => {
    if (!promptText.trim()) return;
    setExecuting(true);
    setRuns([]);

    try {
      if (!isCompareMode) {
        // Single Model Run
        const res = await aiApi.executePlaygroundSingle({
          prompt: promptText,
          provider: provider1,
          model: model1,
          system_prompt: systemPrompt,
          temperature,
          top_p: topP,
          max_tokens: maxTokens,
          json_mode: jsonMode,
        });
        setRuns([res]);
      } else {
        // Multi-Provider Comparison Run
        const targets = [
          { provider: provider1, model: model1 },
          { provider: provider2, model: model2 },
          { provider: provider3, model: model3 },
        ];
        const resList = await aiApi.executePlaygroundCompare({
          prompt: promptText,
          targets,
          system_prompt: systemPrompt,
          temperature,
          top_p: topP,
          max_tokens: maxTokens,
          json_mode: jsonMode,
        });
        setRuns(resList);
      }
    } catch (err: any) {
      alert(`Playground execution failed: ${err.message}`);
    } finally {
      setExecuting(false);
    }
  };

  const handleSaveSession = async () => {
    if (runs.length === 0) return;
    try {
      await aiApi.savePlaygroundSession({
        title: sessionTitle,
        prompt: promptText,
        runs,
        system_prompt: systemPrompt,
        hyperparameters: { temperature, topP, maxTokens, jsonMode },
      });
      alert("Playground session saved successfully!");
      await fetchSessions();
    } catch (err: any) {
      alert(`Save session failed: ${err.message}`);
    }
  };

  const handleExportMarkdown = async () => {
    if (runs.length === 0) return;
    try {
      const md = await aiApi.exportPlaygroundResults({
        session_data: {
          title: sessionTitle,
          prompt: promptText,
          runs,
          created_at: new Date().toISOString(),
        },
        format_type: "markdown",
      });

      const blob = new Blob([md], { type: "text/markdown" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `playground_report_${Date.now()}.md`;
      a.click();
    } catch (err: any) {
      alert(`Export failed: ${err.message}`);
    }
  };

  return (
    <div style={{ padding: "2rem", color: "#f8fafc", fontFamily: "Inter, sans-serif" }}>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1.5rem" }}>
        <div>
          <h1 style={{ fontSize: "1.875rem", fontWeight: 700, margin: 0, color: "#fff" }}>
            🧪 Enterprise AI Playground & Model Comparison
          </h1>
          <p style={{ color: "#94a3b8", fontSize: "0.9rem", marginTop: "0.25rem" }}>
            Side-by-Side Provider Benchmarking, Real-time SSE Streaming, Hyperparameter Tuning & Telemetry
          </p>
        </div>
        <div style={{ display: "flex", gap: "1rem", alignItems: "center" }}>
          <span style={{ fontSize: "0.8rem", color: "#94a3b8" }}>Saved Sessions: {sessions.length}</span>
          <button
            onClick={() => setIsCompareMode(!isCompareMode)}
            style={{ padding: "0.5rem 1rem", background: isCompareMode ? "#a855f7" : "#334155", color: "#fff", border: "none", borderRadius: "6px", fontWeight: 700, cursor: "pointer" }}
          >
            {isCompareMode ? "⚔️ Compare Mode: ACTIVE (3 Providers)" : "🎯 Single Model Mode"}
          </button>
          <NotificationBell />
        </div>
      </div>

      {/* Main Grid: Control Panel + Output Workspace */}
      <div style={{ display: "grid", gridTemplateColumns: "320px 1fr", gap: "1.5rem", marginBottom: "2rem" }}>
        {/* Left Sidebar: Hyperparameters & Target Config */}
        <div style={{ background: "#1e293b", padding: "1.25rem", borderRadius: "10px", border: "1px solid #334155" }}>
          <h3 style={{ margin: "0 0 1rem 0", color: "#f1f5f9" }}>🎛️ Hyperparameters</h3>

          <div style={{ marginBottom: "0.75rem" }}>
            <label style={{ display: "block", color: "#94a3b8", fontSize: "0.8rem", marginBottom: "0.25rem" }}>System Prompt</label>
            <textarea
              rows={3}
              value={systemPrompt}
              onChange={(e) => setSystemPrompt(e.target.value)}
              style={{ width: "100%", padding: "0.5rem", background: "#0f172a", border: "1px solid #334155", borderRadius: "6px", color: "#fff", fontSize: "0.8rem" }}
            />
          </div>

          <div style={{ marginBottom: "0.75rem" }}>
            <div style={{ display: "flex", justifyContent: "space-between", color: "#94a3b8", fontSize: "0.8rem" }}>
              <span>Temperature</span>
              <span>{temperature}</span>
            </div>
            <input
              type="range"
              min="0"
              max="2"
              step="0.1"
              value={temperature}
              onChange={(e) => setTemperature(parseFloat(e.target.value))}
              style={{ width: "100%" }}
            />
          </div>

          <div style={{ marginBottom: "0.75rem" }}>
            <div style={{ display: "flex", justifyContent: "space-between", color: "#94a3b8", fontSize: "0.8rem" }}>
              <span>Top P</span>
              <span>{topP}</span>
            </div>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={topP}
              onChange={(e) => setTopP(parseFloat(e.target.value))}
              style={{ width: "100%" }}
            />
          </div>

          <div style={{ marginBottom: "0.75rem" }}>
            <label style={{ display: "block", color: "#94a3b8", fontSize: "0.8rem", marginBottom: "0.25rem" }}>Max Tokens</label>
            <input
              type="number"
              value={maxTokens}
              onChange={(e) => setMaxTokens(parseInt(e.target.value) || 1024)}
              style={{ width: "100%", padding: "0.4rem", background: "#0f172a", border: "1px solid #334155", borderRadius: "4px", color: "#fff" }}
            />
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "1.25rem" }}>
            <input
              type="checkbox"
              id="json_mode_chk"
              checked={jsonMode}
              onChange={(e) => setJsonMode(e.target.checked)}
            />
            <label htmlFor="json_mode_chk" style={{ color: "#fff", fontSize: "0.85rem" }}>Force JSON Mode</label>
          </div>

          <h4 style={{ margin: "1rem 0 0.5rem 0", color: "#f1f5f9" }}>Provider 1 (Primary)</h4>
          <select
            value={provider1}
            onChange={(e) => setProvider1(e.target.value)}
            style={{ width: "100%", padding: "0.4rem", background: "#0f172a", border: "1px solid #334155", borderRadius: "4px", color: "#fff", marginBottom: "0.5rem" }}
          >
            <option value="gemini">Gemini (Google)</option>
            <option value="groq">Groq (Llama-3 Fast)</option>
            <option value="mistral">Mistral AI</option>
            <option value="openrouter">OpenRouter</option>
            <option value="openai">OpenAI (GPT-4o)</option>
            <option value="claude">Claude (Anthropic)</option>
            <option value="deepseek">DeepSeek R1</option>
          </select>

          {isCompareMode && (
            <>
              <h4 style={{ margin: "0.75rem 0 0.5rem 0", color: "#f1f5f9" }}>Provider 2</h4>
              <select
                value={provider2}
                onChange={(e) => setProvider2(e.target.value)}
                style={{ width: "100%", padding: "0.4rem", background: "#0f172a", border: "1px solid #334155", borderRadius: "4px", color: "#fff", marginBottom: "0.5rem" }}
              >
                <option value="groq">Groq (Llama-3 Fast)</option>
                <option value="gemini">Gemini (Google)</option>
                <option value="mistral">Mistral AI</option>
                <option value="deepseek">DeepSeek R1</option>
              </select>

              <h4 style={{ margin: "0.75rem 0 0.5rem 0", color: "#f1f5f9" }}>Provider 3</h4>
              <select
                value={provider3}
                onChange={(e) => setProvider3(e.target.value)}
                style={{ width: "100%", padding: "0.4rem", background: "#0f172a", border: "1px solid #334155", borderRadius: "4px", color: "#fff" }}
              >
                <option value="mistral">Mistral AI</option>
                <option value="deepseek">DeepSeek R1</option>
                <option value="openrouter">OpenRouter</option>
              </select>
            </>
          )}
        </div>

        {/* Right Output Console: Prompt Composition & Side-by-Side Outputs */}
        <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
          {/* Prompt Input Area */}
          <div style={{ background: "#1e293b", padding: "1.25rem", borderRadius: "10px", border: "1px solid #334155" }}>
            <h3 style={{ margin: "0 0 0.75rem 0", color: "#f1f5f9" }}>📝 User Prompt Composition</h3>
            <textarea
              rows={4}
              value={promptText}
              onChange={(e) => setPromptText(e.target.value)}
              style={{ width: "100%", padding: "0.75rem", background: "#0f172a", border: "1px solid #334155", borderRadius: "6px", color: "#fff", fontSize: "0.9rem", marginBottom: "0.75rem" }}
            />
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div style={{ display: "flex", gap: "0.5rem" }}>
                <input
                  type="text"
                  placeholder="Session Title"
                  value={sessionTitle}
                  onChange={(e) => setSessionTitle(e.target.value)}
                  style={{ padding: "0.4rem 0.6rem", background: "#0f172a", border: "1px solid #334155", borderRadius: "4px", color: "#fff", fontSize: "0.8rem" }}
                />
                <button onClick={handleSaveSession} style={{ padding: "0.4rem 0.8rem", background: "#334155", color: "#fff", border: "none", borderRadius: "4px", fontWeight: 600, cursor: "pointer", fontSize: "0.8rem" }}>
                  💾 Save Session
                </button>
                <button onClick={handleExportMarkdown} style={{ padding: "0.4rem 0.8rem", background: "#f59e0b", color: "#000", border: "none", borderRadius: "4px", fontWeight: 700, cursor: "pointer", fontSize: "0.8rem" }}>
                  📥 Export Markdown
                </button>
              </div>
              <button
                onClick={handleExecute}
                disabled={executing}
                style={{ padding: "0.6rem 1.5rem", background: "#10b981", color: "#fff", border: "none", borderRadius: "6px", fontWeight: 700, cursor: "pointer" }}
              >
                {executing ? "Executing Comparison..." : "⚡ Execute Playground Prompt"}
              </button>
            </div>
          </div>

          {/* Side-by-Side Model Outputs Grid */}
          <div style={{ display: "grid", gridTemplateColumns: isCompareMode ? "repeat(auto-fit, minmax(280px, 1fr))" : "1fr", gap: "1rem" }}>
            {runs.map((r, idx) => (
              <div key={idx} style={{ background: "#1e293b", padding: "1.25rem", borderRadius: "10px", border: "1px solid #334155", display: "flex", flexDirection: "column" }}>
                {/* Model Header */}
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.75rem", borderBottom: "1px solid #334155", paddingBottom: "0.5rem" }}>
                  <span style={{ fontWeight: 700, color: "#38bdf8", textTransform: "uppercase" }}>{r.provider}</span>
                  <span style={{ fontSize: "0.75rem", padding: "0.2rem 0.5rem", borderRadius: "4px", background: "rgba(16,185,129,0.1)", color: "#10b981", fontWeight: 700 }}>
                    ⚡ {r.duration_ms} ms
                  </span>
                </div>

                {/* Response Content */}
                <div style={{ flex: 1, background: "#0f172a", padding: "0.75rem", borderRadius: "6px", color: "#e2e8f0", fontSize: "0.85rem", fontFamily: "monospace", overflowY: "auto", maxHeight: "280px", whiteSpace: "pre-wrap", marginBottom: "0.75rem" }}>
                  {r.content}
                </div>

                {/* Telemetry Metrics Footer */}
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.75rem", color: "#94a3b8" }}>
                  <span>Tokens: {r.input_tokens} in / {r.output_tokens} out</span>
                  <span style={{ color: "#f59e0b", fontWeight: 700 }}>Cost: ${r.cost_usd.toFixed(5)}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AIPlaygroundWorkspace;
