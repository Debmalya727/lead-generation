import React, { useEffect, useState } from "react";
import { aiApi } from "../../api/ai";
import { NotificationBell } from "../../components/NotificationBell";

export const EmailWorkspace: React.FC = () => {
  const [analytics, setAnalytics] = useState<any>(null);
  const [webhookEvents, setWebhookEvents] = useState<any[]>([]);

  // Send Single Email State
  const [toEmail, setToEmail] = useState<string>("lead.target@acme.com");
  const [emailSubject, setEmailSubject] = useState<string>("Exclusive LeadForgeAI Demo Invitation for {{company}}");
  const [emailHtml, setEmailHtml] = useState<string>("<p>Hi {{first_name}},</p><p>We saw your work at {{company}} and wanted to share our AI Gateway platform.</p><a href='https://leadforgeai.com/demo'>Schedule Demo</a>");
  const [sending, setSending] = useState<boolean>(false);

  // Template Studio State
  const [templateMjml, setTemplateMjml] = useState<string>("<mjml><mj-body><mj-section><mj-text>Hello {{first_name}} from {{company}}!</mj-text><mj-button href='https://leadforgeai.com'>Claim Offer</mj-button></mj-section></mj-body></mj-html>");
  const [compiledHtml, setCompiledHtml] = useState<string>("");
  const [compiling, setCompiling] = useState<boolean>(false);

  const fetchEmailData = async () => {
    try {
      const [analyticsData, webhooksData] = await Promise.all([
        aiApi.getEmailAnalytics(),
        aiApi.getEmailWebhookEvents(50),
      ]);
      setAnalytics(analyticsData);
      setWebhookEvents(webhooksData);
    } catch (err: any) {
      console.error("Failed to fetch email platform data:", err);
    }
  };

  useEffect(() => {
    fetchEmailData();
    const interval = setInterval(fetchEmailData, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleSendEmail = async () => {
    if (!toEmail.trim() || !emailSubject.trim()) return;
    setSending(true);
    try {
      await aiApi.sendEmail({
        to_email: toEmail,
        subject: emailSubject,
        html_content: emailHtml,
        variables: { first_name: "Alex", company: "Acme Corp" },
      });
      alert(`Email successfully dispatched via Resend to ${toEmail}!`);
      await fetchEmailData();
    } catch (err: any) {
      alert(`Email dispatch failed: ${err.message}`);
    } finally {
      setSending(false);
    }
  };

  const handleCompileMjml = async () => {
    setCompiling(true);
    try {
      const res = await aiApi.compileEmailTemplate({
        template_str: templateMjml,
        variables: { first_name: "Sarah", company: "ZettaWeb" },
        is_mjml: true,
      });
      setCompiledHtml(res.compiled_html);
    } catch (err: any) {
      alert(`MJML compilation failed: ${err.message}`);
    } finally {
      setCompiling(false);
    }
  };

  return (
    <div style={{ padding: "2rem", color: "#f8fafc", fontFamily: "Inter, sans-serif" }}>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "2rem" }}>
        <div>
          <h1 style={{ fontSize: "1.875rem", fontWeight: 700, margin: 0, color: "#fff" }}>
            ✉️ Resend Enterprise Email & Outreach Platform
          </h1>
          <p style={{ color: "#94a3b8", fontSize: "0.9rem", marginTop: "0.25rem" }}>
            MJML/HTML Templates, Open/Click Tracking, Resend Webhooks & Auto Bounce Suppression
          </p>
        </div>
        <NotificationBell />
      </div>

      {/* Analytics Banner */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "1rem", marginBottom: "2rem" }}>
        <div style={{ background: "#1e293b", padding: "1.25rem", borderRadius: "10px", border: "1px solid #334155" }}>
          <span style={{ color: "#94a3b8", fontSize: "0.8rem", textTransform: "uppercase" }}>Total Dispatched</span>
          <div style={{ fontSize: "2rem", fontWeight: 700, color: "#38bdf8", marginTop: "0.25rem" }}>
            {analytics ? analytics.total_sent.toLocaleString() : "..."}
          </div>
          <span style={{ fontSize: "0.75rem", color: "#64748b" }}>Delivered: {analytics?.total_delivered}</span>
        </div>

        <div style={{ background: "#1e293b", padding: "1.25rem", borderRadius: "10px", border: "1px solid #334155" }}>
          <span style={{ color: "#94a3b8", fontSize: "0.8rem", textTransform: "uppercase" }}>Delivery Rate</span>
          <div style={{ fontSize: "2rem", fontWeight: 700, color: "#10b981", marginTop: "0.25rem" }}>
            {analytics ? `${analytics.delivery_rate_percent}%` : "..."}
          </div>
          <span style={{ fontSize: "0.75rem", color: "#64748b" }}>Bounced: {analytics?.total_bounced}</span>
        </div>

        <div style={{ background: "#1e293b", padding: "1.25rem", borderRadius: "10px", border: "1px solid #334155" }}>
          <span style={{ color: "#94a3b8", fontSize: "0.8rem", textTransform: "uppercase" }}>Open Rate</span>
          <div style={{ fontSize: "2rem", fontWeight: 700, color: "#a855f7", marginTop: "0.25rem" }}>
            {analytics ? `${analytics.open_rate_percent}%` : "..."}
          </div>
          <span style={{ fontSize: "0.75rem", color: "#64748b" }}>Opened: {analytics?.total_opened}</span>
        </div>

        <div style={{ background: "#1e293b", padding: "1.25rem", borderRadius: "10px", border: "1px solid #334155" }}>
          <span style={{ color: "#94a3b8", fontSize: "0.8rem", textTransform: "uppercase" }}>Click-Through Rate (CTR)</span>
          <div style={{ fontSize: "2rem", fontWeight: 700, color: "#f59e0b", marginTop: "0.25rem" }}>
            {analytics ? `${analytics.click_through_rate_percent}%` : "..."}
          </div>
          <span style={{ fontSize: "0.75rem", color: "#64748b" }}>Clicked: {analytics?.total_clicked}</span>
        </div>
      </div>

      {/* Main Grid: Send Email & Template Compiler */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.5rem", marginBottom: "2rem" }}>
        {/* Transactional Email Dispatcher */}
        <div style={{ background: "#1e293b", padding: "1.5rem", borderRadius: "10px", border: "1px solid #334155" }}>
          <h3 style={{ margin: "0 0 1rem 0", color: "#f1f5f9" }}>📤 Resend Email Dispatcher</h3>
          <div style={{ marginBottom: "0.75rem" }}>
            <label style={{ display: "block", color: "#94a3b8", fontSize: "0.8rem", marginBottom: "0.25rem" }}>Recipient Email</label>
            <input
              type="email"
              value={toEmail}
              onChange={(e) => setToEmail(e.target.value)}
              style={{ width: "100%", padding: "0.5rem", background: "#0f172a", border: "1px solid #334155", borderRadius: "6px", color: "#fff" }}
            />
          </div>

          <div style={{ marginBottom: "0.75rem" }}>
            <label style={{ display: "block", color: "#94a3b8", fontSize: "0.8rem", marginBottom: "0.25rem" }}>Subject Line</label>
            <input
              type="text"
              value={emailSubject}
              onChange={(e) => setEmailSubject(e.target.value)}
              style={{ width: "100%", padding: "0.5rem", background: "#0f172a", border: "1px solid #334155", borderRadius: "6px", color: "#fff" }}
            />
          </div>

          <div style={{ marginBottom: "1rem" }}>
            <label style={{ display: "block", color: "#94a3b8", fontSize: "0.8rem", marginBottom: "0.25rem" }}>HTML Body (Supports mustache variable tags)</label>
            <textarea
              rows={5}
              value={emailHtml}
              onChange={(e) => setEmailHtml(e.target.value)}
              style={{ width: "100%", padding: "0.5rem", background: "#0f172a", border: "1px solid #334155", borderRadius: "6px", color: "#fff", fontSize: "0.85rem" }}
            />
          </div>

          <button
            onClick={handleSendEmail}
            disabled={sending}
            style={{ width: "100%", padding: "0.75rem", background: "#4f46e5", color: "#fff", border: "none", borderRadius: "6px", fontWeight: 700, cursor: "pointer" }}
          >
            {sending ? "Sending via Resend..." : "🚀 Send Email via Resend"}
          </button>
        </div>

        {/* MJML Template Studio */}
        <div style={{ background: "#1e293b", padding: "1.5rem", borderRadius: "10px", border: "1px solid #334155" }}>
          <h3 style={{ margin: "0 0 1rem 0", color: "#f1f5f9" }}>🎨 MJML Template Compiler & Studio</h3>
          <div style={{ marginBottom: "1rem" }}>
            <label style={{ display: "block", color: "#94a3b8", fontSize: "0.8rem", marginBottom: "0.25rem" }}>MJML Responsive Source Code</label>
            <textarea
              rows={5}
              value={templateMjml}
              onChange={(e) => setTemplateMjml(e.target.value)}
              style={{ width: "100%", padding: "0.5rem", background: "#0f172a", border: "1px solid #334155", borderRadius: "6px", color: "#fff", fontSize: "0.85rem", fontFamily: "monospace" }}
            />
          </div>

          <button
            onClick={handleCompileMjml}
            disabled={compiling}
            style={{ width: "100%", padding: "0.6rem", background: "#10b981", color: "#fff", border: "none", borderRadius: "6px", fontWeight: 700, cursor: "pointer", marginBottom: "1rem" }}
          >
            {compiling ? "Compiling..." : "⚡ Compile MJML to HTML"}
          </button>

          {compiledHtml && (
            <div style={{ padding: "0.75rem", background: "#0f172a", borderRadius: "6px", border: "1px solid #334155", maxHeight: "140px", overflowY: "auto" }}>
              <div style={{ fontSize: "0.75rem", color: "#94a3b8", marginBottom: "0.25rem" }}>Compiled Responsive HTML Preview:</div>
              <div style={{ color: "#38bdf8", fontSize: "0.8rem", fontFamily: "monospace" }}>{compiledHtml}</div>
            </div>
          )}
        </div>
      </div>

      {/* Resend Webhooks Event Stream */}
      <div style={{ background: "#1e293b", padding: "1.5rem", borderRadius: "10px", border: "1px solid #334155" }}>
        <h3 style={{ margin: "0 0 1rem 0", color: "#f1f5f9" }}>📡 Resend Webhook Event Stream</h3>
        <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left", fontSize: "0.85rem" }}>
          <thead>
            <tr style={{ borderBottom: "1px solid #334155", color: "#94a3b8" }}>
              <th style={{ padding: "0.75rem" }}>Timestamp</th>
              <th style={{ padding: "0.75rem" }}>Event Type</th>
              <th style={{ padding: "0.75rem" }}>Resend Email ID</th>
              <th style={{ padding: "0.75rem" }}>Recipient Email</th>
            </tr>
          </thead>
          <tbody>
            {webhookEvents.slice(0, 10).map((evt, idx) => (
              <tr key={idx} style={{ borderBottom: "1px solid #0f172a" }}>
                <td style={{ padding: "0.75rem", color: "#64748b" }}>{new Date(evt.timestamp).toLocaleTimeString()}</td>
                <td style={{ padding: "0.75rem" }}>
                  <span style={{ padding: "0.2rem 0.5rem", borderRadius: "4px", fontSize: "0.75rem", fontWeight: 700, background: evt.event_type.includes("bounced") ? "rgba(239,68,68,0.1)" : "rgba(74,222,128,0.1)", color: evt.event_type.includes("bounced") ? "#ef4444" : "#4ade80" }}>
                    {evt.event_type}
                  </span>
                </td>
                <td style={{ padding: "0.75rem", color: "#38bdf8", fontFamily: "monospace" }}>{evt.resend_email_id}</td>
                <td style={{ padding: "0.75rem", color: "#fff" }}>{evt.recipient_email}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default EmailWorkspace;
