import React, { useEffect, useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../contexts/AuthContext";
import { chatApi, ChatSession, ChatMessage, ActionCard } from "../../api/chat";

const SLASH_COMMANDS = [
  { cmd: "/discover", desc: "Discover target companies & leads" },
  { cmd: "/research", desc: "Deep company research & firmographics" },
  { cmd: "/score", desc: "Lead qualification & predictive fit score" },
  { cmd: "/outreach", desc: "Draft cold email & LinkedIn sequence" },
  { cmd: "/report", desc: "Generate Executive Sales Report" },
  { cmd: "/workflows", desc: "Execute autonomous workflow pipeline" },
  { cmd: "/help", desc: "View all platform capabilities & commands" },
  { cmd: "/history", desc: "View analytics & execution history" },
];

export const ChatPage: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  // Sessions state
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSession, setActiveSession] = useState<ChatSession | null>(null);
  const [searchTerm, setSearchTerm] = useState("");

  // Messages state
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMsg, setInputMsg] = useState("");
  const [companyOverride, setCompanyOverride] = useState("");
  const [loading, setLoading] = useState(false);
  const [stageIndicator, setStageIndicator] = useState<string | null>(null);
  const [showSlashMenu, setShowSlashMenu] = useState(false);

  // Selected visual execution for right sidebar
  const [activeVisualization, setActiveVisualization] = useState<Record<string, any> | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchSessions();
  }, []);

  const fetchSessions = async () => {
    try {
      const data = await chatApi.listSessions({ limit: 50 });
      setSessions(data.items);
      if (data.items.length > 0 && !activeSession) {
        selectSession(data.items[0]);
      }
    } catch {}
  };

  const selectSession = async (sess: ChatSession) => {
    setActiveSession(sess);
    try {
      const history = await chatApi.getHistory(sess.session_id);
      setMessages(history);
      if (history.length > 0) {
        const lastWithVis = [...history].reverse().find(m => m.execution_visualization && Object.keys(m.execution_visualization).length > 0);
        if (lastWithVis?.execution_visualization) setActiveVisualization(lastWithVis.execution_visualization);
      }
    } catch {}
  };

  const handleNewSession = async () => {
    setActiveSession(null);
    setMessages([]);
    setActiveVisualization(null);
  };

  const handleSend = async (customMessage?: string) => {
    const textToSend = customMessage || inputMsg;
    if (!textToSend.trim() || loading) return;

    setLoading(true);
    setStageIndicator("Thinking...");
    setShowSlashMenu(false);
    setInputMsg("");

    try {
      setTimeout(() => setStageIndicator("Planning Workflow..."), 300);
      setTimeout(() => setStageIndicator("Executing Workflow Engine..."), 600);

      const resMessage = await chatApi.sendMessage({
        message: textToSend.trim(),
        session_id: activeSession?.session_id,
        company_name: companyOverride.trim() || undefined,
      });

      setMessages(prev => [...prev, 
        { message_id: `user_${Date.now()}`, session_id: resMessage.session_id, role: "user", content: textToSend, action_cards: [], timestamp: new Date().toISOString() },
        resMessage
      ]);

      if (resMessage.execution_visualization) {
        setActiveVisualization(resMessage.execution_visualization);
      }

      fetchSessions();
    } catch (err: any) {
      setMessages(prev => [...prev, {
        message_id: `err_${Date.now()}`,
        session_id: activeSession?.session_id || "new",
        role: "assistant",
        content: `❌ Error processing query: ${err?.response?.data?.detail || err.message}`,
        action_cards: [],
        timestamp: new Date().toISOString(),
      }]);
    } finally {
      setLoading(false);
      setStageIndicator(null);
    }
  };

  const handleActionClick = (card: ActionCard) => {
    if (card.action_type === "research" && card.payload.company_name) {
      handleSend(`/research ${card.payload.company_name}`);
    } else if (card.action_type === "outreach" && card.payload.company_name) {
      handleSend(`/outreach ${card.payload.company_name}`);
    } else if (card.action_type === "open_report") {
      handleSend(`/report ${card.payload.company_name || ""}`);
    } else if (card.action_type === "run_workflow") {
      handleSend(`/workflows ${card.payload.company_name || ""}`);
    } else {
      handleSend(`Execute ${card.title}`);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    setInputMsg(val);
    if (val.startsWith("/")) {
      setShowSlashMenu(true);
    } else {
      setShowSlashMenu(false);
    }
  };

  const selectSlashCommand = (cmd: string) => {
    setInputMsg(`${cmd} `);
    setShowSlashMenu(false);
  };

  const filteredSessions = sessions.filter(s => s.title.toLowerCase().includes(searchTerm.toLowerCase()));

  return (
    <div style={{ minHeight: "100vh", background: "#0a0f1e", color: "#e2e8f0", fontFamily: "'Inter', sans-serif", display: "flex", flexDirection: "column" }}>
      {/* Top Header */}
      <nav style={{ background: "rgba(15,23,42,0.95)", borderBottom: "1px solid rgba(99,102,241,0.2)", padding: "0 2rem", height: "60px", display: "flex", alignItems: "center", justifyContent: "space-between", backdropFilter: "blur(12px)", position: "sticky", top: 0, zIndex: 100 }}>
        <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
          <div style={{ fontSize: "1.4rem", fontWeight: 800, background: "linear-gradient(135deg, #6366f1, #8b5cf6)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
            LeadForgeAI
          </div>
          <div style={{ color: "#64748b", fontSize: "0.85rem" }}>/ Enterprise Conversational CRM</div>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
          <button onClick={() => navigate("/workflows")} style={{ background: "none", border: "1px solid rgba(99,102,241,0.3)", color: "#a5b4fc", padding: "0.4rem 1rem", borderRadius: "6px", cursor: "pointer", fontSize: "0.85rem" }}>⚡ Workflows</button>
          <button onClick={() => navigate("/agents")} style={{ background: "none", border: "1px solid rgba(99,102,241,0.3)", color: "#94a3b8", padding: "0.4rem 1rem", borderRadius: "6px", cursor: "pointer", fontSize: "0.85rem" }}>🤖 Agents</button>
          <span style={{ color: "#64748b", fontSize: "0.85rem" }}>{user?.email}</span>
          <button onClick={logout} style={{ background: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.3)", color: "#f87171", padding: "0.4rem 1rem", borderRadius: "6px", cursor: "pointer", fontSize: "0.85rem" }}>Logout</button>
        </div>
      </nav>

      <div style={{ display: "grid", gridTemplateColumns: "300px 1fr 340px", flex: 1, minHeight: 0 }}>
        {/* Left Sidebar: Sessions */}
        <aside style={{ background: "rgba(15,23,42,0.85)", borderRight: "1px solid rgba(99,102,241,0.15)", display: "flex", flexDirection: "column", overflow: "hidden" }}>
          <div style={{ padding: "1rem", borderBottom: "1px solid rgba(99,102,241,0.15)", display: "flex", flexDirection: "column", gap: "0.75rem" }}>
            <button onClick={handleNewSession} style={{ padding: "0.6rem", borderRadius: "8px", border: "none", background: "linear-gradient(135deg, #6366f1, #8b5cf6)", color: "#fff", fontWeight: 700, fontSize: "0.85rem", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center", gap: "0.5rem" }}>
              <span>+</span> New Conversation
            </button>
            <input value={searchTerm} onChange={e => setSearchTerm(e.target.value)} placeholder="Search sessions…" style={{ padding: "0.5rem 0.75rem", borderRadius: "6px", border: "1px solid rgba(99,102,241,0.25)", background: "rgba(30,41,59,0.6)", color: "#e2e8f0", fontSize: "0.8rem", outline: "none" }} />
          </div>

          <div style={{ flex: 1, overflowY: "auto", padding: "0.75rem" }}>
            <div style={{ fontSize: "0.75rem", color: "#64748b", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: "0.5rem" }}>Sessions ({filteredSessions.length})</div>
            {filteredSessions.map(sess => (
              <div key={sess.session_id} onClick={() => selectSession(sess)} style={{ padding: "0.75rem", borderRadius: "8px", marginBottom: "0.4rem", cursor: "pointer", border: `1px solid ${activeSession?.session_id === sess.session_id ? "rgba(99,102,241,0.5)" : "rgba(99,102,241,0.12)"}`, background: activeSession?.session_id === sess.session_id ? "rgba(99,102,241,0.12)" : "rgba(30,41,59,0.4)" }}>
                <div style={{ fontSize: "0.82rem", fontWeight: 600, color: "#e2e8f0", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{sess.title}</div>
                {sess.active_company_name && <div style={{ fontSize: "0.7rem", color: "#34d399", marginTop: "0.2rem" }}>🏢 {sess.active_company_name}</div>}
              </div>
            ))}
          </div>
        </aside>

        {/* Center: Chat Feed & Controls */}
        <main style={{ display: "flex", flexDirection: "column", background: "rgba(10,15,30,0.6)", position: "relative" }}>
          {/* Active Session Header */}
          <div style={{ padding: "0.85rem 1.5rem", borderBottom: "1px solid rgba(99,102,241,0.15)", background: "rgba(15,23,42,0.6)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div>
              <div style={{ fontSize: "0.95rem", fontWeight: 700, color: "#e2e8f0" }}>{activeSession ? activeSession.title : "New Enterprise CRM Session"}</div>
              <div style={{ fontSize: "0.75rem", color: "#64748b" }}>Orchestrator: <span style={{ color: "#a5b4fc" }}>WorkflowEngine & Business Agents</span></div>
            </div>
            {activeSession?.active_company_name && (
              <span style={{ fontSize: "0.75rem", padding: "0.25rem 0.65rem", borderRadius: "100px", background: "rgba(52,211,153,0.12)", color: "#34d399", border: "1px solid rgba(52,211,153,0.3)", fontWeight: 600 }}>🏢 {activeSession.active_company_name}</span>
            )}
          </div>

          {/* Message List */}
          <div style={{ flex: 1, overflowY: "auto", padding: "1.5rem", display: "flex", flexDirection: "column", gap: "1.25rem" }}>
            {messages.length === 0 ? (
              <div style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: "1rem", color: "#64748b", padding: "4rem" }}>
                <div style={{ fontSize: "3rem" }}>💬</div>
                <div style={{ fontSize: "1.2rem", fontWeight: 700, color: "#e2e8f0" }}>Welcome to Enterprise Conversational CRM</div>
                <div style={{ fontSize: "0.85rem", textAlign: "center", maxWidth: "480px", lineHeight: 1.6 }}>
                  Control lead discovery, deep research, predictive lead scoring, cold outreach, and executive reports using natural language.
                </div>
              </div>
            ) : (
              messages.map(msg => (
                <div key={msg.message_id} style={{ display: "flex", flexDirection: "column", alignItems: msg.role === "user" ? "flex-end" : "flex-start" }}>
                  <div style={{ fontSize: "0.72rem", color: "#64748b", marginBottom: "0.25rem", padding: "0 0.5rem" }}>{msg.role === "user" ? "You" : "LeadForgeAI OS"}</div>
                  <div style={{ maxWidth: "85%", padding: "1rem 1.25rem", borderRadius: "12px", background: msg.role === "user" ? "linear-gradient(135deg, #6366f1, #4f46e5)" : "rgba(15,23,42,0.85)", border: msg.role === "user" ? "none" : "1px solid rgba(99,102,241,0.2)", color: "#e2e8f0", fontSize: "0.88rem", lineHeight: 1.6, whiteSpace: "pre-wrap" }}>
                    {msg.content}

                    {/* Action Cards */}
                    {msg.action_cards && msg.action_cards.length > 0 && (
                      <div style={{ marginTop: "1rem", display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "0.75rem", borderTop: "1px solid rgba(99,102,241,0.2)", paddingTop: "0.75rem" }}>
                        {msg.action_cards.map((card, idx) => (
                          <div key={idx} style={{ padding: "0.75rem", borderRadius: "8px", background: "rgba(30,41,59,0.7)", border: "1px solid rgba(99,102,241,0.25)", display: "flex", flexDirection: "column", gap: "0.4rem" }}>
                            <div style={{ fontSize: "0.8rem", fontWeight: 700, color: "#a5b4fc" }}>{card.title}</div>
                            <div style={{ fontSize: "0.72rem", color: "#94a3b8" }}>{card.description}</div>
                            <button onClick={() => handleActionClick(card)} style={{ marginTop: "0.3rem", padding: "0.35rem 0.6rem", borderRadius: "6px", border: "none", background: "linear-gradient(135deg, #6366f1, #8b5cf6)", color: "#fff", fontSize: "0.75rem", fontWeight: 600, cursor: "pointer" }}>
                              {card.button_label}
                            </button>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              ))
            )}
            {stageIndicator && (
              <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", color: "#6366f1", fontSize: "0.8rem", padding: "0.5rem 1rem" }}>
                <span className="pulse">⏳</span> {stageIndicator}
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Slash Menu Popup */}
          {showSlashMenu && (
            <div style={{ position: "absolute", bottom: "80px", left: "1.5rem", background: "rgba(15,23,42,0.95)", border: "1px solid rgba(99,102,241,0.3)", borderRadius: "8px", padding: "0.5rem", display: "flex", flexDirection: "column", gap: "0.25rem", zIndex: 50, backdropFilter: "blur(10px)" }}>
              {SLASH_COMMANDS.map(sc => (
                <div key={sc.cmd} onClick={() => selectSlashCommand(sc.cmd)} style={{ padding: "0.4rem 0.75rem", borderRadius: "6px", cursor: "pointer", display: "flex", gap: "0.75rem", fontSize: "0.8rem" }}>
                  <span style={{ color: "#a5b4fc", fontWeight: 700 }}>{sc.cmd}</span>
                  <span style={{ color: "#64748b" }}>{sc.desc}</span>
                </div>
              ))}
            </div>
          )}

          {/* Input Bar */}
          <div style={{ padding: "1rem 1.5rem", borderTop: "1px solid rgba(99,102,241,0.15)", background: "rgba(15,23,42,0.8)", display: "flex", gap: "0.75rem" }}>
            <input value={companyOverride} onChange={e => setCompanyOverride(e.target.value)} placeholder="Target Company (optional)" style={{ width: "160px", padding: "0.6rem 0.75rem", borderRadius: "8px", border: "1px solid rgba(99,102,241,0.25)", background: "rgba(30,41,59,0.6)", color: "#e2e8f0", fontSize: "0.8rem", outline: "none" }} />
            <input value={inputMsg} onChange={handleInputChange} onKeyDown={e => e.key === "Enter" && handleSend()} placeholder="Type natural language instruction or /slash command…" style={{ flex: 1, padding: "0.6rem 1rem", borderRadius: "8px", border: "1px solid rgba(99,102,241,0.3)", background: "rgba(30,41,59,0.7)", color: "#e2e8f0", fontSize: "0.85rem", outline: "none" }} />
            <button onClick={() => handleSend()} disabled={loading || !inputMsg.trim()} style={{ padding: "0.6rem 1.25rem", borderRadius: "8px", border: "none", background: loading ? "rgba(99,102,241,0.4)" : "linear-gradient(135deg, #6366f1, #8b5cf6)", color: "#fff", fontWeight: 700, fontSize: "0.85rem", cursor: loading ? "not-allowed" : "pointer" }}>
              Send
            </button>
          </div>
        </main>

        {/* Right Sidebar: Execution Visualization */}
        <aside style={{ background: "rgba(15,23,42,0.85)", borderLeft: "1px solid rgba(99,102,241,0.15)", display: "flex", flexDirection: "column", padding: "1.25rem", gap: "1.25rem", overflowY: "auto" }}>
          <div style={{ fontSize: "0.8rem", fontWeight: 700, color: "#6366f1", textTransform: "uppercase", letterSpacing: "0.08em" }}>Live Execution Drawer</div>

          {activeVisualization ? (
            <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
              <div style={{ padding: "0.85rem", borderRadius: "8px", border: "1px solid rgba(99,102,241,0.2)", background: "rgba(30,41,59,0.5)" }}>
                <div style={{ fontSize: "0.72rem", color: "#64748b" }}>Classified Intent</div>
                <div style={{ fontSize: "0.9rem", fontWeight: 700, color: "#e2e8f0" }}>{activeVisualization.intent}</div>
                <div style={{ fontSize: "0.72rem", color: "#34d399", marginTop: "0.25rem" }}>Confidence: {(activeVisualization.confidence * 100).toFixed(0)}%</div>
              </div>

              {activeVisualization.execution_id && (
                <div style={{ padding: "0.85rem", borderRadius: "8px", border: "1px solid rgba(99,102,241,0.2)", background: "rgba(30,41,59,0.5)" }}>
                  <div style={{ fontSize: "0.72rem", color: "#64748b" }}>Workflow Execution ID</div>
                  <div style={{ fontSize: "0.78rem", fontFamily: "monospace", color: "#a5b4fc" }}>{activeVisualization.execution_id}</div>
                  <div style={{ fontSize: "0.75rem", color: "#e2e8f0", marginTop: "0.3rem" }}>Status: {activeVisualization.workflow_status} ({activeVisualization.progress}%)</div>
                </div>
              )}

              {activeVisualization.entities && (
                <div style={{ padding: "0.85rem", borderRadius: "8px", border: "1px solid rgba(99,102,241,0.2)", background: "rgba(30,41,59,0.5)" }}>
                  <div style={{ fontSize: "0.72rem", color: "#64748b", marginBottom: "0.4rem" }}>Extracted Entities</div>
                  <pre style={{ margin: 0, fontSize: "0.7rem", color: "#cbd5e1", background: "rgba(10,15,30,0.6)", padding: "0.5rem", borderRadius: "6px" }}>{JSON.stringify(activeVisualization.entities, null, 2)}</pre>
                </div>
              )}

              <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem", marginTop: "0.5rem" }}>
                <div style={{ fontSize: "0.75rem", color: "#64748b", fontWeight: 700, textTransform: "uppercase" }}>Export Response</div>
                <button style={{ padding: "0.45rem", borderRadius: "6px", border: "1px solid rgba(99,102,241,0.25)", background: "rgba(30,41,59,0.6)", color: "#cbd5e1", fontSize: "0.78rem", cursor: "pointer" }}>📄 Export Markdown</button>
                <button style={{ padding: "0.45rem", borderRadius: "6px", border: "1px solid rgba(99,102,241,0.25)", background: "rgba(30,41,59,0.6)", color: "#cbd5e1", fontSize: "0.78rem", cursor: "pointer" }}>📥 Export JSON</button>
              </div>
            </div>
          ) : (
            <div style={{ color: "#64748b", fontSize: "0.8rem", textAlign: "center", marginTop: "2rem" }}>
              Execute a prompt to inspect intent classification, entity extraction, and Workflow Engine status.
            </div>
          )}
        </aside>
      </div>
    </div>
  );
};

export default ChatPage;
