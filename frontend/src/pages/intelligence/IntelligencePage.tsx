import React, { useCallback, useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../../contexts/AuthContext";
import axiosClient from "../../api/axiosClient";
import {
  IntelligenceResponse,
  IntelligenceStatusResponse,
  TechStackItem,
  intelligenceApi,
} from "../../api/intelligence";

// ────────────────────────────────────────────────────────────
// Sub-components
// ────────────────────────────────────────────────────────────

const ConfidenceMeter: React.FC<{ score: number }> = ({ score }) => {
  const pct = Math.min(100, Math.max(0, score));
  const color =
    pct >= 70 ? "from-emerald-500 to-teal-400" :
    pct >= 40 ? "from-amber-500 to-yellow-400" :
    "from-red-500 to-rose-400";

  return (
    <div className="space-y-2">
      <div className="flex justify-between items-center text-[10px] font-mono text-neutral-400">
        <span>CONFIDENCE SCORE</span>
        <span className="text-white font-bold text-sm">{pct}/100</span>
      </div>
      <div className="w-full h-3 bg-black/50 rounded-full border border-glass overflow-hidden p-0.5">
        <div
          style={{ width: `${pct}%` }}
          className={`h-full bg-gradient-to-r ${color} rounded-full transition-all duration-700 ease-out`}
        />
      </div>
      <p className="text-[10px] text-neutral-500 font-mono">
        {pct >= 70 ? "HIGH — Strong intelligence extracted" :
         pct >= 40 ? "MEDIUM — Partial data available" :
         "LOW — Limited data, consider re-analyzing"}
      </p>
    </div>
  );
};

const TagBadge: React.FC<{ label: string; variant?: "amber" | "emerald" | "blue" | "neutral" }> = ({
  label,
  variant = "neutral",
}) => {
  const styles = {
    amber: "bg-amber-500/10 border-amber-500/30 text-amber-300",
    emerald: "bg-emerald-500/10 border-emerald-500/30 text-emerald-300",
    blue: "bg-persian-indigo/10 border-persian-indigo/30 text-persian-300",
    neutral: "bg-glass border-glass text-neutral-300",
  };
  return (
    <span className={`inline-flex items-center px-2.5 py-1 rounded-full border text-[11px] font-mono ${styles[variant]}`}>
      {label}
    </span>
  );
};

const TECH_CATEGORY_COLORS: Record<string, string> = {
  CMS: "bg-violet-500/15 border-violet-500/30 text-violet-300",
  Analytics: "bg-blue-500/15 border-blue-500/30 text-blue-300",
  Framework: "bg-cyan-500/15 border-cyan-500/30 text-cyan-300",
  "UI Library": "bg-pink-500/15 border-pink-500/30 text-pink-300",
  CDN: "bg-orange-500/15 border-orange-500/30 text-orange-300",
  Hosting: "bg-emerald-500/15 border-emerald-500/30 text-emerald-300",
  Payments: "bg-amber-500/15 border-amber-500/30 text-amber-300",
  "E-commerce": "bg-red-500/15 border-red-500/30 text-red-300",
  "CRM/Support": "bg-teal-500/15 border-teal-500/30 text-teal-300",
  "CRM/Marketing": "bg-lime-500/15 border-lime-500/30 text-lime-300",
  CRM: "bg-indigo-500/15 border-indigo-500/30 text-indigo-300",
};

const TechBadge: React.FC<{ item: TechStackItem }> = ({ item }) => {
  const cls = TECH_CATEGORY_COLORS[item.category] || "bg-glass border-glass text-neutral-300";
  return (
    <span className={`inline-flex flex-col items-center px-3 py-1.5 rounded-lg border text-center ${cls}`}>
      <span className="text-[11px] font-semibold font-mono">{item.name}</span>
      <span className="text-[9px] opacity-60 uppercase tracking-wider mt-0.5">{item.category}</span>
    </span>
  );
};

const SOCIAL_ICONS: Record<string, string> = {
  linkedin: "💼",
  twitter: "🐦",
  facebook: "📘",
  instagram: "📷",
  youtube: "▶️",
  github: "⚙️",
};

// ────────────────────────────────────────────────────────────
// Lead Selector types
// ────────────────────────────────────────────────────────────
interface LeadItem {
  id: string;
  name: string;
  website?: string;
  status: string;
}

// ────────────────────────────────────────────────────────────
// Main Page
// ────────────────────────────────────────────────────────────
export const IntelligencePage: React.FC = () => {
  const { logout } = useAuth();

  // Leads data
  const [leads, setLeads] = useState<LeadItem[]>([]);
  const [leadsSearch, setLeadsSearch] = useState("");
  const [selectedLead, setSelectedLead] = useState<LeadItem | null>(null);

  // Analysis job state
  const [activeJob, setActiveJob] = useState<IntelligenceStatusResponse | null>(null);
  const [report, setReport] = useState<IntelligenceResponse | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"summary" | "products" | "sales" | "tech" | "links">("summary");

  const pollingRef = useRef<NodeJS.Timeout | null>(null);

  // Fetch lead list on mount and on search change
  const fetchLeads = useCallback(async (search: string) => {
    try {
      const res = await axiosClient.get("/leads", {
        params: { search: search || undefined, limit: 50 },
      });
      setLeads(
        (res.data.items || []).map((l: any) => ({
          id: String(l.id),
          name: l.name,
          website: l.website,
          status: l.status,
        }))
      );
    } catch {
      // silent
    }
  }, []);

  useEffect(() => {
    fetchLeads(leadsSearch);
  }, [leadsSearch, fetchLeads]);

  // Check if there's already an existing report when selecting a lead
  const handleSelectLead = async (lead: LeadItem) => {
    stopPolling();
    setSelectedLead(lead);
    setActiveJob(null);
    setReport(null);
    setError(null);
    setActiveTab("summary");

    try {
      const existing = await intelligenceApi.getByLead(lead.id);
      if (existing.status === "completed") {
        setReport(existing);
      } else if (existing.status === "running" || existing.status === "pending") {
        setActiveJob(existing);
        setAnalyzing(true);
        startPolling(existing.id);
      }
    } catch {
      // No existing report — that's fine
    }
  };

  const handleStartAnalysis = async () => {
    if (!selectedLead) return;
    if (!selectedLead.website) {
      setError("This lead has no website URL. Edit the lead and add a website first.");
      return;
    }

    setError(null);
    setReport(null);
    setAnalyzing(true);
    setActiveTab("summary");

    try {
      const job = await intelligenceApi.startAnalysis(selectedLead.id);
      setActiveJob(job);
      startPolling(job.id);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to start analysis.");
      setAnalyzing(false);
    }
  };

  const startPolling = (jobId: string) => {
    stopPolling();
    pollingRef.current = setInterval(async () => {
      try {
        const status = await intelligenceApi.pollJob(jobId);
        setActiveJob(status);

        if (status.status === "completed") {
          stopPolling();
          setAnalyzing(false);
          // Fetch the full report now
          if (selectedLead) {
            const full = await intelligenceApi.getByLead(selectedLead.id);
            setReport(full);
          }
        } else if (status.status === "failed") {
          stopPolling();
          setAnalyzing(false);
          setError(status.error_message || "Analysis failed.");
        }
      } catch {
        // network blip — keep polling
      }
    }, 1800);
  };

  const stopPolling = () => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
      pollingRef.current = null;
    }
  };

  useEffect(() => () => stopPolling(), []);

  const handleDelete = async () => {
    if (!selectedLead) return;
    try {
      await intelligenceApi.deleteIntelligence(selectedLead.id);
      setReport(null);
      setActiveJob(null);
      setError(null);
    } catch {
      alert("Could not delete the report.");
    }
  };

  const filteredLeads = leads.filter(
    (l) =>
      leadsSearch === "" ||
      l.name.toLowerCase().includes(leadsSearch.toLowerCase())
  );

  const progress = activeJob?.progress ?? 0;

  return (
    <div className="relative min-h-screen bg-[#030303] text-white font-sans overflow-x-hidden pb-16">
      {/* Background glows */}
      <div className="absolute top-0 left-1/4 w-[700px] h-[500px] bg-gradient-to-br from-persian-indigo via-transparent to-transparent opacity-15 rounded-full blur-[140px] pointer-events-none" />
      <div className="absolute bottom-0 right-0 w-[500px] h-[500px] bg-gradient-to-tl from-persian-turquoise via-transparent to-transparent opacity-10 rounded-full blur-[120px] pointer-events-none" />
      {/* Grid texture */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,rgba(255,255,255,0.012)_1px,transparent_1px),linear-gradient(to_bottom,rgba(255,255,255,0.012)_1px,transparent_1px)] bg-[size:45px_45px] pointer-events-none" />

      {/* ── Header ── */}
      <header className="relative z-10 border-b border-glass bg-black/40 backdrop-blur-md px-6 md:px-12 py-4 flex justify-between items-center">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-persian-indigo to-persian-turquoise flex items-center justify-center font-bold text-black font-display text-sm">
            LF
          </div>
          <div>
            <h1 className="text-lg font-display font-extrabold tracking-tight">
              LeadForge<span className="text-persian-turquoise">AI</span>
            </h1>
            <span className="text-[10px] text-neutral-500 font-mono tracking-widest uppercase">Intelligence Engine</span>
          </div>
        </div>
        <nav className="flex gap-3 items-center">
          <Link to="/" className="px-3 py-1.5 border border-glass hover:border-persian-turquoise/40 text-neutral-400 hover:text-white font-mono text-xs rounded transition-all">
            ← LEADS
          </Link>
          <Link to="/discovery" className="px-3 py-1.5 border border-glass hover:border-persian-turquoise/40 text-neutral-400 hover:text-white font-mono text-xs rounded transition-all">
            🔍 DISCOVERY
          </Link>
          <Link to="/scoring" className="px-3 py-1.5 border border-glass hover:border-persian-turquoise/40 text-neutral-400 hover:text-white font-mono text-xs rounded transition-all">
            🎯 SCORING
          </Link>
          <Link to="/outreach" className="px-3 py-1.5 border border-glass hover:border-persian-turquoise/40 text-neutral-400 hover:text-white font-mono text-xs rounded transition-all">
            ✉️ OUTREACH
          </Link>
          <button onClick={logout} className="px-3 py-1.5 border border-glass hover:border-red-500/40 hover:bg-red-500/10 text-neutral-400 hover:text-red-400 font-mono text-xs rounded transition-all">
            DISCONNECT
          </button>
        </nav>
      </header>

      {/* ── Main layout ── */}
      <main className="relative z-10 max-w-7xl mx-auto px-6 md:px-10 mt-8 grid grid-cols-1 lg:grid-cols-[280px_1fr] gap-6">
        {/* ── Left: Lead Selector Panel ── */}
        <aside className="space-y-4">
          <div>
            <h2 className="text-xl font-display font-extrabold tracking-tight">Company Intelligence</h2>
            <p className="text-[11px] text-neutral-500 mt-1 font-mono">
              AI-powered website analysis engine
            </p>
          </div>

          <div className="border border-glass rounded-xl bg-glass backdrop-blur-xl overflow-hidden">
            <div className="p-4 border-b border-glass/50">
              <p className="text-[10px] font-mono text-neutral-400 uppercase tracking-wider mb-2">Select Lead</p>
              <input
                type="text"
                value={leadsSearch}
                onChange={(e) => setLeadsSearch(e.target.value)}
                placeholder="Search leads..."
                className="w-full px-3 py-2 bg-black/40 border border-glass rounded-lg text-xs text-white placeholder-neutral-700 focus:outline-none focus:border-persian-turquoise transition-all font-mono"
              />
            </div>

            <div className="max-h-[400px] overflow-y-auto divide-y divide-glass/30">
              {filteredLeads.length === 0 ? (
                <div className="p-4 text-center text-neutral-600 text-xs font-mono">NO LEADS FOUND</div>
              ) : (
                filteredLeads.map((lead) => (
                  <button
                    key={lead.id}
                    onClick={() => handleSelectLead(lead)}
                    className={`w-full text-left px-4 py-3 transition-all hover:bg-glass-hover/20 ${
                      selectedLead?.id === lead.id ? "bg-persian-indigo/10 border-l-2 border-persian-turquoise" : ""
                    }`}
                  >
                    <div className="text-sm text-white font-medium truncate">{lead.name}</div>
                    {lead.website ? (
                      <div className="text-[10px] text-persian-turquoise/70 font-mono truncate mt-0.5">
                        {lead.website.replace(/(^\w+:|^)\/\//, "")}
                      </div>
                    ) : (
                      <div className="text-[10px] text-neutral-600 font-mono mt-0.5">no website</div>
                    )}
                  </button>
                ))
              )}
            </div>
          </div>

          {/* Analyze button */}
          {selectedLead && (
            <button
              onClick={handleStartAnalysis}
              disabled={analyzing}
              className="w-full py-3 bg-gradient-to-r from-persian-indigo to-persian-turquoise hover:from-persian-turquoise hover:to-persian-indigo text-black font-bold text-xs rounded-xl transition-all active:scale-[0.98] duration-300 disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {analyzing ? (
                <>
                  <span className="w-3 h-3 border-2 border-black/40 border-t-black rounded-full animate-spin" />
                  ANALYZING...
                </>
              ) : report ? "🔄 RE-ANALYZE" : "🧠 START ANALYSIS"}
            </button>
          )}

          {report && (
            <button
              onClick={handleDelete}
              className="w-full py-2 border border-red-500/20 hover:border-red-500/50 hover:bg-red-500/10 text-red-500/70 hover:text-red-400 font-mono text-[10px] rounded-xl transition-all"
            >
              DELETE REPORT
            </button>
          )}
        </aside>

        {/* ── Right: Report Panel ── */}
        <section className="space-y-5 min-h-[600px]">

          {/* Error banner */}
          {error && (
            <div className="p-4 rounded-xl border border-red-500/20 bg-red-500/10 text-red-400 text-xs font-mono">
              ⚠️ {error}
            </div>
          )}

          {/* Progress card */}
          {activeJob && analyzing && (
            <div className="border border-glass rounded-xl bg-glass backdrop-blur-xl p-6 space-y-4">
              <div className="flex justify-between items-center text-xs font-mono">
                <div>
                  STATUS:{" "}
                  <span className="font-bold text-persian-turquoise animate-pulse">
                    {activeJob.status.toUpperCase()}
                  </span>
                </div>
                <div>PROGRESS: <span className="font-bold text-white">{progress}%</span></div>
              </div>

              <div className="w-full bg-black/50 border border-glass h-3 rounded-full overflow-hidden p-0.5">
                <div
                  style={{ width: `${progress}%` }}
                  className="h-full bg-gradient-to-r from-persian-indigo to-persian-turquoise rounded-full transition-all duration-700 ease-out"
                />
              </div>

              <div className="grid grid-cols-4 gap-2 text-[9px] font-mono text-neutral-600">
                {[
                  { label: "INITIALIZE", pct: 10 },
                  { label: "CRAWL SITE", pct: 25 },
                  { label: "PROCESS", pct: 50 },
                  { label: "AI EXTRACT", pct: 75 },
                ].map((stage) => (
                  <div
                    key={stage.label}
                    className={`flex flex-col items-center gap-1 ${
                      progress >= stage.pct ? "text-persian-turquoise" : ""
                    }`}
                  >
                    <div className={`w-2 h-2 rounded-full ${progress >= stage.pct ? "bg-persian-turquoise" : "bg-neutral-800 border border-glass"}`} />
                    {stage.label}
                  </div>
                ))}
              </div>

              <p className="text-[10px] text-neutral-600 font-mono text-center">
                Analyzing <span className="text-white">{activeJob.company_name}</span> — this takes 15-30 seconds
              </p>
            </div>
          )}

          {/* Empty state */}
          {!selectedLead && !activeJob && !report && (
            <div className="border border-glass rounded-xl bg-glass backdrop-blur-xl p-16 text-center space-y-4">
              <div className="text-5xl">🧠</div>
              <h3 className="text-xl font-display font-bold">Company Intelligence</h3>
              <p className="text-sm text-neutral-400 max-w-sm mx-auto">
                Select a lead from the sidebar to start AI-powered website analysis. We'll extract executive summaries, pain points, buying signals, and more.
              </p>
            </div>
          )}

          {selectedLead && !report && !analyzing && (
            <div className="border border-glass rounded-xl bg-glass backdrop-blur-xl p-16 text-center space-y-4">
              <div className="text-5xl">🔍</div>
              <h3 className="text-lg font-display font-bold">{selectedLead.name}</h3>
              <p className="text-sm text-neutral-400">
                {selectedLead.website
                  ? "Click 'Start Analysis' to crawl this website and extract AI-powered intelligence."
                  : "⚠️ No website URL set for this lead. Edit the lead and add a website URL first."}
              </p>
            </div>
          )}

          {/* Full Report */}
          {report && !analyzing && (
            <>
              {/* Report Header */}
              <div className="border border-glass rounded-xl bg-glass backdrop-blur-xl p-5 flex flex-wrap items-start justify-between gap-4">
                <div>
                  <h2 className="text-xl font-display font-extrabold">{report.company_name}</h2>
                  <a
                    href={report.website_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-xs text-persian-turquoise hover:underline font-mono"
                  >
                    {report.website_url}
                  </a>
                  {report.intelligence?.industry && (
                    <div className="mt-2">
                      <TagBadge label={report.intelligence.industry} variant="blue" />
                    </div>
                  )}
                </div>

                <div className="w-64">
                  {report.intelligence?.confidence_score !== undefined && (
                    <ConfidenceMeter score={report.intelligence.confidence_score} />
                  )}
                </div>
              </div>

              {/* Tab Navigation */}
              <div className="flex gap-1 border border-glass rounded-xl bg-glass backdrop-blur-xl p-1.5">
                {(["summary", "products", "sales", "tech", "links"] as const).map((tab) => (
                  <button
                    key={tab}
                    onClick={() => setActiveTab(tab)}
                    className={`flex-1 py-2 text-[11px] font-mono uppercase tracking-wide rounded-lg transition-all ${
                      activeTab === tab
                        ? "bg-gradient-to-r from-persian-indigo to-persian-turquoise text-black font-bold"
                        : "text-neutral-400 hover:text-white"
                    }`}
                  >
                    {tab === "summary" ? "📋 Summary" :
                     tab === "products" ? "📦 Products" :
                     tab === "sales" ? "🎯 Sales Intel" :
                     tab === "tech" ? "⚙️ Tech Stack" :
                     "🔗 Links"}
                  </button>
                ))}
              </div>

              {/* Tab Content */}
              <div className="border border-glass rounded-xl bg-glass backdrop-blur-xl p-6 space-y-5">

                {/* SUMMARY TAB */}
                {activeTab === "summary" && (
                  <div className="space-y-5">
                    {report.intelligence?.executive_summary && (
                      <div>
                        <h3 className="text-[10px] font-mono text-neutral-400 uppercase tracking-wider mb-2">Executive Summary</h3>
                        <p className="text-sm text-white leading-relaxed border-l-2 border-persian-turquoise pl-4">
                          {report.intelligence.executive_summary}
                        </p>
                      </div>
                    )}
                    {report.intelligence?.company_description && (
                      <div>
                        <h3 className="text-[10px] font-mono text-neutral-400 uppercase tracking-wider mb-2">Company Description</h3>
                        <p className="text-sm text-neutral-300 leading-relaxed">
                          {report.intelligence.company_description}
                        </p>
                      </div>
                    )}
                    <div className="grid grid-cols-2 gap-4">
                      {report.intelligence?.company_size && (
                        <div className="border border-glass rounded-lg p-3 bg-black/20">
                          <p className="text-[9px] font-mono text-neutral-500 uppercase">Company Size</p>
                          <p className="text-sm text-white mt-1">{report.intelligence.company_size}</p>
                        </div>
                      )}
                      {report.intelligence?.revenue_estimate && (
                        <div className="border border-glass rounded-lg p-3 bg-black/20">
                          <p className="text-[9px] font-mono text-neutral-500 uppercase">
                            Revenue Est. ({report.intelligence.revenue_confidence ?? "—"} confidence)
                          </p>
                          <p className="text-sm text-white mt-1">{report.intelligence.revenue_estimate}</p>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* PRODUCTS TAB */}
                {activeTab === "products" && (
                  <div className="space-y-5">
                    {(report.intelligence?.products?.length ?? 0) > 0 && (
                      <div>
                        <h3 className="text-[10px] font-mono text-neutral-400 uppercase tracking-wider mb-3">Products</h3>
                        <div className="flex flex-wrap gap-2">
                          {report.intelligence!.products.map((p, i) => (
                            <TagBadge key={i} label={p} variant="blue" />
                          ))}
                        </div>
                      </div>
                    )}
                    {(report.intelligence?.services?.length ?? 0) > 0 && (
                      <div>
                        <h3 className="text-[10px] font-mono text-neutral-400 uppercase tracking-wider mb-3">Services</h3>
                        <div className="flex flex-wrap gap-2">
                          {report.intelligence!.services.map((s, i) => (
                            <TagBadge key={i} label={s} variant="neutral" />
                          ))}
                        </div>
                      </div>
                    )}
                    {(report.intelligence?.products?.length ?? 0) === 0 &&
                     (report.intelligence?.services?.length ?? 0) === 0 && (
                      <p className="text-sm text-neutral-500 font-mono">No products or services extracted.</p>
                    )}
                  </div>
                )}

                {/* SALES INTEL TAB */}
                {activeTab === "sales" && (
                  <div className="space-y-5">
                    {report.intelligence?.ideal_sales_angle && (
                      <div className="p-4 rounded-xl border border-persian-turquoise/20 bg-persian-indigo/5">
                        <h3 className="text-[10px] font-mono text-persian-turquoise uppercase tracking-wider mb-2">
                          🎯 Ideal Sales Angle
                        </h3>
                        <p className="text-sm text-white leading-relaxed">
                          {report.intelligence.ideal_sales_angle}
                        </p>
                      </div>
                    )}
                    {(report.intelligence?.pain_points?.length ?? 0) > 0 && (
                      <div>
                        <h3 className="text-[10px] font-mono text-neutral-400 uppercase tracking-wider mb-3">Pain Points</h3>
                        <div className="space-y-2">
                          {report.intelligence!.pain_points.map((p, i) => (
                            <div key={i} className="flex items-start gap-2.5">
                              <span className="text-amber-400 mt-0.5 text-xs">⚠</span>
                              <p className="text-sm text-neutral-200">{p}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                    {(report.intelligence?.buying_signals?.length ?? 0) > 0 && (
                      <div>
                        <h3 className="text-[10px] font-mono text-neutral-400 uppercase tracking-wider mb-3">Buying Signals</h3>
                        <div className="space-y-2">
                          {report.intelligence!.buying_signals.map((s, i) => (
                            <div key={i} className="flex items-start gap-2.5">
                              <span className="text-emerald-400 mt-0.5 text-xs">✓</span>
                              <p className="text-sm text-neutral-200">{s}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* TECH STACK TAB */}
                {activeTab === "tech" && (
                  <div className="space-y-4">
                    <h3 className="text-[10px] font-mono text-neutral-400 uppercase tracking-wider">Detected Technology Stack</h3>
                    {report.tech_stack.length === 0 ? (
                      <p className="text-sm text-neutral-500 font-mono">No technology signals detected on this website.</p>
                    ) : (
                      <div className="flex flex-wrap gap-3">
                        {report.tech_stack.map((t, i) => (
                          <TechBadge key={i} item={t} />
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* LINKS TAB */}
                {activeTab === "links" && (
                  <div className="space-y-5">
                    {/* Social Links */}
                    {Object.keys(report.social_links).length > 0 && (
                      <div>
                        <h3 className="text-[10px] font-mono text-neutral-400 uppercase tracking-wider mb-3">Social Media</h3>
                        <div className="flex flex-wrap gap-2">
                          {Object.entries(report.social_links).map(([platform, url]) => (
                            <a
                              key={platform}
                              href={url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="inline-flex items-center gap-2 px-3 py-2 border border-glass bg-glass rounded-lg text-xs font-mono text-neutral-300 hover:text-white hover:border-persian-turquoise/40 transition-all"
                            >
                              <span>{SOCIAL_ICONS[platform] ?? "🔗"}</span>
                              {platform.charAt(0).toUpperCase() + platform.slice(1)}
                            </a>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Key Pages */}
                    <div>
                      <h3 className="text-[10px] font-mono text-neutral-400 uppercase tracking-wider mb-3">Key Pages</h3>
                      <div className="space-y-2">
                        {[
                          { label: "Contact Page", url: report.contact_page },
                          { label: "Careers Page", url: report.careers_page },
                          { label: "About Page", url: report.about_page },
                          { label: "Main Website", url: report.website_url },
                        ].map(({ label, url }) =>
                          url ? (
                            <div key={label} className="flex items-center justify-between border border-glass rounded-lg px-4 py-2.5 bg-black/20">
                              <span className="text-[11px] font-mono text-neutral-400 uppercase">{label}</span>
                              <a
                                href={url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-xs text-persian-turquoise hover:underline font-mono truncate max-w-[60%] text-right"
                              >
                                {url.replace(/(^\w+:|^)\/\//, "")}
                              </a>
                            </div>
                          ) : null
                        )}
                      </div>
                    </div>

                    {Object.keys(report.social_links).length === 0 &&
                      !report.contact_page && !report.careers_page && !report.about_page && (
                      <p className="text-sm text-neutral-500 font-mono">No additional links extracted.</p>
                    )}
                  </div>
                )}
              </div>

              {/* Analyzed timestamp */}
              {report.analyzed_at && (
                <p className="text-[10px] text-neutral-600 font-mono text-right">
                  Last analyzed: {new Date(report.analyzed_at).toLocaleString()}
                </p>
              )}
            </>
          )}
        </section>
      </main>
    </div>
  );
};

export default IntelligencePage;
