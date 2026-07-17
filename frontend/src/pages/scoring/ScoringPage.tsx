import React, { useCallback, useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../../contexts/AuthContext";
import axiosClient from "../../api/axiosClient";
import {
  ScoreBreakdown,
  ScoringResponse,
  ScoringStatusResponse,
  scoringApi,
} from "../../api/scoring";

// ─────────────────────────────────────────────────────────────
// Sub-components
// ─────────────────────────────────────────────────────────────

/** Animated SVG score gauge (arc-based) */
const ScoreGauge: React.FC<{ score: number }> = ({ score }) => {
  const pct = Math.min(100, Math.max(0, score));
  const radius = 70;
  const stroke = 10;
  const cx = 90;
  const cy = 90;
  const circumference = Math.PI * radius; // half-circle
  const offset = circumference - (pct / 100) * circumference;

  const color =
    pct >= 70 ? "#10b981" :  // emerald
    pct >= 40 ? "#f59e0b" :  // amber
    "#ef4444";                // red

  const gradId = `gauge-grad-${pct}`;

  return (
    <div className="flex flex-col items-center gap-2">
      <svg width="180" height="100" viewBox="0 0 180 100">
        <defs>
          <linearGradient id={gradId} x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#6366f1" />
            <stop offset="100%" stopColor={color} />
          </linearGradient>
        </defs>
        {/* Track */}
        <path
          d={`M ${cx - radius} ${cy} A ${radius} ${radius} 0 0 1 ${cx + radius} ${cy}`}
          fill="none"
          stroke="rgba(255,255,255,0.06)"
          strokeWidth={stroke}
          strokeLinecap="round"
        />
        {/* Progress arc */}
        <path
          d={`M ${cx - radius} ${cy} A ${radius} ${radius} 0 0 1 ${cx + radius} ${cy}`}
          fill="none"
          stroke={`url(#${gradId})`}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          style={{ transition: "stroke-dashoffset 1s ease-out" }}
        />
        {/* Score label */}
        <text x={cx} y={cy - 12} textAnchor="middle" fill="white" fontSize="28" fontWeight="bold" fontFamily="Outfit, sans-serif">
          {pct}
        </text>
        <text x={cx} y={cy + 4} textAnchor="middle" fill="rgba(255,255,255,0.4)" fontSize="10" fontFamily="JetBrains Mono, monospace">
          OUT OF 100
        </text>
      </svg>
    </div>
  );
};

/** Priority badge with color-coded styling */
const PriorityBadge: React.FC<{ priority: string }> = ({ priority }) => {
  const styles: Record<string, string> = {
    Hot: "bg-red-500/20 border-red-500/50 text-red-300",
    Warm: "bg-amber-500/20 border-amber-500/50 text-amber-300",
    Cold: "bg-blue-500/20 border-blue-500/50 text-blue-300",
  };
  const icons: Record<string, string> = {
    Hot: "🔥",
    Warm: "☀️",
    Cold: "❄️",
  };
  const cls = styles[priority] || "bg-glass border-glass text-neutral-300";
  return (
    <span className={`inline-flex items-center gap-2 px-4 py-2 rounded-full border text-sm font-bold font-mono ${cls}`}>
      {icons[priority] ?? "●"} {priority.toUpperCase()} LEAD
    </span>
  );
};

/** Confidence meter bar */
const ConfidenceMeter: React.FC<{ score: number }> = ({ score }) => {
  const pct = Math.min(100, Math.max(0, score));
  const color =
    pct >= 70 ? "from-emerald-500 to-teal-400" :
    pct >= 40 ? "from-amber-500 to-yellow-400" :
    "from-red-500 to-rose-400";
  return (
    <div className="space-y-1.5">
      <div className="flex justify-between items-center text-[10px] font-mono text-neutral-400">
        <span>AI CONFIDENCE</span>
        <span className="text-white font-bold">{pct}/100</span>
      </div>
      <div className="w-full h-2.5 bg-black/50 rounded-full border border-glass overflow-hidden p-0.5">
        <div
          style={{ width: `${pct}%` }}
          className={`h-full bg-gradient-to-r ${color} rounded-full transition-all duration-700 ease-out`}
        />
      </div>
    </div>
  );
};

/** Score breakdown table row */
const BreakdownRow: React.FC<{ item: ScoreBreakdown }> = ({ item }) => {
  const pct = item.max_score > 0 ? (item.score / item.max_score) * 100 : 0;
  const barColor =
    pct >= 70 ? "bg-emerald-500/60" :
    pct >= 40 ? "bg-amber-500/60" :
    "bg-red-500/60";

  return (
    <div className="py-3 border-b border-glass/30 last:border-b-0">
      <div className="flex items-center justify-between mb-1.5">
        <span className="text-xs font-medium text-white">{item.label}</span>
        <span className="text-xs font-mono text-neutral-400">{item.score}/{item.max_score}</span>
      </div>
      <div className="w-full h-1.5 bg-black/40 rounded-full overflow-hidden">
        <div
          style={{ width: `${pct}%` }}
          className={`h-full ${barColor} rounded-full transition-all duration-500`}
        />
      </div>
      <p className="text-[10px] text-neutral-500 mt-1 font-mono">{item.rationale}</p>
    </div>
  );
};

// ─────────────────────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────────────────────
interface LeadItem {
  id: string;
  name: string;
  website?: string;
  status: string;
}

// ─────────────────────────────────────────────────────────────
// Main Scoring Page
// ─────────────────────────────────────────────────────────────
export const ScoringPage: React.FC = () => {
  const { logout } = useAuth();

  const [leads, setLeads] = useState<LeadItem[]>([]);
  const [leadsSearch, setLeadsSearch] = useState("");
  const [selectedLead, setSelectedLead] = useState<LeadItem | null>(null);

  const [activeJob, setActiveJob] = useState<ScoringStatusResponse | null>(null);
  const [report, setReport] = useState<ScoringResponse | null>(null);
  const [scoring, setScoring] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"overview" | "breakdown" | "strategy">("overview");

  const pollingRef = useRef<NodeJS.Timeout | null>(null);

  // Fetch leads list
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

  const handleSelectLead = async (lead: LeadItem) => {
    stopPolling();
    setSelectedLead(lead);
    setActiveJob(null);
    setReport(null);
    setError(null);
    setActiveTab("overview");

    try {
      const existing = await scoringApi.getByLead(lead.id);
      if (existing.status === "completed") {
        setReport(existing);
      } else if (existing.status === "running" || existing.status === "pending") {
        setActiveJob(existing);
        setScoring(true);
        startPolling(existing.id);
      }
    } catch {
      // No existing report — fine
    }
  };

  const handleStartScoring = async () => {
    if (!selectedLead) return;
    setError(null);
    setReport(null);
    setScoring(true);
    setActiveTab("overview");

    try {
      const job = await scoringApi.startScoring(selectedLead.id);
      setActiveJob(job);
      startPolling(job.id);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to start scoring.");
      setScoring(false);
    }
  };

  const startPolling = (jobId: string) => {
    stopPolling();
    pollingRef.current = setInterval(async () => {
      try {
        const status = await scoringApi.pollJob(jobId);
        setActiveJob(status);

        if (status.status === "completed") {
          stopPolling();
          setScoring(false);
          if (selectedLead) {
            const full = await scoringApi.getByLead(selectedLead.id);
            setReport(full);
          }
        } else if (status.status === "failed") {
          stopPolling();
          setScoring(false);
          setError(status.error_message || "Scoring failed.");
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
      await scoringApi.deleteScore(selectedLead.id);
      setReport(null);
      setActiveJob(null);
      setError(null);
    } catch {
      alert("Could not delete the scoring report.");
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
      <div className="absolute top-0 right-1/4 w-[700px] h-[500px] bg-gradient-to-bl from-persian-indigo via-transparent to-transparent opacity-15 rounded-full blur-[140px] pointer-events-none" />
      <div className="absolute bottom-0 left-0 w-[500px] h-[500px] bg-gradient-to-tr from-persian-turquoise via-transparent to-transparent opacity-10 rounded-full blur-[120px] pointer-events-none" />
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
            <span className="text-[10px] text-neutral-500 font-mono tracking-widest uppercase">Lead Scoring Engine</span>
          </div>
        </div>
        <nav className="flex gap-3 items-center">
          <Link to="/" className="px-3 py-1.5 border border-glass hover:border-persian-turquoise/40 text-neutral-400 hover:text-white font-mono text-xs rounded transition-all">
            ← LEADS
          </Link>
          <Link to="/discovery" className="px-3 py-1.5 border border-glass hover:border-persian-turquoise/40 text-neutral-400 hover:text-white font-mono text-xs rounded transition-all">
            🔍 DISCOVERY
          </Link>
          <Link to="/intelligence" className="px-3 py-1.5 border border-glass hover:border-persian-turquoise/40 text-neutral-400 hover:text-white font-mono text-xs rounded transition-all">
            🧠 INTELLIGENCE
          </Link>
          <Link to="/outreach" className="px-3 py-1.5 border border-glass hover:border-persian-turquoise/40 text-neutral-400 hover:text-white font-mono text-xs rounded transition-all">
            ✉️ OUTREACH
          </Link>
          <button onClick={logout} className="px-3 py-1.5 border border-glass hover:border-red-500/40 hover:bg-red-500/10 text-neutral-400 hover:text-red-400 font-mono text-xs rounded transition-all">
            DISCONNECT
          </button>
        </nav>
      </header>

      {/* ── Main Layout ── */}
      <main className="relative z-10 max-w-7xl mx-auto px-6 md:px-10 mt-8 grid grid-cols-1 lg:grid-cols-[280px_1fr] gap-6">

        {/* ── Left: Lead Selector ── */}
        <aside className="space-y-4">
          <div>
            <h2 className="text-xl font-display font-extrabold tracking-tight">Lead Scoring</h2>
            <p className="text-[11px] text-neutral-500 mt-1 font-mono">AI-powered quality scoring engine</p>
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
            <div className="max-h-[360px] overflow-y-auto divide-y divide-glass/30">
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
                    <div className="text-[10px] text-neutral-500 font-mono mt-0.5 truncate">
                      {lead.website ? lead.website.replace(/(^\w+:|^)\/\//, "") : "no website"}
                    </div>
                  </button>
                ))
              )}
            </div>
          </div>

          {/* Score button */}
          {selectedLead && (
            <button
              onClick={handleStartScoring}
              disabled={scoring}
              className="w-full py-3 bg-gradient-to-r from-persian-indigo to-persian-turquoise hover:from-persian-turquoise hover:to-persian-indigo text-black font-bold text-xs rounded-xl transition-all active:scale-[0.98] duration-300 disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {scoring ? (
                <>
                  <span className="w-3 h-3 border-2 border-black/40 border-t-black rounded-full animate-spin" />
                  SCORING...
                </>
              ) : report ? "🔄 RECALCULATE" : "🎯 SCORE LEAD"}
            </button>
          )}

          {report && (
            <button
              onClick={handleDelete}
              className="w-full py-2 border border-red-500/20 hover:border-red-500/50 hover:bg-red-500/10 text-red-500/70 hover:text-red-400 font-mono text-[10px] rounded-xl transition-all"
            >
              DELETE SCORE
            </button>
          )}
        </aside>

        {/* ── Right: Report Panel ── */}
        <section className="space-y-5 min-h-[600px]">

          {/* Error */}
          {error && (
            <div className="p-4 rounded-xl border border-red-500/20 bg-red-500/10 text-red-400 text-xs font-mono">
              ⚠️ {error}
            </div>
          )}

          {/* Progress card */}
          {activeJob && scoring && (
            <div className="border border-glass rounded-xl bg-glass backdrop-blur-xl p-6 space-y-4">
              <div className="flex justify-between items-center text-xs font-mono">
                <div>
                  STATUS:{" "}
                  <span className="font-bold text-persian-turquoise animate-pulse">
                    {activeJob.status.toUpperCase()}
                  </span>
                </div>
                <div>PROGRESS: <span className="font-bold text-white">{progress.toFixed(0)}%</span></div>
              </div>

              <div className="w-full bg-black/50 border border-glass h-3 rounded-full overflow-hidden p-0.5">
                <div
                  style={{ width: `${progress}%` }}
                  className="h-full bg-gradient-to-r from-persian-indigo to-persian-turquoise rounded-full transition-all duration-700 ease-out"
                />
              </div>

              <div className="grid grid-cols-4 gap-2 text-[9px] font-mono text-neutral-600">
                {[
                  { label: "LOAD DATA", pct: 25 },
                  { label: "FEATURES", pct: 40 },
                  { label: "RULE ENGINE", pct: 55 },
                  { label: "AI REASON", pct: 85 },
                ].map((stage) => (
                  <div
                    key={stage.label}
                    className={`flex flex-col items-center gap-1 ${progress >= stage.pct ? "text-persian-turquoise" : ""}`}
                  >
                    <div className={`w-2 h-2 rounded-full ${progress >= stage.pct ? "bg-persian-turquoise" : "bg-neutral-800 border border-glass"}`} />
                    {stage.label}
                  </div>
                ))}
              </div>

              <p className="text-[10px] text-neutral-600 font-mono text-center">
                Scoring <span className="text-white">{activeJob.company_name}</span> — combining rule engine + AI reasoning
              </p>
            </div>
          )}

          {/* Empty state */}
          {!selectedLead && !activeJob && !report && (
            <div className="border border-glass rounded-xl bg-glass backdrop-blur-xl p-16 text-center space-y-4">
              <div className="text-5xl">🎯</div>
              <h3 className="text-xl font-display font-bold">Lead Scoring Engine</h3>
              <p className="text-sm text-neutral-400 max-w-sm mx-auto">
                Select a lead from the sidebar to score it using our AI-powered scoring engine. Combines weighted rule scoring with LLM reasoning.
              </p>
            </div>
          )}

          {selectedLead && !report && !scoring && (
            <div className="border border-glass rounded-xl bg-glass backdrop-blur-xl p-16 text-center space-y-4">
              <div className="text-5xl">📊</div>
              <h3 className="text-lg font-display font-bold">{selectedLead.name}</h3>
              <p className="text-sm text-neutral-400">
                Click 'Score Lead' to compute an AI-powered quality score combining rule-based signals with LLM reasoning.
              </p>
              <p className="text-xs text-neutral-600 font-mono">
                Tip: Run Company Intelligence first for richer scoring inputs.
              </p>
            </div>
          )}

          {/* Full Report */}
          {report && !scoring && (
            <>
              {/* Score Header */}
              <div className="border border-glass rounded-xl bg-glass backdrop-blur-xl p-6">
                <div className="flex flex-wrap items-center justify-between gap-6">
                  {/* Gauge */}
                  <div className="flex flex-col items-center gap-3">
                    <ScoreGauge score={report.score ?? 0} />
                    {report.priority && <PriorityBadge priority={report.priority} />}
                  </div>

                  {/* Score meta */}
                  <div className="flex-1 min-w-[200px] space-y-4">
                    <div>
                      <h2 className="text-xl font-display font-extrabold">{report.company_name}</h2>
                      {report.website_url && (
                        <a
                          href={report.website_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-xs text-persian-turquoise hover:underline font-mono"
                        >
                          {report.website_url}
                        </a>
                      )}
                    </div>

                    <div className="grid grid-cols-2 gap-3">
                      <div className="border border-glass rounded-lg p-3 bg-black/20 text-center">
                        <p className="text-[9px] font-mono text-neutral-500 uppercase">Rule Score</p>
                        <p className="text-lg font-bold text-white mt-1">{report.rule_score ?? "—"}/100</p>
                      </div>
                      <div className="border border-glass rounded-lg p-3 bg-black/20 text-center">
                        <p className="text-[9px] font-mono text-neutral-500 uppercase">AI Adjustment</p>
                        <p className={`text-lg font-bold mt-1 ${
                          (report.llm_score_adjustment ?? 0) > 0 ? "text-emerald-400" :
                          (report.llm_score_adjustment ?? 0) < 0 ? "text-red-400" :
                          "text-neutral-400"
                        }`}>
                          {(report.llm_score_adjustment ?? 0) > 0 ? "+" : ""}{report.llm_score_adjustment ?? 0}
                        </p>
                      </div>
                    </div>

                    {report.confidence_score !== null && report.confidence_score !== undefined && (
                      <ConfidenceMeter score={report.confidence_score} />
                    )}
                  </div>
                </div>

                {/* Score explanation */}
                {report.score_explanation && (
                  <div className="mt-4 pt-4 border-t border-glass/50">
                    <p className="text-[10px] font-mono text-neutral-400 uppercase tracking-wider mb-2">Scoring Explanation</p>
                    <p className="text-sm text-neutral-300 leading-relaxed">{report.score_explanation}</p>
                  </div>
                )}
              </div>

              {/* Tab navigation */}
              <div className="flex gap-1 border border-glass rounded-xl bg-glass backdrop-blur-xl p-1.5">
                {(["overview", "breakdown", "strategy"] as const).map((tab) => (
                  <button
                    key={tab}
                    onClick={() => setActiveTab(tab)}
                    className={`flex-1 py-2 text-[11px] font-mono uppercase tracking-wide rounded-lg transition-all ${
                      activeTab === tab
                        ? "bg-gradient-to-r from-persian-indigo to-persian-turquoise text-black font-bold"
                        : "text-neutral-400 hover:text-white"
                    }`}
                  >
                    {tab === "overview" ? "📊 Overview" :
                     tab === "breakdown" ? "🔢 Breakdown" :
                     "🎯 Strategy"}
                  </button>
                ))}
              </div>

              {/* Tab Content */}
              <div className="border border-glass rounded-xl bg-glass backdrop-blur-xl p-6 space-y-5">

                {/* OVERVIEW TAB */}
                {activeTab === "overview" && (
                  <div className="space-y-6">
                    {/* Strengths */}
                    {report.strengths.length > 0 && (
                      <div>
                        <h3 className="text-[10px] font-mono text-emerald-400 uppercase tracking-wider mb-3">
                          ✓ Strengths
                        </h3>
                        <div className="space-y-2">
                          {report.strengths.map((s, i) => (
                            <div key={i} className="flex items-start gap-2.5 p-3 rounded-lg bg-emerald-500/5 border border-emerald-500/10">
                              <span className="text-emerald-400 mt-0.5 text-xs shrink-0">✓</span>
                              <p className="text-sm text-neutral-200">{s}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Weaknesses */}
                    {report.weaknesses.length > 0 && (
                      <div>
                        <h3 className="text-[10px] font-mono text-amber-400 uppercase tracking-wider mb-3">
                          ⚠ Weaknesses
                        </h3>
                        <div className="space-y-2">
                          {report.weaknesses.map((w, i) => (
                            <div key={i} className="flex items-start gap-2.5 p-3 rounded-lg bg-amber-500/5 border border-amber-500/10">
                              <span className="text-amber-400 mt-0.5 text-xs shrink-0">⚠</span>
                              <p className="text-sm text-neutral-200">{w}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Risk Factors */}
                    {report.risk_factors.length > 0 && (
                      <div>
                        <h3 className="text-[10px] font-mono text-red-400 uppercase tracking-wider mb-3">
                          ⛔ Risk Factors
                        </h3>
                        <div className="space-y-2">
                          {report.risk_factors.map((r, i) => (
                            <div key={i} className="flex items-start gap-2.5 p-3 rounded-lg bg-red-500/5 border border-red-500/10">
                              <span className="text-red-400 mt-0.5 text-xs shrink-0">⛔</span>
                              <p className="text-sm text-neutral-200">{r}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {report.strengths.length === 0 && report.weaknesses.length === 0 && report.risk_factors.length === 0 && (
                      <p className="text-sm text-neutral-500 font-mono">No qualitative data extracted.</p>
                    )}
                  </div>
                )}

                {/* BREAKDOWN TAB */}
                {activeTab === "breakdown" && (
                  <div className="space-y-2">
                    <h3 className="text-[10px] font-mono text-neutral-400 uppercase tracking-wider mb-3">
                      Rule Engine Score Breakdown
                    </h3>
                    {report.score_breakdown.length === 0 ? (
                      <p className="text-sm text-neutral-500 font-mono">No breakdown data available.</p>
                    ) : (
                      <div className="divide-y divide-glass/30">
                        {report.score_breakdown.map((item, i) => (
                          <BreakdownRow key={i} item={item} />
                        ))}
                      </div>
                    )}
                    <div className="pt-3 border-t border-glass/30 flex justify-between items-center">
                      <span className="text-xs font-mono text-neutral-400">TOTAL RULE SCORE</span>
                      <span className="text-lg font-bold text-white font-mono">{report.rule_score ?? "—"}/100</span>
                    </div>
                    {(report.llm_score_adjustment ?? 0) !== 0 && (
                      <div className="flex justify-between items-center">
                        <span className="text-xs font-mono text-neutral-400">AI ADJUSTMENT</span>
                        <span className={`text-sm font-bold font-mono ${
                          (report.llm_score_adjustment ?? 0) > 0 ? "text-emerald-400" : "text-red-400"
                        }`}>
                          {(report.llm_score_adjustment ?? 0) > 0 ? "+" : ""}{report.llm_score_adjustment}
                        </span>
                      </div>
                    )}
                    <div className="flex justify-between items-center pt-2 border-t border-glass/50">
                      <span className="text-xs font-mono text-persian-turquoise uppercase">FINAL SCORE</span>
                      <span className="text-xl font-bold text-white font-mono">{report.score ?? "—"}/100</span>
                    </div>
                  </div>
                )}

                {/* STRATEGY TAB */}
                {activeTab === "strategy" && (
                  <div className="space-y-5">
                    {report.recommended_outreach ? (
                      <div className="p-5 rounded-xl border border-persian-turquoise/20 bg-persian-indigo/5 space-y-2">
                        <h3 className="text-[10px] font-mono text-persian-turquoise uppercase tracking-wider">
                          🎯 Recommended Outreach Strategy
                        </h3>
                        <p className="text-sm text-white leading-relaxed">{report.recommended_outreach}</p>
                      </div>
                    ) : (
                      <p className="text-sm text-neutral-500 font-mono">No outreach strategy generated.</p>
                    )}

                    {/* Meta info */}
                    <div className="grid grid-cols-2 gap-3 pt-2">
                      <div className="border border-glass rounded-lg p-3 bg-black/20">
                        <p className="text-[9px] font-mono text-neutral-500 uppercase">Scoring Profile</p>
                        <p className="text-sm text-white mt-1 font-mono">{report.scoring_profile}</p>
                      </div>
                      <div className="border border-glass rounded-lg p-3 bg-black/20">
                        <p className="text-[9px] font-mono text-neutral-500 uppercase">Version</p>
                        <p className="text-sm text-white mt-1 font-mono">{report.scoring_version}</p>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Scored timestamp */}
              {report.scored_at && (
                <p className="text-[10px] text-neutral-600 font-mono text-right">
                  Last scored: {new Date(report.scored_at).toLocaleString()}
                </p>
              )}
            </>
          )}
        </section>
      </main>
    </div>
  );
};

export default ScoringPage;
