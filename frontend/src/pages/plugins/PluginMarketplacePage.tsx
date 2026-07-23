import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../contexts/AuthContext";
import { pluginsApi, PluginItem } from "../../api/plugins";
import { NotificationBell } from "../../components/NotificationBell";

export const PluginMarketplacePage: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const [plugins, setPlugins] = useState<PluginItem[]>([]);

  useEffect(() => {
    fetchPlugins();
  }, []);

  const fetchPlugins = async () => {
    try {
      const data = await pluginsApi.listPlugins();
      setPlugins(data);
    } catch {}
  };

  const handleInstall = async (pluginId: string) => {
    try {
      await pluginsApi.installPlugin(pluginId);
      fetchPlugins();
    } catch {}
  };

  const handleToggle = async (plugin: PluginItem) => {
    try {
      await pluginsApi.togglePlugin(plugin.plugin_id, !plugin.is_enabled);
      setPlugins(prev => prev.map(p => p.plugin_id === plugin.plugin_id ? { ...p, is_enabled: !p.is_enabled } : p));
    } catch {}
  };

  return (
    <div style={{ minHeight: "100vh", background: "#0a0f1e", color: "#e2e8f0", fontFamily: "'Inter', sans-serif", display: "flex", flexDirection: "column" }}>
      {/* Top Header */}
      <nav style={{ background: "rgba(15,23,42,0.95)", borderBottom: "1px solid rgba(99,102,241,0.2)", padding: "0 2rem", height: "60px", display: "flex", alignItems: "center", justifyContent: "space-between", backdropFilter: "blur(12px)", position: "sticky", top: 0, zIndex: 100 }}>
        <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
          <div style={{ fontSize: "1.4rem", fontWeight: 800, background: "linear-gradient(135deg, #6366f1, #8b5cf6)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
            LeadForgeAI
          </div>
          <div style={{ color: "#64748b", fontSize: "0.85rem" }}>/ Plugin SDK Marketplace</div>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
          <NotificationBell />
          <button onClick={() => navigate("/scheduler")} style={{ background: "none", border: "1px solid rgba(99,102,241,0.3)", color: "#a5b4fc", padding: "0.4rem 1rem", borderRadius: "6px", cursor: "pointer", fontSize: "0.85rem" }}>⏱️ Scheduler</button>
          <button onClick={() => navigate("/chat")} style={{ background: "none", border: "1px solid rgba(99,102,241,0.3)", color: "#94a3b8", padding: "0.4rem 1rem", borderRadius: "6px", cursor: "pointer", fontSize: "0.85rem" }}>💬 Chat CRM</button>
          <span style={{ color: "#64748b", fontSize: "0.85rem" }}>{user?.email}</span>
          <button onClick={logout} style={{ background: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.3)", color: "#f87171", padding: "0.4rem 1rem", borderRadius: "6px", cursor: "pointer", fontSize: "0.85rem" }}>Logout</button>
        </div>
      </nav>

      {/* Plugins Grid */}
      <div style={{ flex: 1, padding: "2rem", display: "flex", flexDirection: "column", gap: "1.5rem" }}>
        <div>
          <div style={{ fontSize: "1.2rem", fontWeight: 700, color: "#e2e8f0" }}>Enterprise Plugin SDK Catalog</div>
          <div style={{ fontSize: "0.85rem", color: "#64748b", marginTop: "0.25rem" }}>
            Extend BaseTool capabilities with native CRM, communication, and webhook integrations.
          </div>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: "1.25rem" }}>
          {plugins.map(p => (
            <div key={p.plugin_id} style={{ padding: "1.5rem", borderRadius: "12px", border: "1px solid rgba(99,102,241,0.2)", background: "rgba(15,23,42,0.8)", display: "flex", flexDirection: "column", justifyContent: "space-between", gap: "1rem" }}>
              <div>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <div style={{ fontSize: "1.05rem", fontWeight: 700, color: "#a5b4fc" }}>{p.name}</div>
                  <span style={{ fontSize: "0.7rem", padding: "0.2rem 0.5rem", borderRadius: "100px", background: "rgba(99,102,241,0.15)", color: "#6366f1", fontWeight: 600 }}>{p.category.toUpperCase()}</span>
                </div>
                <div style={{ fontSize: "0.8rem", color: "#94a3b8", marginTop: "0.5rem", lineHeight: 1.5 }}>{p.description}</div>
                <div style={{ fontSize: "0.72rem", color: "#64748b", marginTop: "0.5rem" }}>SDK Version: {p.version}</div>
              </div>

              <div style={{ borderTop: "1px solid rgba(99,102,241,0.15)", paddingTop: "0.75rem", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                {p.is_installed ? (
                  <>
                    <span style={{ fontSize: "0.75rem", color: "#34d399", fontWeight: 600 }}>Installed ✅</span>
                    <button onClick={() => handleToggle(p)} style={{ padding: "0.4rem 0.85rem", borderRadius: "6px", border: "none", background: p.is_enabled ? "rgba(239,68,68,0.15)" : "rgba(16,185,129,0.15)", color: p.is_enabled ? "#f87171" : "#34d399", fontWeight: 700, fontSize: "0.78rem", cursor: "pointer" }}>
                      {p.is_enabled ? "Disable" : "Enable"}
                    </button>
                  </>
                ) : (
                  <button onClick={() => handleInstall(p.plugin_id)} style={{ width: "100%", padding: "0.5rem", borderRadius: "6px", border: "none", background: "linear-gradient(135deg, #6366f1, #8b5cf6)", color: "#fff", fontWeight: 700, fontSize: "0.8rem", cursor: "pointer" }}>
                    Install Plugin
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default PluginMarketplacePage;
