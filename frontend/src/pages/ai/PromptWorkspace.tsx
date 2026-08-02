import React, { useEffect, useState } from "react";
import { aiApi, AIPromptTemplateItem } from "../../api/ai";
import { NotificationBell } from "../../components/NotificationBell";

export const PromptWorkspace: React.FC = () => {
  const [prompts, setPrompts] = useState<AIPromptTemplateItem[]>([]);
  const [selectedPrompt, setSelectedPrompt] = useState<AIPromptTemplateItem | null>(null);
  const [history, setHistory] = useState<any[]>([]);
  const [diffData, setDiffData] = useState<any>(null);
  const [testResult, setTestResult] = useState<any>(null);

  // Search & Filters
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [selectedCategory, setSelectedCategory] = useState<string>("");
  const [selectedStatus, setSelectedStatus] = useState<string>("");

  // Editor State
  const [templateId, setTemplateId] = useState<string>("");
  const [name, setName] = useState<string>("");
  const [category, setCategory] = useState<string>("conversation");
  const [tags, setTags] = useState<string>("");
  const [systemTemplate, setSystemTemplate] = useState<string>("");
  const [userTemplate, setUserTemplate] = useState<string>("");
  const [changesDesc, setChangesDesc] = useState<string>("");

  // Test Runner State
  const [testVars, setTestVars] = useState<Record<string, string>>({});
  const [testProvider, setTestProvider] = useState<string>("gemini");
  const [testModel, setTestModel] = useState<string>("gemini-1.5-flash");
  const [testing, setTesting] = useState<boolean>(false);

  const fetchPrompts = async () => {
    try {
      const data = await aiApi.getPrompts();
      setPrompts(data);
      if (data.length > 0 && !selectedPrompt) {
        selectPrompt(data[0]);
      }
    } catch (err: any) {
      console.error("Failed to fetch prompts:", err);
    }
  };

  useEffect(() => {
    fetchPrompts();
  }, []);

  const selectPrompt = async (item: AIPromptTemplateItem) => {
    setSelectedPrompt(item);
    setTemplateId(item.template_id);
    setName(item.name);
    setCategory(item.category);
    setSystemTemplate(item.system_prompt_template || "");
    setUserTemplate(item.user_prompt_template);
    setDiffData(null);
    setTestResult(null);

    // Init test vars
    const initialVars: Record<string, string> = {};
    (item.variables || []).forEach((v: string) => {
      initialVars[v] = `Sample ${v}`;
    });
    setTestVars(initialVars);

    // Fetch version history
    try {
      const historyData = await aiApi.getPromptHistory(item.template_id);
      setHistory(historyData);
    } catch (err: any) {
      console.error("Failed to fetch version history:", err);
    }
  };

  const handleSavePrompt = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!templateId || !name || !userTemplate) return;
    try {
      const tagList = tags.split(",").map((t) => t.trim()).filter(Boolean);
      await aiApi.savePrompt({
        template_id: templateId,
        name,
        category,
        tags: tagList,
        user_prompt_template: userTemplate,
        system_prompt_template: systemTemplate,
        changes_description: changesDesc || "Updated prompt template",
      });
      setChangesDesc("");
      await fetchPrompts();
      alert("Prompt template saved successfully!");
    } catch (err: any) {
      alert(`Save failed: ${err.message}`);
    }
  };

  const handleRollback = async (version: number) => {
    if (!selectedPrompt) return;
    if (!confirm(`Are you sure you want to rollback to Version ${version}?`)) return;
    try {
      await aiApi.rollbackPrompt(selectedPrompt.template_id, version);
      await fetchPrompts();
      alert(`Rolled back to version ${version}`);
    } catch (err: any) {
      alert(`Rollback failed: ${err.message}`);
    }
  };

  const handleCompareDiff = async (vA: number, vB: number) => {
    if (!selectedPrompt) return;
    try {
      const data = await aiApi.getPromptDiff(selectedPrompt.template_id, vA, vB);
      setDiffData(data);
    } catch (err: any) {
      alert(`Diff failed: ${err.message}`);
    }
  };

  const handleUpdateStatus = async (newStatus: string) => {
    if (!selectedPrompt) return;
    try {
      await aiApi.updatePromptApproval(selectedPrompt.template_id, newStatus);
      await fetchPrompts();
    } catch (err: any) {
      alert(`Status update failed: ${err.message}`);
    }
  };

  const handleTestPrompt = async () => {
    if (!selectedPrompt) return;
    setTesting(true);
    setTestResult(null);
    try {
      const res = await aiApi.testPromptTemplate(selectedPrompt.template_id, {
        variables: testVars,
        provider: testProvider,
        model: testModel,
      });
      setTestResult(res);
    } catch (err: any) {
      alert(`Test failed: ${err.message}`);
    } finally {
      setTesting(false);
    }
  };

  return (
    <div style={{ padding: "2rem", color: "#f8fafc", fontFamily: "Inter, sans-serif" }}>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "2rem" }}>
        <div>
          <h1 style={{ fontSize: "1.875rem", fontWeight: 700, margin: 0, color: "#fff" }}>
            📖 Enterprise Prompt Management Platform
          </h1>
          <p style={{ color: "#94a3b8", fontSize: "0.9rem", marginTop: "0.25rem" }}>
            Library, Versioning, Variables Engine, Approval Workflows, Testing Playground & Diff Viewer
          </p>
        </div>
        <NotificationBell />
      </div>

      {/* Main Workspace Layout */}
      <div style={{ display: "grid", gridTemplateColumns: "320px 1fr", gap: "1.5rem" }}>
        {/* Left Column: Prompt Library Catalog */}
        <div style={{ background: "#1e293b", padding: "1.25rem", borderRadius: "10px", border: "1px solid #334155" }}>
          <h3 style={{ margin: "0 0 1rem 0", color: "#f1f5f9" }}>📚 Prompt Library</h3>
          
          <input
            type="text"
            placeholder="Search prompts..."
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

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.5rem", marginBottom: "1rem" }}>
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              style={{ padding: "0.4rem", background: "#0f172a", border: "1px solid #334155", borderRadius: "4px", color: "#fff", fontSize: "0.8rem" }}
            >
              <option value="">All Categories</option>
              <option value="conversation">Conversation</option>
              <option value="research">Research</option>
              <option value="outreach">Outreach</option>
              <option value="score">Scoring</option>
              <option value="summary">Summary</option>
            </select>
            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              style={{ padding: "0.4rem", background: "#0f172a", border: "1px solid #334155", borderRadius: "4px", color: "#fff", fontSize: "0.8rem" }}
            >
              <option value="">All Statuses</option>
              <option value="DRAFT">DRAFT</option>
              <option value="IN_REVIEW">IN_REVIEW</option>
              <option value="APPROVED">APPROVED</option>
              <option value="PUBLISHED">PUBLISHED</option>
            </select>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem", maxHeight: "600px", overflowY: "auto" }}>
            {prompts
              .filter((p) => !searchQuery || p.name.toLowerCase().includes(searchQuery.toLowerCase()))
              .map((p) => (
                <div
                  key={p.template_id}
                  onClick={() => selectPrompt(p)}
                  style={{
                    padding: "0.75rem",
                    borderRadius: "8px",
                    background: selectedPrompt?.template_id === p.template_id ? "#334155" : "#0f172a",
                    border: selectedPrompt?.template_id === p.template_id ? "1px solid #6366f1" : "1px solid transparent",
                    cursor: "pointer",
                  }}
                >
                  <div style={{ fontWeight: 600, color: "#fff", fontSize: "0.9rem" }}>{p.name}</div>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "0.4rem" }}>
                    <span style={{ fontSize: "0.7rem", color: "#38bdf8", background: "rgba(56,189,248,0.1)", padding: "0.1rem 0.4rem", borderRadius: "4px" }}>
                      {p.category}
                    </span>
                    <span style={{ fontSize: "0.7rem", color: "#a855f7", fontWeight: 700 }}>
                      v{p.current_version || 1}
                    </span>
                  </div>
                </div>
              ))}
          </div>
        </div>

        {/* Right Column: Template Editor, History, Diff & Playground */}
        <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
          {/* Template Editor */}
          <div style={{ background: "#1e293b", padding: "1.5rem", borderRadius: "10px", border: "1px solid #334155" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
              <h3 style={{ margin: 0, color: "#f1f5f9" }}>✏️ Prompt Template Editor</h3>
              {selectedPrompt && (
                <div style={{ display: "flex", gap: "0.5rem" }}>
                  <button
                    onClick={() => handleUpdateStatus("APPROVED")}
                    style={{ padding: "0.35rem 0.75rem", background: "#10b981", color: "#fff", border: "none", borderRadius: "4px", cursor: "pointer", fontSize: "0.8rem" }}
                  >
                    Approve
                  </button>
                  <button
                    onClick={() => handleUpdateStatus("PUBLISHED")}
                    style={{ padding: "0.35rem 0.75rem", background: "#6366f1", color: "#fff", border: "none", borderRadius: "4px", cursor: "pointer", fontSize: "0.8rem" }}
                  >
                    Publish
                  </button>
                </div>
              )}
            </div>

            <form onSubmit={handleSavePrompt} style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr 1fr", gap: "1rem" }}>
                <div>
                  <label style={{ display: "block", color: "#94a3b8", fontSize: "0.8rem", marginBottom: "0.25rem" }}>Template ID</label>
                  <input
                    type="text"
                    value={templateId}
                    onChange={(e) => setTemplateId(e.target.value)}
                    style={{ width: "100%", padding: "0.5rem", background: "#0f172a", border: "1px solid #334155", borderRadius: "6px", color: "#fff" }}
                  />
                </div>
                <div>
                  <label style={{ display: "block", color: "#94a3b8", fontSize: "0.8rem", marginBottom: "0.25rem" }}>Name</label>
                  <input
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    style={{ width: "100%", padding: "0.5rem", background: "#0f172a", border: "1px solid #334155", borderRadius: "6px", color: "#fff" }}
                  />
                </div>
                <div>
                  <label style={{ display: "block", color: "#94a3b8", fontSize: "0.8rem", marginBottom: "0.25rem" }}>Category</label>
                  <select
                    value={category}
                    onChange={(e) => setCategory(e.target.value)}
                    style={{ width: "100%", padding: "0.5rem", background: "#0f172a", border: "1px solid #334155", borderRadius: "6px", color: "#fff" }}
                  >
                    <option value="conversation">Conversation</option>
                    <option value="research">Research</option>
                    <option value="outreach">Outreach</option>
                    <option value="score">Scoring</option>
                    <option value="summary">Summary</option>
                    <option value="reasoning">Reasoning</option>
                    <option value="coding">Coding</option>
                  </select>
                </div>
                <div>
                  <label style={{ display: "block", color: "#94a3b8", fontSize: "0.8rem", marginBottom: "0.25rem" }}>Tags (comma-separated)</label>
                  <input
                    type="text"
                    placeholder="e.g. outreach, b2b"
                    value={tags}
                    onChange={(e) => setTags(e.target.value)}
                    style={{ width: "100%", padding: "0.5rem", background: "#0f172a", border: "1px solid #334155", borderRadius: "6px", color: "#fff" }}
                  />
                </div>
              </div>

              <div>
                <label style={{ display: "block", color: "#94a3b8", fontSize: "0.8rem", marginBottom: "0.25rem" }}>System Instruction Template</label>
                <textarea
                  rows={2}
                  value={systemTemplate}
                  onChange={(e) => setSystemTemplate(e.target.value)}
                  style={{ width: "100%", padding: "0.5rem", background: "#0f172a", border: "1px solid #334155", borderRadius: "6px", color: "#fff", fontFamily: "monospace" }}
                />
              </div>

              <div>
                <label style={{ display: "block", color: "#94a3b8", fontSize: "0.8rem", marginBottom: "0.25rem" }}>User Prompt Template (Use &#123;var&#125; or &#123;&#123;var&#125;&#125;)</label>
                <textarea
                  rows={4}
                  value={userTemplate}
                  onChange={(e) => setUserTemplate(e.target.value)}
                  style={{ width: "100%", padding: "0.5rem", background: "#0f172a", border: "1px solid #334155", borderRadius: "6px", color: "#fff", fontFamily: "monospace" }}
                />
              </div>

              <div>
                <label style={{ display: "block", color: "#94a3b8", fontSize: "0.8rem", marginBottom: "0.25rem" }}>Commit / Change Description</label>
                <input
                  type="text"
                  placeholder="e.g. Added personalization guidelines"
                  value={changesDesc}
                  onChange={(e) => setChangesDesc(e.target.value)}
                  style={{ width: "100%", padding: "0.5rem", background: "#0f172a", border: "1px solid #334155", borderRadius: "6px", color: "#fff" }}
                />
              </div>

              <button
                type="submit"
                style={{ padding: "0.6rem 1.25rem", background: "#4f46e5", color: "#fff", border: "none", borderRadius: "6px", fontWeight: 600, cursor: "pointer", alignSelf: "flex-start" }}
              >
                💾 Save & Commit New Version
              </button>
            </form>
          </div>

          {/* Interactive Testing Playground */}
          <div style={{ background: "#1e293b", padding: "1.5rem", borderRadius: "10px", border: "1px solid #334155" }}>
            <h3 style={{ margin: "0 0 1rem 0", color: "#f1f5f9" }}>🧪 Interactive Testing Playground</h3>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem", marginBottom: "1rem" }}>
              <div>
                <label style={{ display: "block", color: "#94a3b8", fontSize: "0.8rem", marginBottom: "0.25rem" }}>AI Provider</label>
                <select
                  value={testProvider}
                  onChange={(e) => setTestProvider(e.target.value)}
                  style={{ width: "100%", padding: "0.5rem", background: "#0f172a", border: "1px solid #334155", borderRadius: "6px", color: "#fff" }}
                >
                  <option value="gemini">Google Gemini</option>
                  <option value="groq">Groq AI</option>
                  <option value="mistral">Mistral AI</option>
                  <option value="openrouter">OpenRouter</option>
                </select>
              </div>
              <div>
                <label style={{ display: "block", color: "#94a3b8", fontSize: "0.8rem", marginBottom: "0.25rem" }}>Model ID</label>
                <input
                  type="text"
                  value={testModel}
                  onChange={(e) => setTestModel(e.target.value)}
                  style={{ width: "100%", padding: "0.5rem", background: "#0f172a", border: "1px solid #334155", borderRadius: "6px", color: "#fff" }}
                />
              </div>
            </div>

            {/* Variable Inputs */}
            {selectedPrompt && (selectedPrompt.variables || []).length > 0 && (
              <div style={{ marginBottom: "1rem" }}>
                <label style={{ display: "block", color: "#94a3b8", fontSize: "0.8rem", marginBottom: "0.5rem" }}>Test Variables</label>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.5rem" }}>
                  {(selectedPrompt.variables || []).map((v) => (
                    <div key={v}>
                      <span style={{ fontSize: "0.75rem", color: "#38bdf8" }}>{v}</span>
                      <input
                        type="text"
                        value={testVars[v] || ""}
                        onChange={(e) => setTestVars({ ...testVars, [v]: e.target.value })}
                        style={{ width: "100%", padding: "0.4rem", background: "#0f172a", border: "1px solid #334155", borderRadius: "4px", color: "#fff", fontSize: "0.85rem" }}
                      />
                    </div>
                  ))}
                </div>
              </div>
            )}

            <button
              onClick={handleTestPrompt}
              disabled={testing}
              style={{ padding: "0.6rem 1.25rem", background: "#10b981", color: "#fff", border: "none", borderRadius: "6px", fontWeight: 600, cursor: "pointer" }}
            >
              {testing ? "Testing..." : "▶️ Execute Test Run"}
            </button>

            {testResult && (
              <div style={{ marginTop: "1rem", padding: "1rem", background: "#0f172a", borderRadius: "8px", border: "1px solid #334155" }}>
                <div style={{ color: "#38bdf8", fontWeight: 600, fontSize: "0.85rem", marginBottom: "0.5rem" }}>Test Execution Result:</div>
                <pre style={{ margin: 0, color: "#e2e8f0", fontSize: "0.8rem", whiteSpace: "pre-wrap" }}>
                  {JSON.stringify(testResult.gateway_response, null, 2)}
                </pre>
              </div>
            )}
          </div>

          {/* Version History & Diff Viewer */}
          <div style={{ background: "#1e293b", padding: "1.5rem", borderRadius: "10px", border: "1px solid #334155" }}>
            <h3 style={{ margin: "0 0 1rem 0", color: "#f1f5f9" }}>📜 Version History & Diff Viewer</h3>
            <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
              {history.map((ver) => (
                <div
                  key={ver.version}
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    padding: "0.75rem",
                    background: "#0f172a",
                    borderRadius: "6px",
                  }}
                >
                  <div>
                    <span style={{ fontWeight: 700, color: "#38bdf8", marginRight: "0.5rem" }}>
                      Version {ver.version} ({ver.version_tag || "v1.0.0"})
                    </span>
                    <span style={{ color: "#94a3b8", fontSize: "0.8rem" }}>{ver.changes_description}</span>
                  </div>
                  <div style={{ display: "flex", gap: "0.5rem" }}>
                    <button
                      onClick={() => handleCompareDiff(ver.version - 1, ver.version)}
                      disabled={ver.version <= 1}
                      style={{ padding: "0.3rem 0.6rem", background: "#334155", color: "#fff", border: "none", borderRadius: "4px", cursor: "pointer", fontSize: "0.75rem" }}
                    >
                      Compare Diff
                    </button>
                    <button
                      onClick={() => handleRollback(ver.version)}
                      style={{ padding: "0.3rem 0.6rem", background: "#f59e0b", color: "#fff", border: "none", borderRadius: "4px", cursor: "pointer", fontSize: "0.75rem" }}
                    >
                      Rollback
                    </button>
                  </div>
                </div>
              ))}
            </div>

            {diffData && (
              <div style={{ marginTop: "1rem", padding: "1rem", background: "#0f172a", borderRadius: "8px", border: "1px solid #334155" }}>
                <div style={{ fontWeight: 600, color: "#a855f7", marginBottom: "0.5rem" }}>
                  Diff Preview (v{diffData.version_a} ➔ v{diffData.version_b}):
                </div>
                <pre style={{ margin: 0, color: "#4ade80", fontSize: "0.8rem", whiteSpace: "pre-wrap" }}>
                  {diffData.diff_lines.join("\n") || "No text changes detected."}
                </pre>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default PromptWorkspace;
