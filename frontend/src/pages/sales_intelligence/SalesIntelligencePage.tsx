import React, { useEffect, useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { leadsApi, Lead } from '../../api/leads';
import { salesIntelligenceApi, SalesIntelligenceReport } from '../../api/salesIntelligence';

export const SalesIntelligencePage: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const [leads, setLeads] = useState<Lead[]>([]);
  const [selectedLeadId, setSelectedLeadId] = useState<string | null>(null);
  const [report, setReport] = useState<SalesIntelligenceReport | null>(null);
  const [loadingLeads, setLoadingLeads] = useState<boolean>(true);
  const [loadingReport, setLoadingReport] = useState<boolean>(false);
  const [analyzing, setAnalyzing] = useState<boolean>(false);
  const [progress, setProgress] = useState<number>(0);
  const [activeTab, setActiveTab] = useState<'overview' | 'decision_makers' | 'signals' | 'timeline' | 'playbook' | 'graph'>('overview');
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
      setErrorMessage('Failed to load leads list');
    } finally {
      setLoadingLeads(false);
    }
  };

  const fetchReport = async (leadId: string) => {
    try {
      setLoadingReport(true);
      setErrorMessage(null);
      const data = await salesIntelligenceApi.getReportByLead(leadId);
      setReport(data);
    } catch (err: any) {
      setReport(null);
    } finally {
      setLoadingReport(false);
    }
  };

  const handleStartAnalysis = async () => {
    if (!selectedLeadId) return;
    try {
      setAnalyzing(true);
      setProgress(10);
      setErrorMessage(null);

      const statusRes = await salesIntelligenceApi.analyzeLead(selectedLeadId);
      let currentProgress = statusRes.progress || 10;
      setProgress(currentProgress);

      const pollInterval = setInterval(async () => {
        try {
          const pollRes = await salesIntelligenceApi.getJobStatus(statusRes.id);
          setProgress(pollRes.progress);
          if (pollRes.status === 'completed') {
            clearInterval(pollInterval);
            setAnalyzing(false);
            fetchReport(selectedLeadId);
          } else if (pollRes.status === 'failed') {
            clearInterval(pollInterval);
            setAnalyzing(false);
            setErrorMessage(pollRes.error_message || 'Sales intelligence analysis failed.');
          }
        } catch (e) {
          clearInterval(pollInterval);
          setAnalyzing(false);
        }
      }, 2000);
    } catch (err: any) {
      setAnalyzing(false);
      setErrorMessage(err.response?.data?.detail || 'Failed to start sales intelligence analysis');
    }
  };

  const filteredLeads = (leads || []).filter(l =>
    (l.name || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
    (l.website || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
    (l.email || '').toLowerCase().includes(searchQuery.toLowerCase())
  );

  const selectedLead = (leads || []).find(l => l.id === selectedLeadId);

  const getIntentColor = (score: number) => {
    if (score >= 85) return 'from-emerald-500 to-teal-400 text-emerald-400';
    if (score >= 70) return 'from-blue-500 to-cyan-400 text-cyan-400';
    if (score >= 50) return 'from-amber-500 to-yellow-400 text-amber-400';
    return 'from-rose-500 to-pink-500 text-rose-400';
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans flex flex-col">
      {/* Top Header Navigation */}
      <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-8">
            <div className="flex items-center space-x-3 cursor-pointer" onClick={() => navigate('/leads')}>
              <div className="h-9 w-9 rounded-xl bg-gradient-to-tr from-indigo-500 via-purple-500 to-pink-500 flex items-center justify-center font-bold text-white shadow-lg shadow-indigo-500/25">
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
              <Link to="/sales-intelligence" className="px-3 py-2 rounded-lg text-sm font-medium text-indigo-400 bg-indigo-500/10 border border-indigo-500/20">Sales Intelligence</Link>
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
            placeholder="Search lead or company..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500 mb-3"
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
                        ? 'bg-indigo-900/30 border-indigo-500/50 shadow-md shadow-indigo-500/10'
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
              Select a lead from the sidebar to view sales intelligence.
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
                        className="text-xs px-2.5 py-1 rounded-md bg-slate-800 text-indigo-400 hover:underline font-mono"
                      >
                        🔗 {selectedLead.website}
                      </a>
                    )}
                  </h1>
                  <p className="text-xs text-slate-400 mt-1">
                    Phase 8 Advanced Account & Opportunity Intelligence Analysis
                  </p>
                </div>

                <button
                  onClick={handleStartAnalysis}
                  disabled={analyzing}
                  className={`px-5 py-2.5 rounded-xl font-medium text-sm transition shadow-lg flex items-center justify-center space-x-2 ${
                    analyzing
                      ? 'bg-slate-800 text-slate-400 cursor-not-allowed border border-slate-700'
                      : 'bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 text-white hover:opacity-90 shadow-indigo-500/25'
                  }`}
                >
                  {analyzing ? (
                    <>
                      <div className="w-4 h-4 border-2 border-slate-400 border-t-transparent rounded-full animate-spin"></div>
                      <span>Enriching ({progress}%)...</span>
                    </>
                  ) : report ? (
                    <span>🔄 Re-run Sales Intelligence</span>
                  ) : (
                    <span>🚀 Run Sales Intelligence</span>
                  )}
                </button>
              </div>

              {/* Progress Bar when analyzing */}
              {analyzing && (
                <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl space-y-2">
                  <div className="flex justify-between text-xs text-slate-300">
                    <span>Enriching Decision Makers, Growth Signals & AI Playbook...</span>
                    <span>{progress}%</span>
                  </div>
                  <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
                    <div
                      className="bg-gradient-to-r from-indigo-500 to-emerald-400 h-full transition-all duration-300"
                      style={{ width: `${progress}%` }}
                    ></div>
                  </div>
                </div>
              )}

              {/* Error Message Alert */}
              {errorMessage && (
                <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs">
                  ⚠️ {errorMessage}
                </div>
              )}

              {/* Report Content */}
              {loadingReport ? (
                <div className="py-16 text-center text-slate-500 text-sm">Loading Sales Intelligence Report...</div>
              ) : !report ? (
                <div className="py-16 text-center bg-slate-950/50 border border-slate-800/80 rounded-2xl p-8 space-y-4">
                  <div className="text-4xl">🔍</div>
                  <h3 className="text-lg font-bold text-white">No Sales Intelligence Report Yet</h3>
                  <p className="text-xs text-slate-400 max-w-md mx-auto">
                    Click <strong>Run Sales Intelligence</strong> above to discover decision makers, compute buying intent, generate growth signals, and assemble an AI Sales Playbook.
                  </p>
                </div>
              ) : (
                <div className="space-y-6">

                  {/* Top Key Metrics Banner: Intent Meter & Classification */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {/* Intent Arc Card */}
                    <div className="bg-slate-950/60 border border-slate-800 p-5 rounded-2xl flex flex-col justify-between">
                      <div className="text-xs font-semibold uppercase tracking-wider text-slate-400">Buying Intent Meter</div>
                      <div className="my-3 flex items-baseline space-x-3">
                        <span className={`text-4xl font-extrabold ${getIntentColor(report.intent_score)}`}>
                          {report.intent_score}
                        </span>
                        <span className="text-sm font-semibold text-slate-300">/ 100</span>
                        <span className={`text-xs px-2.5 py-1 rounded-full font-bold uppercase border border-slate-700 bg-slate-900 ${getIntentColor(report.intent_score)}`}>
                          {report.intent_level} INTENT
                        </span>
                      </div>
                      <p className="text-xs text-slate-400 line-clamp-2">{report.intent_reason}</p>
                    </div>

                    {/* Primary Classification */}
                    <div className="bg-slate-950/60 border border-slate-800 p-5 rounded-2xl flex flex-col justify-between">
                      <div className="text-xs font-semibold uppercase tracking-wider text-slate-400">Opportunity Classification</div>
                      <div className="my-2">
                        <span className="text-lg font-bold text-white">
                          {report.classification?.primary_category || 'SMB'}
                        </span>
                        <div className="flex flex-wrap gap-1.5 mt-2">
                          {(report.classification?.categories || []).map((cat, idx) => (
                            <span key={idx} className="text-[11px] px-2 py-0.5 rounded-md bg-indigo-500/15 border border-indigo-500/30 text-indigo-300 font-medium">
                              {cat}
                            </span>
                          ))}
                        </div>
                      </div>
                      <p className="text-xs text-slate-400 line-clamp-2">{report.classification?.rationale}</p>
                    </div>

                    {/* Key Stats Summary */}
                    <div className="bg-slate-950/60 border border-slate-800 p-5 rounded-2xl flex flex-col justify-between">
                      <div className="text-xs font-semibold uppercase tracking-wider text-slate-400">Enrichment Coverage</div>
                      <div className="grid grid-cols-2 gap-2 my-2 text-center">
                        <div className="bg-slate-900/80 p-2 rounded-xl border border-slate-800">
                          <div className="text-xl font-bold text-indigo-400">{(report.decision_makers || []).length}</div>
                          <div className="text-[10px] text-slate-400 uppercase">Decision Makers</div>
                        </div>
                        <div className="bg-slate-900/80 p-2 rounded-xl border border-slate-800">
                          <div className="text-xl font-bold text-emerald-400">{(report.growth_signals || []).length}</div>
                          <div className="text-[10px] text-slate-400 uppercase">Growth Signals</div>
                        </div>
                      </div>
                      <div className="text-[11px] text-slate-400 text-right">
                        Stage: <strong className="text-slate-200">{report.timeline?.current_stage || 'Growth'}</strong>
                      </div>
                    </div>
                  </div>

                  {/* Workspace Navigation Tabs */}
                  <div className="border-b border-slate-800 flex space-x-2 overflow-x-auto pb-1">
                    {[
                      { id: 'overview', label: '📊 Overview' },
                      { id: 'decision_makers', label: `👥 Decision Makers (${(report.decision_makers || []).length})` },
                      { id: 'signals', label: `📈 Growth Signals (${(report.growth_signals || []).length})` },
                      { id: 'timeline', label: '📅 Company Timeline' },
                      { id: 'playbook', label: '🎯 Sales Playbook' },
                      { id: 'graph', label: '🕸️ Relationship Graph' },
                    ].map((t) => (
                      <button
                        key={t.id}
                        onClick={() => setActiveTab(t.id as any)}
                        className={`px-4 py-2 text-xs font-semibold rounded-xl transition whitespace-nowrap ${
                          activeTab === t.id
                            ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-500/20'
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
                        <h4 className="text-xs font-bold uppercase tracking-wider text-indigo-400">Account Opportunity Summary</h4>
                        <p className="text-sm text-slate-200 leading-relaxed">
                          {report.recommendations?.opportunity_summary || report.timeline?.ai_summary}
                        </p>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="bg-slate-950/50 border border-slate-800 p-5 rounded-2xl space-y-2">
                          <h4 className="text-xs font-bold uppercase tracking-wider text-emerald-400">Recommended Pitch Angle</h4>
                          <p className="text-xs text-slate-300 leading-relaxed">
                            {report.recommendations?.recommended_product_pitch}
                          </p>
                        </div>
                        <div className="bg-slate-950/50 border border-slate-800 p-5 rounded-2xl space-y-2">
                          <h4 className="text-xs font-bold uppercase tracking-wider text-cyan-400">Competitive Advantage</h4>
                          <p className="text-xs text-slate-300 leading-relaxed">
                            {report.recommendations?.competitive_advantage}
                          </p>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Tab 2: Decision Makers */}
                  {activeTab === 'decision_makers' && (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {(report.decision_makers || []).map((dm, idx) => (
                        <div key={idx} className="bg-slate-950/50 border border-slate-800 p-5 rounded-2xl space-y-3">
                          <div className="flex items-start justify-between">
                            <div>
                              <h4 className="text-base font-bold text-white">{dm.name}</h4>
                              <p className="text-xs font-medium text-indigo-400">{dm.designation}</p>
                              <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-400 font-mono inline-block mt-1">
                                {dm.department} Department
                              </span>
                            </div>
                            <span className="text-xs px-2.5 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 font-bold">
                              {dm.confidence_score}% Match
                            </span>
                          </div>

                          <div className="space-y-1.5 text-xs text-slate-300 pt-2 border-t border-slate-800/80">
                            {dm.company_email && (
                              <div className="flex items-center space-x-2">
                                <span className="text-slate-500">✉️</span>
                                <span className="font-mono text-slate-200">{dm.company_email}</span>
                                <span className="text-[10px] px-1.5 py-0.2 rounded bg-emerald-950 text-emerald-400 border border-emerald-800">Verified MX</span>
                              </div>
                            )}
                            {dm.phone && (
                              <div className="flex items-center space-x-2">
                                <span className="text-slate-500">📞</span>
                                <span className="font-mono text-slate-200">{dm.phone}</span>
                              </div>
                            )}
                            {dm.linkedin_url && (
                              <div className="flex items-center space-x-2">
                                <span className="text-slate-500">🔗</span>
                                <a href={dm.linkedin_url} target="_blank" rel="noreferrer" className="text-indigo-400 hover:underline">
                                  LinkedIn Profile
                                </a>
                              </div>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Tab 3: Growth Signals */}
                  {activeTab === 'signals' && (
                    <div className="space-y-3">
                      {(report.growth_signals || []).map((sig, idx) => (
                        <div key={idx} className="bg-slate-950/50 border border-slate-800 p-4 rounded-xl flex items-start space-x-4">
                          <div className="text-2xl p-2 rounded-xl bg-slate-900 border border-slate-800">
                            {sig.type === 'hiring' ? '👥' : sig.type === 'funding' ? '💰' : sig.type === 'tech_migration' ? '⚡' : '🚀'}
                          </div>
                          <div className="flex-1">
                            <div className="flex items-center space-x-2">
                              <span className="text-xs font-bold uppercase text-indigo-400">{sig.type}</span>
                              <span className="text-[10px] text-slate-500">• Confidence {sig.confidence}%</span>
                            </div>
                            <p className="text-xs text-slate-200 mt-1">{sig.description}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Tab 4: Timeline */}
                  {activeTab === 'timeline' && (
                    <div className="bg-slate-950/50 border border-slate-800 p-6 rounded-2xl space-y-6">
                      <div className="flex justify-between items-center pb-4 border-b border-slate-800">
                        <div>
                          <div className="text-xs text-slate-400 uppercase font-semibold">Current Company Stage</div>
                          <div className="text-xl font-bold text-white">{report.timeline?.current_stage || 'Growth'}</div>
                        </div>
                        <div className="text-right">
                          <div className="text-xs text-slate-400 uppercase font-semibold">Founded Year</div>
                          <div className="text-xl font-bold text-indigo-400">{report.timeline?.founded_year || '2018'}</div>
                        </div>
                      </div>

                      <div className="space-y-4">
                        <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">Milestone Timeline</h4>
                        {(report.timeline?.milestones || []).map((m, idx) => (
                          <div key={idx} className="flex items-start space-x-4 border-l-2 border-indigo-500/50 pl-4 py-1">
                            <span className="text-xs font-bold font-mono text-indigo-400 w-16">{m.year_or_date}</span>
                            <span className="text-xs text-slate-200">{m.event}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Tab 5: Sales Playbook */}
                  {activeTab === 'playbook' && (
                    <div className="space-y-4">
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div className="bg-slate-950/50 border border-slate-800 p-4 rounded-xl">
                          <div className="text-[11px] font-semibold text-slate-400 uppercase">Target Persona</div>
                          <div className="text-sm font-bold text-white mt-1">{report.recommendations?.best_contact_person}</div>
                        </div>
                        <div className="bg-slate-950/50 border border-slate-800 p-4 rounded-xl">
                          <div className="text-[11px] font-semibold text-slate-400 uppercase">Primary Channel</div>
                          <div className="text-sm font-bold text-indigo-400 mt-1">{report.recommendations?.best_outreach_channel}</div>
                        </div>
                        <div className="bg-slate-950/50 border border-slate-800 p-4 rounded-xl">
                          <div className="text-[11px] font-semibold text-slate-400 uppercase">Optimal Outreach Window</div>
                          <div className="text-xs font-bold text-emerald-400 mt-1">{report.recommendations?.best_time_to_contact}</div>
                        </div>
                      </div>

                      <div className="bg-slate-950/50 border border-slate-800 p-5 rounded-2xl space-y-2">
                        <h4 className="text-xs font-bold uppercase tracking-wider text-amber-400">Conversation Starter</h4>
                        <p className="text-xs text-slate-200 italic">"{report.recommendations?.conversation_starter}"</p>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="bg-slate-950/50 border border-slate-800 p-5 rounded-2xl space-y-2">
                          <h4 className="text-xs font-bold uppercase tracking-wider text-rose-400">Potential Objections & Counters</h4>
                          <ul className="list-disc list-inside text-xs text-slate-300 space-y-1">
                            {(report.recommendations?.objections || []).map((obj, i) => (
                              <li key={i}>{obj}</li>
                            ))}
                          </ul>
                        </div>
                        <div className="bg-slate-950/50 border border-slate-800 p-5 rounded-2xl space-y-2">
                          <h4 className="text-xs font-bold uppercase tracking-wider text-cyan-400">Follow-up Sequence Cadence</h4>
                          <p className="text-xs text-slate-300 leading-relaxed">{report.recommendations?.followup_strategy}</p>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Tab 6: Relationship Graph */}
                  {activeTab === 'graph' && (
                    <div className="bg-slate-950/50 border border-slate-800 p-6 rounded-2xl space-y-4">
                      <h4 className="text-xs font-bold uppercase tracking-wider text-indigo-400">Company Relationship Graph Nodes</h4>
                      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                        {(report.graph?.nodes || []).map((node, idx) => (
                          <div key={idx} className="bg-slate-900 border border-slate-800 p-3 rounded-xl">
                            <div className="text-[10px] uppercase font-bold text-indigo-400">{node.type}</div>
                            <div className="text-xs font-semibold text-white truncate">{node.label}</div>
                          </div>
                        ))}
                      </div>
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

export default SalesIntelligencePage;
