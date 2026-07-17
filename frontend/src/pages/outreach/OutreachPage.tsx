import React, { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../../contexts/AuthContext";
import axiosClient from "../../api/axiosClient";
import {
  Campaign,
  CampaignDetail,
  CampaignStep,
  EmailAccount,
  EmailTemplate,
  outreachApi,
} from "../../api/outreach";

interface LeadItem {
  id: string;
  name: string;
  website?: string;
  email?: string;
  status: string;
}

export const OutreachPage: React.FC = () => {
  const { logout } = useAuth();

  // Active Tab: campaigns | builder | templates | accounts | analytics
  const [activeTab, setActiveTab] = useState<"campaigns" | "builder" | "templates" | "accounts" | "analytics">("campaigns");

  // State data
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [selectedCampaign, setSelectedCampaign] = useState<CampaignDetail | null>(null);
  const [templates, setTemplates] = useState<EmailTemplate[]>([]);
  const [accounts, setAccounts] = useState<EmailAccount[]>([]);
  const [leads, setLeads] = useState<LeadItem[]>([]);

  // Builder state
  const [campaignName, setCampaignName] = useState("");
  const [selectedAccount, setSelectedAccount] = useState<string>("");
  const [dailyLimit, setDailyLimit] = useState(50);
  const [selectedLeadIds, setSelectedLeadIds] = useState<string[]>([]);
  const [steps, setSteps] = useState<CampaignStep[]>([
    { step_number: 1, delay_days: 0, step_type: "email", subject: "Quick question for {{company}}", body: "<p>Hi {{first_name}},</p><p>Noticed {{company}}'s growth in {{industry}}. We help teams address {{pain_points}}.</p><p>Would you be open to a 5-minute chat?</p>" }
  ]);

  // Account form state
  const [newAccName, setNewAccName] = useState("");
  const [newAccEmail, setNewAccEmail] = useState("");
  const [newAccHost, setNewAccHost] = useState("");
  const [newAccPort, setNewAccPort] = useState(587);
  const [newAccUser, setNewAccUser] = useState("");
  const [newAccPass, setNewAccPass] = useState("");
  const [newAccType, setNewAccType] = useState("smtp");

  // Template form state
  const [newTplName, setNewTplName] = useState("");
  const [newTplSubject, setNewTplSubject] = useState("");
  const [newTplBody, setNewTplBody] = useState("");

  // AI & Feedback state
  const [aiLoading, setAiLoading] = useState(false);
  const [infoMsg, setInfoMsg] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    try {
      const cList = await outreachApi.listCampaigns().catch(() => []);
      const tList = await outreachApi.listTemplates().catch(() => []);
      const aList = await outreachApi.listAccounts().catch(() => []);
      const lRes = await axiosClient.get("/leads?limit=50").catch(() => null);

      const validCampaigns = Array.isArray(cList) ? cList : [];
      const validTemplates = Array.isArray(tList) ? tList : [];
      const validAccounts = Array.isArray(aList) ? aList : [];

      setCampaigns(validCampaigns);
      setTemplates(validTemplates);
      setAccounts(validAccounts);

      const items = lRes?.data?.items;
      if (Array.isArray(items)) {
        setLeads(
          items.map((l: any) => ({
            id: String(l.id || l._id || ""),
            name: l.name || "Unnamed Lead",
            website: l.website || "",
            email: l.email || "",
            status: l.status || "discovered",
          }))
        );
      } else {
        setLeads([]);
      }

      if (validAccounts.length > 0 && !selectedAccount) {
        setSelectedAccount(validAccounts[0].id || "");
      }
    } catch (err) {
      console.error("Failed to load outreach workspace data:", err);
    }
  }, [selectedAccount]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleSelectCampaign = async (cid: string) => {
    try {
      const detail = await outreachApi.getCampaignDetail(cid);
      if (detail && detail.campaign) {
        setSelectedCampaign(detail);
      }
    } catch {
      setErrorMsg("Failed to load campaign details.");
    }
  };

  const handleStatusToggle = async (cid: string, currentStatus: string) => {
    try {
      const nextStatus = currentStatus === "active" ? "paused" : "active";
      await outreachApi.updateCampaignStatus(cid, nextStatus);
      setInfoMsg(`Campaign updated to ${nextStatus.toUpperCase()}`);
      fetchData();
      if (selectedCampaign?.campaign?.id === cid) {
        handleSelectCampaign(cid);
      }
    } catch {
      setErrorMsg("Failed to update campaign status.");
    }
  };

  const handleAddStep = () => {
    setSteps((prev) => [
      ...prev,
      {
        step_number: prev.length + 1,
        delay_days: 3,
        step_type: "follow_up",
        subject: "Re: Quick question for {{company}}",
        body: "<p>Hi {{first_name}}, following up on my previous note. Thought I'd share how similar teams solved key bottlenecks.</p>",
      },
    ]);
  };

  const handleRemoveStep = (idx: number) => {
    setSteps((prev) => prev.filter((_, i) => i !== idx).map((s, i) => ({ ...s, step_number: i + 1 })));
  };

  const handleStepChange = (idx: number, field: keyof CampaignStep, val: any) => {
    setSteps((prev) => {
      const copy = [...prev];
      copy[idx] = { ...copy[idx], [field]: val };
      return copy;
    });
  };

  const insertVariable = (stepIdx: number, varName: string) => {
    const placeholder = `{{${varName}}}`;
    setSteps((prev) => {
      const copy = [...prev];
      copy[stepIdx].body += ` ${placeholder} `;
      return copy;
    });
  };

  const handleAiGenerateStep = async (stepIdx: number, type: "cold_email" | "subject" | "icebreaker") => {
    if (leads.length === 0) {
      setErrorMsg("Please ensure you have leads in your workspace first.");
      return;
    }
    const targetLead = leads[0];
    setAiLoading(true);
    setErrorMsg(null);
    try {
      const res = await outreachApi.generateAiCopy({
        lead_id: targetLead.id,
        generation_type: type,
        step_number: steps[stepIdx].step_number,
      });
      if (type === "subject" && res.subject) {
        handleStepChange(stepIdx, "subject", res.subject);
      } else if (type === "icebreaker" && res.icebreaker) {
        handleStepChange(stepIdx, "body", `<p>${res.icebreaker}</p>` + steps[stepIdx].body);
      } else if (res.body) {
        if (res.subject) handleStepChange(stepIdx, "subject", res.subject);
        handleStepChange(stepIdx, "body", res.body);
      }
      setInfoMsg("AI copy generated successfully using Lead & Intelligence context!");
    } catch {
      setErrorMsg("AI copy generation failed.");
    } finally {
      setAiLoading(false);
    }
  };

  const handleCreateCampaign = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!campaignName.trim()) {
      setErrorMsg("Please enter a campaign name.");
      return;
    }
    try {
      await outreachApi.createCampaign({
        name: campaignName,
        sending_account_id: selectedAccount || undefined,
        daily_limit: dailyLimit,
        steps,
        lead_ids: selectedLeadIds,
      });
      setInfoMsg("Campaign created successfully!");
      setCampaignName("");
      setSelectedLeadIds([]);
      setActiveTab("campaigns");
      fetchData();
    } catch {
      setErrorMsg("Failed to create campaign.");
    }
  };

  const handleCreateAccount = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await outreachApi.createAccount({
        name: newAccName,
        email_address: newAccEmail,
        smtp_host: newAccHost,
        smtp_port: newAccPort,
        smtp_username: newAccUser,
        smtp_password: newAccPass,
        provider_type: newAccType,
        is_default: accounts.length === 0,
      });
      setInfoMsg("Email sending account added successfully.");
      setNewAccName("");
      setNewAccEmail("");
      setNewAccHost("");
      setNewAccUser("");
      setNewAccPass("");
      fetchData();
    } catch {
      setErrorMsg("Failed to create email account.");
    }
  };

  const handleCreateTemplate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await outreachApi.createTemplate({
        name: newTplName,
        subject: newTplSubject,
        body: newTplBody,
      });
      setInfoMsg("Template created successfully.");
      setNewTplName("");
      setNewTplSubject("");
      setNewTplBody("");
      fetchData();
    } catch {
      setErrorMsg("Failed to create template.");
    }
  };

  const toggleLeadSelection = (lid: string) => {
    setSelectedLeadIds((prev) =>
      prev.includes(lid) ? prev.filter((id) => id !== lid) : [...prev, lid]
    );
  };

  return (
    <div className="relative min-h-screen bg-[#030303] text-white font-sans overflow-x-hidden pb-16">
      {/* Background Glows */}
      <div className="absolute top-0 right-1/4 w-[700px] h-[500px] bg-gradient-to-bl from-persian-indigo via-transparent to-transparent opacity-15 rounded-full blur-[140px] pointer-events-none" />
      <div className="absolute bottom-0 left-0 w-[500px] h-[500px] bg-gradient-to-tr from-persian-turquoise via-transparent to-transparent opacity-10 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute inset-0 bg-[linear-gradient(to_right,rgba(255,255,255,0.012)_1px,transparent_1px),linear-gradient(to_bottom,rgba(255,255,255,0.012)_1px,transparent_1px)] bg-[size:45px_45px] pointer-events-none" />

      {/* Navigation Header */}
      <header className="relative z-10 border-b border-glass bg-black/40 backdrop-blur-md px-6 md:px-12 py-4 flex justify-between items-center">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-persian-indigo to-persian-turquoise flex items-center justify-center font-bold text-black font-display text-sm">
            LF
          </div>
          <div>
            <h1 className="text-lg font-display font-extrabold tracking-tight">
              LeadForge<span className="text-persian-turquoise">AI</span>
            </h1>
            <span className="text-[10px] text-neutral-500 font-mono tracking-widest uppercase">Sales Outreach Engine</span>
          </div>
        </div>

        <nav className="flex gap-3 items-center font-mono">
          <Link to="/" className="px-3 py-1.5 border border-glass hover:border-persian-turquoise/40 text-neutral-400 hover:text-white text-xs rounded transition-all">
            ← LEADS
          </Link>
          <Link to="/discovery" className="px-3 py-1.5 border border-glass hover:border-persian-turquoise/40 text-neutral-400 hover:text-white text-xs rounded transition-all">
            🔍 DISCOVERY
          </Link>
          <Link to="/intelligence" className="px-3 py-1.5 border border-glass hover:border-persian-turquoise/40 text-neutral-400 hover:text-white text-xs rounded transition-all">
            🧠 INTELLIGENCE
          </Link>
          <Link to="/scoring" className="px-3 py-1.5 border border-glass hover:border-persian-turquoise/40 text-neutral-400 hover:text-white text-xs rounded transition-all">
            🎯 SCORING
          </Link>
          <Link to="/outreach" className="px-3 py-1.5 border border-persian-turquoise/60 bg-persian-indigo/20 text-persian-turquoise text-xs rounded transition-all font-bold">
            ✉️ OUTREACH
          </Link>
          <button onClick={logout} className="px-3.5 py-1.5 border border-glass hover:border-red-500/40 hover:bg-red-500/10 text-neutral-400 hover:text-red-400 text-xs rounded transition-all">
            DISCONNECT
          </button>
        </nav>
      </header>

      {/* Main Container */}
      <main className="relative z-10 max-w-7xl mx-auto px-6 md:px-10 mt-8 space-y-6">
        {/* Messages */}
        {infoMsg && (
          <div className="p-4 rounded-xl border border-emerald-500/30 bg-emerald-500/10 text-emerald-300 text-xs font-mono flex justify-between items-center">
            <span>ℹ️ {infoMsg}</span>
            <button onClick={() => setInfoMsg(null)} className="text-neutral-400 hover:text-white">✕</button>
          </div>
        )}
        {errorMsg && (
          <div className="p-4 rounded-xl border border-red-500/30 bg-red-500/10 text-red-300 text-xs font-mono flex justify-between items-center">
            <span>⚠️ {errorMsg}</span>
            <button onClick={() => setErrorMsg(null)} className="text-neutral-400 hover:text-white">✕</button>
          </div>
        )}

        {/* Workspace Sub-nav Tabs */}
        <div className="flex flex-wrap gap-2 border border-glass rounded-xl bg-glass backdrop-blur-xl p-2">
          {[
            { id: "campaigns", label: "📋 Campaigns Dashboard" },
            { id: "builder", label: "⚡ Campaign Sequence Builder" },
            { id: "templates", label: "📝 Template Manager" },
            { id: "accounts", label: "⚙️ Email Accounts (SMTP/OAuth)" },
            { id: "analytics", label: "📊 Tracking & Analytics" },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`px-4 py-2 text-xs font-mono rounded-lg transition-all ${
                activeTab === tab.id
                  ? "bg-gradient-to-r from-persian-indigo to-persian-turquoise text-black font-bold shadow-cyan-glow"
                  : "text-neutral-400 hover:text-white hover:bg-glass-hover"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* ── TAB 1: CAMPAIGNS DASHBOARD ── */}
        {activeTab === "campaigns" && (
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <div>
                <h2 className="text-xl font-display font-bold">Active Sales Campaigns</h2>
                <p className="text-xs text-neutral-400 font-mono mt-1">Manage and track automated email sequences</p>
              </div>
              <button
                onClick={() => setActiveTab("builder")}
                className="px-4 py-2.5 bg-gradient-to-r from-persian-indigo to-persian-turquoise text-black font-bold text-xs rounded-xl hover:shadow-cyan-glow transition-all"
              >
                + NEW CAMPAIGN
              </button>
            </div>

            {(campaigns || []).length === 0 ? (
              <div className="border border-glass rounded-xl bg-glass backdrop-blur-xl p-16 text-center space-y-4">
                <div className="text-5xl">✉️</div>
                <h3 className="text-lg font-bold">No Outreach Campaigns Created Yet</h3>
                <p className="text-xs text-neutral-400 max-w-md mx-auto">
                  Click 'New Campaign' to build a multi-step sequence powered by AI personalized copy and automated tracking.
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
                {(campaigns || []).map((c) => (
                  <div key={c.id} className="border border-glass rounded-xl bg-glass backdrop-blur-xl p-5 space-y-4 flex flex-col justify-between">
                    <div>
                      <div className="flex justify-between items-start">
                        <h3 className="font-bold text-base text-white">{c.name || "Untitled Campaign"}</h3>
                        <span className={`px-2.5 py-1 rounded-full text-[10px] font-mono border ${
                          c.status === "active" ? "bg-emerald-500/20 border-emerald-500/50 text-emerald-300" :
                          c.status === "paused" ? "bg-amber-500/20 border-amber-500/50 text-amber-300" :
                          "bg-neutral-800 border-glass text-neutral-400"
                        }`}>
                          {(c.status || "DRAFT").toUpperCase()}
                        </span>
                      </div>
                      <p className="text-[11px] text-neutral-500 font-mono mt-2">
                        Limit: {c.daily_limit ?? 50} emails/day • Created {c.created_at ? new Date(c.created_at).toLocaleDateString() : "Recently"}
                      </p>
                    </div>

                    <div className="pt-3 border-t border-glass/40 flex justify-between items-center gap-2">
                      <button
                        onClick={() => handleSelectCampaign(c.id)}
                        className="px-3 py-1.5 border border-glass hover:border-persian-turquoise/50 text-xs font-mono text-neutral-300 hover:text-white rounded-lg transition-all"
                      >
                        VIEW DETAILS
                      </button>
                      <button
                        onClick={() => handleStatusToggle(c.id, c.status)}
                        className={`px-3 py-1.5 text-xs font-mono rounded-lg transition-all ${
                          c.status === "active"
                            ? "bg-amber-500/10 border border-amber-500/30 text-amber-300 hover:bg-amber-500/20"
                            : "bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 hover:bg-emerald-500/20"
                        }`}
                      >
                        {c.status === "active" ? "PAUSE" : "START"}
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Campaign Detail View */}
            {selectedCampaign && selectedCampaign.campaign && (
              <div className="border border-glass rounded-xl bg-glass backdrop-blur-xl p-6 space-y-6">
                <div className="flex justify-between items-center border-b border-glass pb-4">
                  <div>
                    <h3 className="text-xl font-bold">{selectedCampaign.campaign.name || "Campaign Details"}</h3>
                    <p className="text-xs font-mono text-neutral-400">Enrolled Recipients: {selectedCampaign.recipients_count ?? 0}</p>
                  </div>
                  <button onClick={() => setSelectedCampaign(null)} className="text-neutral-400 hover:text-white text-sm">✕ Close</button>
                </div>

                <div className="grid grid-cols-4 gap-4 text-center font-mono">
                  <div className="border border-glass rounded-lg p-3 bg-black/30">
                    <p className="text-[10px] text-neutral-500">SENT</p>
                    <p className="text-xl font-bold text-white mt-1">{selectedCampaign.analytics?.total_sent ?? 0}</p>
                  </div>
                  <div className="border border-glass rounded-lg p-3 bg-black/30">
                    <p className="text-[10px] text-neutral-500">OPEN RATE</p>
                    <p className="text-xl font-bold text-emerald-400 mt-1">{selectedCampaign.analytics?.open_rate ?? 0}%</p>
                  </div>
                  <div className="border border-glass rounded-lg p-3 bg-black/30">
                    <p className="text-[10px] text-neutral-500">CLICK RATE</p>
                    <p className="text-xl font-bold text-persian-turquoise mt-1">{selectedCampaign.analytics?.click_rate ?? 0}%</p>
                  </div>
                  <div className="border border-glass rounded-lg p-3 bg-black/30">
                    <p className="text-[10px] text-neutral-500">REPLY RATE</p>
                    <p className="text-xl font-bold text-indigo-400 mt-1">{selectedCampaign.analytics?.reply_rate ?? 0}%</p>
                  </div>
                </div>

                <div>
                  <h4 className="text-xs font-mono text-neutral-400 uppercase mb-3">Sequence Steps</h4>
                  <div className="space-y-3">
                    {(selectedCampaign.steps || []).map((s, i) => (
                      <div key={i} className="border border-glass rounded-lg p-4 bg-black/20 space-y-2">
                        <div className="flex justify-between items-center text-xs font-mono">
                          <span className="text-persian-turquoise font-bold">STEP {s.step_number} ({s.step_type.toUpperCase()})</span>
                          <span className="text-neutral-400">Delay: {s.delay_days} days</span>
                        </div>
                        <p className="text-sm font-bold text-white">Subject: {s.subject}</p>
                        <div className="text-xs text-neutral-300 p-3 bg-black/40 rounded border border-glass/40 font-mono overflow-x-auto" dangerouslySetInnerHTML={{ __html: s.body }} />
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* ── TAB 2: CAMPAIGN SEQUENCE BUILDER ── */}
        {activeTab === "builder" && (
          <form onSubmit={handleCreateCampaign} className="space-y-6">
            <div className="border border-glass rounded-xl bg-glass backdrop-blur-xl p-6 space-y-4">
              <h2 className="text-lg font-bold">Campaign Details & Settings</h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="text-[10px] font-mono text-neutral-400 uppercase">Campaign Name</label>
                  <input
                    type="text"
                    required
                    value={campaignName}
                    onChange={(e) => setCampaignName(e.target.value)}
                    placeholder="SaaS Enterprise Q3 Outreach"
                    className="w-full mt-1.5 px-3 py-2 bg-black/40 border border-glass rounded-lg text-xs text-white placeholder-neutral-700 font-mono"
                  />
                </div>
                <div>
                  <label className="text-[10px] font-mono text-neutral-400 uppercase">Sending Email Account</label>
                  <select
                    value={selectedAccount}
                    onChange={(e) => setSelectedAccount(e.target.value)}
                    className="w-full mt-1.5 px-3 py-2 bg-black/40 border border-glass rounded-lg text-xs text-white font-mono"
                  >
                    {accounts.map((a) => (
                      <option key={a.id} value={a.id}>{a.name} ({a.email_address})</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="text-[10px] font-mono text-neutral-400 uppercase">Daily Sending Limit</label>
                  <input
                    type="number"
                    value={dailyLimit}
                    onChange={(e) => setDailyLimit(Number(e.target.value))}
                    className="w-full mt-1.5 px-3 py-2 bg-black/40 border border-glass rounded-lg text-xs text-white font-mono"
                  />
                </div>
              </div>
            </div>

            {/* Step Sequence Builder */}
            <div className="border border-glass rounded-xl bg-glass backdrop-blur-xl p-6 space-y-6">
              <div className="flex justify-between items-center">
                <h2 className="text-lg font-bold">Email Sequence Steps ({steps.length})</h2>
                <button
                  type="button"
                  onClick={handleAddStep}
                  className="px-3 py-1.5 border border-glass hover:border-persian-turquoise/50 text-xs font-mono text-neutral-300 hover:text-white rounded-lg"
                >
                  + ADD FOLLOW-UP STEP
                </button>
              </div>

              <div className="space-y-6">
                {steps.map((step, idx) => (
                  <div key={idx} className="border border-glass rounded-xl p-5 bg-black/30 space-y-4">
                    <div className="flex justify-between items-center">
                      <div className="flex items-center gap-3">
                        <span className="w-6 h-6 rounded-full bg-persian-indigo flex items-center justify-center text-xs font-bold font-mono">
                          {step.step_number}
                        </span>
                        <span className="text-sm font-bold font-mono">
                          {step.step_number === 1 ? "INITIAL COLD EMAIL" : `FOLLOW-UP #${step.step_number - 1}`}
                        </span>
                      </div>
                      {steps.length > 1 && (
                        <button
                          type="button"
                          onClick={() => handleRemoveStep(idx)}
                          className="text-xs text-red-400 hover:text-red-300 font-mono"
                        >
                          REMOVE STEP
                        </button>
                      )}
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="text-[10px] font-mono text-neutral-400 uppercase">Step Delay (Days after previous)</label>
                        <input
                          type="number"
                          value={step.delay_days}
                          onChange={(e) => handleStepChange(idx, "delay_days", Number(e.target.value))}
                          className="w-full mt-1 px-3 py-1.5 bg-black/40 border border-glass rounded text-xs text-white font-mono"
                        />
                      </div>
                      <div>
                        <label className="text-[10px] font-mono text-neutral-400 uppercase">Step Type</label>
                        <select
                          value={step.step_type}
                          onChange={(e) => handleStepChange(idx, "step_type", e.target.value)}
                          className="w-full mt-1 px-3 py-1.5 bg-black/40 border border-glass rounded text-xs text-white font-mono"
                        >
                          <option value="email">Initial Email</option>
                          <option value="follow_up">Follow-up Sequence</option>
                        </select>
                      </div>
                    </div>

                    <div>
                      <div className="flex justify-between items-center mb-1">
                        <label className="text-[10px] font-mono text-neutral-400 uppercase">Subject Line</label>
                        <button
                          type="button"
                          disabled={aiLoading}
                          onClick={() => handleAiGenerateStep(idx, "subject")}
                          className="text-[10px] font-mono text-persian-turquoise hover:underline disabled:opacity-50"
                        >
                          ✨ AI Generate Subject
                        </button>
                      </div>
                      <input
                        type="text"
                        required
                        value={step.subject}
                        onChange={(e) => handleStepChange(idx, "subject", e.target.value)}
                        placeholder="Subject with {{company}} placeholder..."
                        className="w-full px-3 py-2 bg-black/40 border border-glass rounded-lg text-xs text-white font-mono"
                      />
                    </div>

                    <div>
                      <div className="flex justify-between items-center mb-1">
                        <label className="text-[10px] font-mono text-neutral-400 uppercase">Email Body (HTML / Text)</label>
                        <div className="flex gap-2 text-[10px] font-mono">
                          <button
                            type="button"
                            disabled={aiLoading}
                            onClick={() => handleAiGenerateStep(idx, "icebreaker")}
                            className="text-persian-turquoise hover:underline"
                          >
                            ✨ AI Icebreaker
                          </button>
                          <span>•</span>
                          <button
                            type="button"
                            disabled={aiLoading}
                            onClick={() => handleAiGenerateStep(idx, "cold_email")}
                            className="text-persian-turquoise hover:underline"
                          >
                            ✨ AI Full Copy
                          </button>
                        </div>
                      </div>

                      {/* Variables helper toolbar */}
                      <div className="flex flex-wrap gap-1 mb-2">
                        {["first_name", "company", "website", "industry", "pain_points", "buying_signal", "score"].map((v) => (
                          <button
                            key={v}
                            type="button"
                            onClick={() => insertVariable(idx, v)}
                            className="px-2 py-0.5 border border-glass/60 hover:border-persian-turquoise bg-black/40 text-[10px] font-mono text-neutral-300 rounded"
                          >
                            + {`{{${v}}}`}
                          </button>
                        ))}
                      </div>

                      <textarea
                        rows={5}
                        required
                        value={step.body}
                        onChange={(e) => handleStepChange(idx, "body", e.target.value)}
                        className="w-full px-3 py-2 bg-black/40 border border-glass rounded-lg text-xs text-white font-mono leading-relaxed"
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Lead Enrollment Section */}
            <div className="border border-glass rounded-xl bg-glass backdrop-blur-xl p-6 space-y-4">
              <h2 className="text-lg font-bold">Enroll Leads ({selectedLeadIds.length} selected)</h2>
              <div className="max-h-60 overflow-y-auto divide-y divide-glass/30 border border-glass rounded-lg bg-black/20">
                {leads.map((l) => (
                  <div key={l.id} className="p-3 flex justify-between items-center hover:bg-glass-hover">
                    <div>
                      <p className="text-xs font-bold text-white">{l.name}</p>
                      <p className="text-[10px] font-mono text-neutral-400">{l.email || "no email"} • {l.website || "no website"}</p>
                    </div>
                    <input
                      type="checkbox"
                      checked={selectedLeadIds.includes(l.id)}
                      onChange={() => toggleLeadSelection(l.id)}
                      className="w-4 h-4 accent-persian-turquoise cursor-pointer"
                    />
                  </div>
                ))}
              </div>
            </div>

            <button
              type="submit"
              className="w-full py-3 bg-gradient-to-r from-persian-indigo to-persian-turquoise text-black font-bold text-xs rounded-xl hover:shadow-cyan-glow transition-all"
            >
              🚀 CREATE & ENROLL CAMPAIGN
            </button>
          </form>
        )}

        {/* ── TAB 3: TEMPLATES MANAGER ── */}
        {activeTab === "templates" && (
          <div className="space-y-6">
            <div className="border border-glass rounded-xl bg-glass backdrop-blur-xl p-6 space-y-4">
              <h2 className="text-lg font-bold">Create New Email Template</h2>
              <form onSubmit={handleCreateTemplate} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-[10px] font-mono text-neutral-400 uppercase">Template Name</label>
                    <input
                      type="text"
                      required
                      value={newTplName}
                      onChange={(e) => setNewTplName(e.target.value)}
                      placeholder="High-Intent SaaS Pitch"
                      className="w-full mt-1 px-3 py-2 bg-black/40 border border-glass rounded-lg text-xs text-white font-mono"
                    />
                  </div>
                  <div>
                    <label className="text-[10px] font-mono text-neutral-400 uppercase">Subject</label>
                    <input
                      type="text"
                      required
                      value={newTplSubject}
                      onChange={(e) => setNewTplSubject(e.target.value)}
                      placeholder="Quick question regarding {{company}}"
                      className="w-full mt-1 px-3 py-2 bg-black/40 border border-glass rounded-lg text-xs text-white font-mono"
                    />
                  </div>
                </div>
                <div>
                  <label className="text-[10px] font-mono text-neutral-400 uppercase">Body Content</label>
                  <textarea
                    rows={4}
                    required
                    value={newTplBody}
                    onChange={(e) => setNewTplBody(e.target.value)}
                    placeholder="Hi {{first_name}}, noticed {{company}}..."
                    className="w-full mt-1 px-3 py-2 bg-black/40 border border-glass rounded-lg text-xs text-white font-mono"
                  />
                </div>
                <button type="submit" className="px-4 py-2 bg-persian-indigo text-white text-xs font-mono font-bold rounded-lg">
                  SAVE TEMPLATE
                </button>
              </form>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {templates.map((t) => (
                <div key={t.id} className="border border-glass rounded-xl bg-glass backdrop-blur-xl p-5 space-y-2">
                  <div className="flex justify-between items-center">
                    <h3 className="font-bold text-sm">{t.name}</h3>
                    <button
                      onClick={async () => {
                        await outreachApi.deleteTemplate(t.id);
                        fetchData();
                      }}
                      className="text-[10px] text-red-400 font-mono"
                    >
                      DELETE
                    </button>
                  </div>
                  <p className="text-xs font-mono text-persian-turquoise">Subject: {t.subject}</p>
                  <div className="text-xs text-neutral-400 font-mono line-clamp-3 bg-black/30 p-2 rounded">{t.body}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ── TAB 4: EMAIL ACCOUNTS MANAGER ── */}
        {activeTab === "accounts" && (
          <div className="space-y-6">
            <div className="border border-glass rounded-xl bg-glass backdrop-blur-xl p-6 space-y-4">
              <h2 className="text-lg font-bold">Connect Sending Account (SMTP / OAuth)</h2>
              <form onSubmit={handleCreateAccount} className="space-y-4">
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <label className="text-[10px] font-mono text-neutral-400 uppercase">Provider Type</label>
                    <select
                      value={newAccType}
                      onChange={(e) => setNewAccType(e.target.value)}
                      className="w-full mt-1 px-3 py-2 bg-black/40 border border-glass rounded-lg text-xs text-white font-mono"
                    >
                      <option value="smtp">Custom SMTP Server</option>
                      <option value="gmail">Gmail OAuth / App Pass</option>
                      <option value="outlook">Outlook / Office365</option>
                    </select>
                  </div>
                  <div>
                    <label className="text-[10px] font-mono text-neutral-400 uppercase">Account Label</label>
                    <input
                      type="text"
                      required
                      value={newAccName}
                      onChange={(e) => setNewAccName(e.target.value)}
                      placeholder="Primary Outreach Account"
                      className="w-full mt-1 px-3 py-2 bg-black/40 border border-glass rounded-lg text-xs text-white font-mono"
                    />
                  </div>
                  <div>
                    <label className="text-[10px] font-mono text-neutral-400 uppercase">Email Address</label>
                    <input
                      type="email"
                      required
                      value={newAccEmail}
                      onChange={(e) => setNewAccEmail(e.target.value)}
                      placeholder="outreach@company.com"
                      className="w-full mt-1 px-3 py-2 bg-black/40 border border-glass rounded-lg text-xs text-white font-mono"
                    />
                  </div>
                </div>

                {newAccType === "smtp" && (
                  <div className="grid grid-cols-4 gap-4">
                    <div>
                      <label className="text-[10px] font-mono text-neutral-400 uppercase">SMTP Host</label>
                      <input
                        type="text"
                        value={newAccHost}
                        onChange={(e) => setNewAccHost(e.target.value)}
                        placeholder="smtp.mailgun.org"
                        className="w-full mt-1 px-3 py-2 bg-black/40 border border-glass rounded-lg text-xs text-white font-mono"
                      />
                    </div>
                    <div>
                      <label className="text-[10px] font-mono text-neutral-400 uppercase">SMTP Port</label>
                      <input
                        type="number"
                        value={newAccPort}
                        onChange={(e) => setNewAccPort(Number(e.target.value))}
                        className="w-full mt-1 px-3 py-2 bg-black/40 border border-glass rounded-lg text-xs text-white font-mono"
                      />
                    </div>
                    <div>
                      <label className="text-[10px] font-mono text-neutral-400 uppercase">Username</label>
                      <input
                        type="text"
                        value={newAccUser}
                        onChange={(e) => setNewAccUser(e.target.value)}
                        className="w-full mt-1 px-3 py-2 bg-black/40 border border-glass rounded-lg text-xs text-white font-mono"
                      />
                    </div>
                    <div>
                      <label className="text-[10px] font-mono text-neutral-400 uppercase">Password / App Pass</label>
                      <input
                        type="password"
                        value={newAccPass}
                        onChange={(e) => setNewAccPass(e.target.value)}
                        className="w-full mt-1 px-3 py-2 bg-black/40 border border-glass rounded-lg text-xs text-white font-mono"
                      />
                    </div>
                  </div>
                )}

                <button type="submit" className="px-4 py-2 bg-persian-turquoise text-black font-bold text-xs font-mono rounded-lg">
                  CONNECT ACCOUNT
                </button>
              </form>
            </div>

            <div className="space-y-3">
              {accounts.map((a) => (
                <div key={a.id} className="border border-glass rounded-xl bg-glass backdrop-blur-xl p-4 flex justify-between items-center">
                  <div>
                    <h3 className="font-bold text-sm text-white">{a.name}</h3>
                    <p className="text-xs font-mono text-neutral-400">{a.email_address} • Provider: {a.provider_type.toUpperCase()}</p>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={async () => {
                        const email = prompt("Enter test recipient email:");
                        if (email) {
                          try {
                            const res = await outreachApi.testAccount(a.id, email);
                            setInfoMsg(res.message);
                          } catch (err: any) {
                            setErrorMsg(err.response?.data?.detail || "Connection test failed");
                          }
                        }
                      }}
                      className="px-3 py-1.5 border border-glass hover:border-persian-turquoise text-xs font-mono text-persian-turquoise rounded-lg"
                    >
                      TEST CONNECTION
                    </button>
                    <button
                      onClick={async () => {
                        await outreachApi.deleteAccount(a.id);
                        fetchData();
                      }}
                      className="px-3 py-1.5 border border-red-500/30 text-xs font-mono text-red-400 rounded-lg"
                    >
                      DELETE
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ── TAB 5: ANALYTICS & TRACKING ── */}
        {activeTab === "analytics" && (
          <div className="space-y-6">
            <h2 className="text-xl font-bold">Aggregate Campaign Analytics</h2>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="border border-glass rounded-xl p-5 bg-glass backdrop-blur-xl text-center">
                <p className="text-xs font-mono text-neutral-400">CAMPAIGNS</p>
                <p className="text-2xl font-bold text-white mt-1">{(campaigns || []).length}</p>
              </div>
              <div className="border border-glass rounded-xl p-5 bg-glass backdrop-blur-xl text-center">
                <p className="text-xs font-mono text-neutral-400">ACTIVE SEQUENCES</p>
                <p className="text-2xl font-bold text-emerald-400 mt-1">{(campaigns || []).filter(c => c?.status === "active").length}</p>
              </div>
              <div className="border border-glass rounded-xl p-5 bg-glass backdrop-blur-xl text-center">
                <p className="text-xs font-mono text-neutral-400">ACCOUNTS CONNECTED</p>
                <p className="text-2xl font-bold text-persian-turquoise mt-1">{(accounts || []).length}</p>
              </div>
              <div className="border border-glass rounded-xl p-5 bg-glass backdrop-blur-xl text-center">
                <p className="text-xs font-mono text-neutral-400">TEMPLATES READY</p>
                <p className="text-2xl font-bold text-indigo-400 mt-1">{(templates || []).length}</p>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
};

export default OutreachPage;
