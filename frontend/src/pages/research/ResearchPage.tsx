import React, { useEffect, useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { leadsApi, Lead } from '../../api/leads';
import { researchApi, ResearchReport } from '../../api/research';

export const ResearchPage: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const [leads, setLeads] = useState<Lead[]>([]);
  const [selectedLeadId, setSelectedLeadId] = useState<string | null>(null);
  const [report, setReport] = useState<ResearchReport | null>(null);
  const [loadingLeads, setLoadingLeads] = useState<boolean>(true);
  const [loadingReport, setLoadingReport] = useState<boolean>(false);
  const [analyzing, setAnalyzing] = useState<boolean>(false);
  const [progress, setProgress] = useState<number>(0);
  const [activeTab, setActiveTab] = useState<
    'overview' | 'swot' | 'website' | 'news' | 'technology' | 'hiring' | 'competitors' | 'social' | 'graph' | 'sources'
  >('overview');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    fetchLeads();
  }, []);

  useEffect(() => {
    if (selectedLeadId) {
      fetchReport(selectedLeadId);
    }
  }, [selectedLeadId]);

  const fetchLeads = async () => {
    try {
      setLoadingLeads(true);
      const res = await leadsApi.getLeads({ limit: 100 });
      const items = res?.items || [];
      setLeads(items);
      if (items.length > 0 && !selectedLeadId) {
        setSelectedLeadId(items[0].id);
      }
    } catch (err: any) {
      setErrorMessage('Failed to load target accounts list');
    } finally {
      setLoadingLeads(false);
    }
  };

  const fetchReport = async (leadId: string) => {
    try {
      setLoadingReport(true);
      setErrorMessage(null);
      const data = await researchApi.getReportByLead(leadId);
      setReport(data);
    } catch (err: any) {
      setReport(null);
    } finally {
      setLoadingReport(false);
    }
  };

  const handleStartResearch = async () => {
    if (!selectedLeadId) return;
    try {
      setAnalyzing(true);
      setProgress(10);
      setErrorMessage(null);

      const statusRes = await researchApi.analyzeCompany(selectedLeadId);
      let currentProgress = statusRes.progress || 10;
      setProgress(currentProgress);

      const pollInterval = setInterval(async () => {
        try {
          const pollRes = await researchApi.getJobStatus(statusRes.id);
          setProgress(pollRes.progress);
          if (pollRes.status === 'completed') {
            clearInterval(pollInterval);
            setAnalyzing(false);
            fetchReport(selectedLeadId);
          } else if (pollRes.status === 'failed') {
            clearInterval(pollInterval);
            setAnalyzing(false);
            setErrorMessage(pollRes.error_message || 'Multi-agent research analysis failed.');
          }
        } catch (e) {
          clearInterval(pollInterval);
          setAnalyzing(false);
        }
      }, 2000);
    } catch (err: any) {
      setAnalyzing(false);
      setErrorMessage(err.response?.data?.detail || 'Failed to trigger AI research agents');
    }
  };

  const filteredLeads = (leads || []).filter(l =>
    (l.name || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
    (l.website || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
    (l.email || '').toLowerCase().includes(searchQuery.toLowerCase())
  );

  const selectedLead = (leads || []).find(l => l.id === selectedLeadId);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans flex flex-col">
      {/* Top Header Navigation */}
      <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-8">
            <div className="flex items-center space-x-3 cursor-pointer" onClick={() => navigate('/leads')}>
              <div className="h-9 w-9 rounded-xl bg-gradient-to-tr from-cyan-500 via-indigo-500 to-purple-500 flex items-center justify-center font-bold text-white shadow-lg shadow-cyan-500/25">
                LF
              </div>
              <span className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white via-slate-200 to-slate-400">
                LeadForgeAI
              </span>
            </div>

            <nav className="hidden md:flex items-center space-x-1">
              <Link to="/leads" className="px-3 py-2 rounded-lg text-sm font-medium text-slate-400 hover:text-white hover:bg-slate-800/50 transition">Leads</Link>
              <Link to="/discovery" className="px-3 py-2 rounded-lg text-sm font-medium text-slate-400 hover:text-white hover:bg-slate-800/50 transition">Discovery</Link>
              <Link to="/intelligence" className="px-3 py-2 rounded-lg text-sm font-medium text-slate-400 hover:text-white hover:bg-slate-800/50 transition">Intelligence</Link>
              <Link to="/scoring" className="px-3 py-2 rounded-lg text-sm font-medium text-slate-400 hover:text-white hover:bg-slate-800/50 transition">Scoring</Link>
              <Link to="/outreach" className="px-3 py-2 rounded-lg text-sm font-medium text-slate-400 hover:text-white hover:bg-slate-800/50 transition">Outreach</Link>
              <Link to="/sales-intelligence" className="px-3 py-2 rounded-lg text-sm font-medium text-slate-400 hover:text-white hover:bg-slate-800/50 transition">Sales Intelligence</Link>
              <Link to="/research" className="px-3 py-2 rounded-lg text-sm font-medium text-cyan-400 bg-cyan-500/10 border border-cyan-500/20">AI Research Agents</Link>
            </nav>
          </div>

          <div className="flex items-center space-x-4">
            <span className="text-xs text-slate-400 hidden sm:inline">{user?.email}</span>
            <button
              onClick={() => logout()}
              className="text-xs px-3 py-1.5 rounded-lg border border-slate-700 text-slate-300 hover:bg-slate-800 hover:text-white transition"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      {/* Main Workspace Layout */}
      <div className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8 flex flex-col md:flex-row gap-6">
        
        {/* Left Sidebar: Leads Selection List */}
        <aside className="w-full md:w-80 bg-slate-900/60 border border-slate-800 rounded-2xl p-4 flex flex-col h-[calc(100vh-8rem)]">
          <h2 className="text-base font-bold text-white mb-3 flex items-center justify-between">
            <span>Target Accounts</span>
            <span className="text-xs px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 font-mono">
              {(leads || []).length}
            </span>
          </h2>

          <input
            type="text"
            placeholder="Search lead or domain..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500 mb-3"
          />

          <div className="flex-1 overflow-y-auto space-y-2 pr-1 custom-scrollbar">
            {loadingLeads ? (
              <div className="text-center py-8 text-xs text-slate-500">Loading leads...</div>
            ) : filteredLeads.length === 0 ? (
              <div className="text-center py-8 text-xs text-slate-500">No leads found</div>
            ) : (
              filteredLeads.map((lead) => {
                const isSelected = lead.id === selectedLeadId;
                return (
                  <div
                    key={lead.id}
                    onClick={() => setSelectedLeadId(lead.id)}
                    className={`p-3 rounded-xl cursor-pointer border transition ${
                      isSelected
                        ? 'bg-cyan-950/40 border-cyan-500/50 shadow-md shadow-cyan-500/10'
                        : 'bg-slate-950/40 border-slate-800/80 hover:border-slate-700 hover:bg-slate-800/30'
                    }`}
                  >
                    <div className="font-semibold text-sm text-white truncate">{lead.name || 'Unnamed Account'}</div>
                    <div className="text-xs text-slate-400 truncate mt-0.5">{lead.website || lead.email || 'No website'}</div>
                  </div>
                );
              })
            )}
          </div>
        </aside>

        {/* Right Main Dashboard Area */}
        <main className="flex-1 bg-slate-900/40 border border-slate-800 rounded-2xl p-6 flex flex-col">
          {!selectedLead ? (
            <div className="flex-1 flex items-center justify-center text-slate-500 text-sm">
              Select a lead from the sidebar to inspect multi-agent AI research.
            </div>
          ) : (
            <div className="space-y-6">
              
              {/* Account Header & Action Bar */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-800">
                <div>
                  <h1 className="text-2xl font-extrabold text-white tracking-tight flex items-center space-x-3">
                    <span>{selectedLead.name}</span>
                    {selectedLead.website && (
                      <a
                        href={selectedLead.website.startsWith('http') ? selectedLead.website : `https://${selectedLead.website}`}
                        target="_blank"
                        rel="noreferrer"
                        className="text-xs px-2.5 py-1 rounded-md bg-slate-800 text-cyan-400 hover:underline font-mono"
                      >
                        🔗 {selectedLead.website}
                      </a>
                    )}
                  </h1>
                  <p className="text-xs text-slate-400 mt-1">
                    Phase 9 Multi-Agent Autonomous Research & Knowledge Discovery Platform
                  </p>
                </div>

                <button
                  onClick={handleStartResearch}
                  disabled={analyzing}
                  className={`px-5 py-2.5 rounded-xl font-medium text-sm transition shadow-lg flex items-center justify-center space-x-2 ${
                    analyzing
                      ? 'bg-slate-800 text-slate-400 cursor-not-allowed border border-slate-700'
                      : 'bg-gradient-to-r from-cyan-500 via-indigo-500 to-purple-500 text-white hover:opacity-90 shadow-cyan-500/25'
                  }`}
                >
                  {analyzing ? (
                    <>
                      <div className="w-4 h-4 border-2 border-slate-400 border-t-transparent rounded-full animate-spin"></div>
                      <span>Researching ({progress}%)...</span>
                    </>
                  ) : report ? (
                    <span>🔄 Re-run AI Research Agents</span>
                  ) : (
                    <span>🤖 Run AI Research Agents</span>
                  )}
                </button>
              </div>

              {/* Progress Bar when analyzing */}
              {analyzing && (
                <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl space-y-2">
                  <div className="flex justify-between text-xs text-slate-300">
                    <span>Running Website, News, Hiring, Tech & Competitor Agents...</span>
                    <span>{progress}%</span>
                  </div>
                  <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
                    <div
                      className="bg-gradient-to-r from-cyan-400 via-indigo-500 to-purple-500 h-full transition-all duration-300"
                      style={{ width: `${progress}%` }}
                    ></div>
                  </div>
                </div>
              )}

              {/* Error Alert */}
              {errorMessage && (
                <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs">
                  ⚠️ {errorMessage}
                </div>
              )}

              {/* Report Content */}
              {loadingReport ? (
                <div className="py-16 text-center text-slate-500 text-sm">Loading AI Research Report...</div>
              ) : !report ? (
                <div className="py-16 text-center bg-slate-950/50 border border-slate-800/80 rounded-2xl p-8 space-y-4">
                  <div className="text-4xl">🤖</div>
                  <h3 className="text-lg font-bold text-white">No AI Research Report Generated</h3>
                  <p className="text-xs text-slate-400 max-w-md mx-auto">
                    Click <strong>Run AI Research Agents</strong> above to autonomously inspect public web pages, news articles, open job positions, tech stacks, competitors, and social signals.
                  </p>
                </div>
              ) : (
                <div className="space-y-6">

                  {/* Top Key Metrics Banner */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="bg-slate-950/60 border border-slate-800 p-5 rounded-2xl flex flex-col justify-between">
                      <div className="text-xs font-semibold uppercase tracking-wider text-slate-400">Research Confidence Rating</div>
                      <div className="my-3 flex items-baseline space-x-3">
                        <span className="text-4xl font-extrabold text-cyan-400">
                          {report.overall_confidence}%
                        </span>
                        <span className="text-xs px-2.5 py-1 rounded-full font-bold uppercase border border-cyan-500/30 bg-cyan-950/50 text-cyan-300">
                          Verified Knowledge
                        </span>
                      </div>
                      <p className="text-xs text-slate-400">Calculated across DOM, DNS, HTTP signatures & cross-validation.</p>
                    </div>

                    <div className="bg-slate-950/60 border border-slate-800 p-5 rounded-2xl flex flex-col justify-between">
                      <div className="text-xs font-semibold uppercase tracking-wider text-slate-400">Business Model</div>
                      <div className="my-2">
                        <span className="text-lg font-bold text-white">
                          {report.website_findings?.business_model || 'B2B Enterprise SaaS'}
                        </span>
                      </div>
                      <div className="text-xs text-slate-400">
                        Target Market: <strong className="text-slate-200">{(report.website_findings?.target_customers || []).join(', ')}</strong>
                      </div>
                    </div>

                    <div className="bg-slate-950/60 border border-slate-800 p-5 rounded-2xl flex flex-col justify-between">
                      <div className="text-xs font-semibold uppercase tracking-wider text-slate-400">Hiring Velocity</div>
                      <div className="my-2 flex items-center justify-between">
                        <span className="text-2xl font-bold text-emerald-400">
                          {report.hiring_findings?.open_positions_count || 0} Openings
                        </span>
                        <span className="text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono">
                          {report.hiring_findings?.hiring_velocity || 'Medium'} Velocity
                        </span>
                      </div>
                      <p className="text-xs text-slate-400 truncate">{report.hiring_findings?.growth_stage}</p>
                    </div>
                  </div>

                  {/* Navigation Tabs */}
                  <div className="border-b border-slate-800 flex space-x-2 overflow-x-auto pb-1">
                    {[
                      { id: 'overview', label: '📊 Overview' },
                      { id: 'swot', label: '🧠 AI SWOT & Insights' },
                      { id: 'website', label: '🌐 Website Research' },
                      { id: 'news', label: `📰 News (${(report.news_findings?.articles || []).length})` },
                      { id: 'technology', label: '⚡ Tech Stack' },
                      { id: 'hiring', label: `👥 Hiring (${report.hiring_findings?.open_positions_count || 0})` },
                      { id: 'competitors', label: `⚔️ Competitors (${(report.competitor_findings?.competitors || []).length})` },
                      { id: 'social', label: '📱 Social Footprint' },
                      { id: 'graph', label: '🕸️ Knowledge Graph' },
                      { id: 'sources', label: `🔍 Facts (${(report.verified_facts || []).length})` },
                    ].map((t) => (
                      <button
                        key={t.id}
                        onClick={() => setActiveTab(t.id as any)}
                        className={`px-4 py-2 text-xs font-semibold rounded-xl transition whitespace-nowrap ${
                          activeTab === t.id
                            ? 'bg-cyan-600 text-white shadow-lg shadow-cyan-500/20'
                            : 'text-slate-400 hover:text-white hover:bg-slate-800/40'
                        }`}
                      >
                        {t.label}
                      </button>
                    ))}
                  </div>

                  {/* Tab 1: Overview */}
                  {activeTab === 'overview' && (
                    <div className="space-y-4">
                      <div className="bg-slate-950/50 border border-slate-800 p-5 rounded-2xl space-y-3">
                        <h4 className="text-xs font-bold uppercase tracking-wider text-cyan-400">Executive Summary</h4>
                        <p className="text-sm text-slate-200 leading-relaxed">
                          {report.ai_summary?.executive_summary || report.website_findings?.executive_summary}
                        </p>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="bg-slate-950/50 border border-slate-800 p-5 rounded-2xl space-y-2">
                          <h4 className="text-xs font-bold uppercase tracking-wider text-emerald-400">Sales Opportunity</h4>
                          <p className="text-xs text-slate-300 leading-relaxed">{report.ai_summary?.sales_opportunity}</p>
                        </div>
                        <div className="bg-slate-950/50 border border-slate-800 p-5 rounded-2xl space-y-2">
                          <h4 className="text-xs font-bold uppercase tracking-wider text-purple-400">Recommended Strategy</h4>
                          <p className="text-xs text-slate-300 leading-relaxed">{report.ai_summary?.recommended_strategy}</p>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Tab 2: AI SWOT & Insights */}
                  {activeTab === 'swot' && (
                    <div className="space-y-4">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="bg-slate-950/50 border border-emerald-500/20 p-5 rounded-2xl space-y-2">
                          <h4 className="text-xs font-bold uppercase tracking-wider text-emerald-400">💪 Strengths</h4>
                          <ul className="list-disc list-inside text-xs text-slate-300 space-y-1">
                            {(report.ai_summary?.swot?.strengths || []).map((s, i) => (
                              <li key={i}>{s}</li>
                            ))}
                          </ul>
                        </div>
                        <div className="bg-slate-950/50 border border-rose-500/20 p-5 rounded-2xl space-y-2">
                          <h4 className="text-xs font-bold uppercase tracking-wider text-rose-400">⚠️ Weaknesses</h4>
                          <ul className="list-disc list-inside text-xs text-slate-300 space-y-1">
                            {(report.ai_summary?.swot?.weaknesses || []).map((w, i) => (
                              <li key={i}>{w}</li>
                            ))}
                          </ul>
                        </div>
                        <div className="bg-slate-950/50 border border-cyan-500/20 p-5 rounded-2xl space-y-2">
                          <h4 className="text-xs font-bold uppercase tracking-wider text-cyan-400">🚀 Opportunities</h4>
                          <ul className="list-disc list-inside text-xs text-slate-300 space-y-1">
                            {(report.ai_summary?.swot?.opportunities || []).map((o, i) => (
                              <li key={i}>{o}</li>
                            ))}
                          </ul>
                        </div>
                        <div className="bg-slate-950/50 border border-amber-500/20 p-5 rounded-2xl space-y-2">
                          <h4 className="text-xs font-bold uppercase tracking-wider text-amber-400">🛡️ Threats</h4>
                          <ul className="list-disc list-inside text-xs text-slate-300 space-y-1">
                            {(report.ai_summary?.swot?.threats || []).map((t, i) => (
                              <li key={i}>{t}</li>
                            ))}
                          </ul>
                        </div>
                      </div>

                      <div className="bg-slate-950/50 border border-slate-800 p-5 rounded-2xl space-y-2">
                        <h4 className="text-xs font-bold uppercase tracking-wider text-indigo-400">Target Pitch Angle</h4>
                        <p className="text-xs text-slate-200 font-medium">{report.ai_summary?.pitch_angle}</p>
                      </div>
                    </div>
                  )}

                  {/* Tab 3: Website Research */}
                  {activeTab === 'website' && (
                    <div className="space-y-4">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="bg-slate-950/50 border border-slate-800 p-5 rounded-2xl space-y-2">
                          <h4 className="text-xs font-bold uppercase tracking-wider text-cyan-400">Products Offered</h4>
                          <ul className="list-disc list-inside text-xs text-slate-300 space-y-1">
                            {(report.website_findings?.products || []).map((p, i) => (
                              <li key={i}>{p}</li>
                            ))}
                          </ul>
                        </div>
                        <div className="bg-slate-950/50 border border-slate-800 p-5 rounded-2xl space-y-2">
                          <h4 className="text-xs font-bold uppercase tracking-wider text-purple-400">Services Offered</h4>
                          <ul className="list-disc list-inside text-xs text-slate-300 space-y-1">
                            {(report.website_findings?.services || []).map((s, i) => (
                              <li key={i}>{s}</li>
                            ))}
                          </ul>
                        </div>
                      </div>

                      <div className="bg-slate-950/50 border border-slate-800 p-5 rounded-2xl space-y-2">
                        <h4 className="text-xs font-bold uppercase tracking-wider text-rose-400">Target Pain Points</h4>
                        <ul className="list-disc list-inside text-xs text-slate-300 space-y-1">
                          {(report.website_findings?.pain_points || []).map((pp, i) => (
                            <li key={i}>{pp}</li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  )}

                  {/* Tab 4: News */}
                  {activeTab === 'news' && (
                    <div className="space-y-3">
                      {(report.news_findings?.articles || []).map((art, idx) => (
                        <div key={idx} className="bg-slate-950/50 border border-slate-800 p-4 rounded-xl space-y-2">
                          <div className="flex items-center justify-between">
                            <span className="text-xs font-bold uppercase text-cyan-400">{art.category}</span>
                            <span className="text-[10px] text-slate-500 font-mono">{art.date || 'Recent'} • {art.source}</span>
                          </div>
                          <h4 className="text-sm font-bold text-white">{art.headline}</h4>
                          <p className="text-xs text-slate-300">{art.summary}</p>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Tab 5: Technology Stack */}
                  {activeTab === 'technology' && (
                    <div className="space-y-4">
                      <div className="bg-slate-950/50 border border-slate-800 p-4 rounded-xl flex items-center justify-between">
                        <div>
                          <span className="text-xs text-slate-400 uppercase font-semibold">Tech Maturity Rating</span>
                          <div className="text-base font-bold text-cyan-400">{report.tech_findings?.tech_maturity}</div>
                        </div>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div className="bg-slate-950/50 border border-slate-800 p-4 rounded-xl space-y-2">
                          <h5 className="text-xs font-bold uppercase text-indigo-400">Frontend</h5>
                          <div className="flex flex-wrap gap-1">
                            {(report.tech_findings?.frontend || []).map((t, i) => (
                              <span key={i} className="text-[11px] px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-slate-200">{t}</span>
                            ))}
                          </div>
                        </div>

                        <div className="bg-slate-950/50 border border-slate-800 p-4 rounded-xl space-y-2">
                          <h5 className="text-xs font-bold uppercase text-purple-400">Backend & DB</h5>
                          <div className="flex flex-wrap gap-1">
                            {(report.tech_findings?.backend || []).concat(report.tech_findings?.database || []).map((t, i) => (
                              <span key={i} className="text-[11px] px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-slate-200">{t}</span>
                            ))}
                          </div>
                        </div>

                        <div className="bg-slate-950/50 border border-slate-800 p-4 rounded-xl space-y-2">
                          <h5 className="text-xs font-bold uppercase text-cyan-400">Cloud & Hosting</h5>
                          <div className="flex flex-wrap gap-1">
                            {(report.tech_findings?.cloud_hosting || []).map((t, i) => (
                              <span key={i} className="text-[11px] px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-slate-200">{t}</span>
                            ))}
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Tab 6: Hiring */}
                  {activeTab === 'hiring' && (
                    <div className="space-y-4">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {(report.hiring_findings?.departments || []).map((d, idx) => (
                          <div key={idx} className="bg-slate-950/50 border border-slate-800 p-4 rounded-xl space-y-2">
                            <div className="flex items-center justify-between">
                              <h4 className="text-sm font-bold text-white">{d.department}</h4>
                              <span className="text-xs font-bold px-2 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-800">
                                {d.open_count} Open Roles
                              </span>
                            </div>
                            <ul className="list-disc list-inside text-xs text-slate-300 space-y-1 pt-1">
                              {d.key_roles.map((r, i) => (
                                <li key={i}>{r}</li>
                              ))}
                            </ul>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Tab 7: Competitors */}
                  {activeTab === 'competitors' && (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {(report.competitor_findings?.competitors || []).map((comp, idx) => (
                        <div key={idx} className="bg-slate-950/50 border border-slate-800 p-5 rounded-2xl space-y-3">
                          <div className="flex items-start justify-between">
                            <div>
                              <h4 className="text-base font-bold text-white">{comp.name}</h4>
                              <p className="text-xs text-slate-400">{comp.market_position}</p>
                            </div>
                            {comp.pricing && (
                              <span className="text-xs px-2 py-0.5 rounded bg-slate-800 text-cyan-400 font-mono">
                                {comp.pricing}
                              </span>
                            )}
                          </div>
                          <div className="text-xs text-slate-300 space-y-1">
                            <strong className="text-emerald-400">Strengths:</strong> {comp.strengths.join(', ')}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Tab 8: Social */}
                  {activeTab === 'social' && (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {(report.social_findings?.platforms || []).map((plat, idx) => (
                        <div key={idx} className="bg-slate-950/50 border border-slate-800 p-4 rounded-xl flex items-start justify-between">
                          <div>
                            <h4 className="text-sm font-bold text-white">{plat.platform}</h4>
                            <p className="text-xs text-slate-400 mt-1">Frequency: {plat.posting_frequency}</p>
                            <p className="text-xs text-cyan-400">{plat.audience_growth_signal}</p>
                          </div>
                          <span className="text-xs px-2 py-1 rounded bg-slate-900 border border-slate-800 text-slate-300">
                            {plat.engagement_level}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Tab 9: Knowledge Graph */}
                  {activeTab === 'graph' && (
                    <div className="bg-slate-950/50 border border-slate-800 p-6 rounded-2xl space-y-4">
                      <h4 className="text-xs font-bold uppercase tracking-wider text-cyan-400">Knowledge Graph Nodes</h4>
                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                        {(report.knowledge_graph?.nodes || []).map((node, idx) => (
                          <div key={idx} className="bg-slate-900 border border-slate-800 p-3 rounded-xl">
                            <div className="text-[10px] uppercase font-bold text-purple-400">{node.type}</div>
                            <div className="text-xs font-semibold text-white truncate">{node.label}</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Tab 10: Sources & Verified Facts */}
                  {activeTab === 'sources' && (
                    <div className="space-y-3">
                      {(report.verified_facts || []).map((fact, idx) => (
                        <div key={idx} className="bg-slate-950/50 border border-slate-800 p-4 rounded-xl flex items-start justify-between space-x-4">
                          <div className="space-y-1">
                            <p className="text-xs font-semibold text-white">{fact.fact}</p>
                            <div className="flex items-center space-x-2 text-[10px] text-slate-500">
                              <span>Agent: <strong>{fact.agent}</strong></span>
                              <span>• Method: {fact.verification_method}</span>
                              <span>• Source: {fact.source}</span>
                            </div>
                          </div>
                          <span className="text-xs px-2.5 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 font-bold whitespace-nowrap">
                            {fact.confidence}% Confidence
                          </span>
                        </div>
                      ))}
                    </div>
                  )}

                </div>
              )}

            </div>
          )}
        </main>

      </div>
    </div>
  );
};

export default ResearchPage;
